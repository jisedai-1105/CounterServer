import asyncio
import sqlite3
import datetime
from time import sleep
import websockets
import json
import clsLog
from dotenv import load_dotenv
import os
import requests

load_dotenv()

# --- データベース設定 ---
DB_NAME = os.getenv("DB_NAME")
PORT_NO = int(os.getenv("PORT_NO"))
READ_TIME = int(os.getenv("READ_TIME"))
INIT_DISTANCE = float(os.getenv("INIT_DISTANCE"))
INIT_SEC = float(os.getenv("INIT_SEC"))
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SLACK_SEND_INTERVAL = int(os.getenv("SLACK_SEND_INTERVAL"))

# --- ログ設定 ---
LOG = clsLog.AppLogger(log_dir=os.getenv("LOG_DIR"), log_name=os.getenv("LOG_NAME"))

# --- 接続中のクライアント情報初期化 ---
connected_clients = set()

# --- DBのコネクション ---
db_connect = None

# --- Slackへの最後の通知時間を記録する辞書 ---
last_sent_times = {}

# --- DBコネクションのクローズ関数 ---
def close_db():
    global db_connect
    try:
        if db_connect:
            db_connect.close()
            db_connect = None
    except Exception as e:
        LOG.error(f"close_db() - Error: {e}")

# --- ブラウザ更新通知関数（WebSocket版） ---
async def notify_update_socket(No):

    try:
        if not connected_clients:
            return
        
        counter_value = get_active_counter(No)
        
        # 送信するメッセージの作成
        message = json.dumps({
            "type": "counter",
            "no": No,
            "value": counter_value,
        })

        # 全クライアントに一斉送信
        # waitを使って並列に処理すると効率的です
        await asyncio.gather(
            *[client.send(message) for client in connected_clients],
            return_exceptions=True # 一部の送信失敗で全体を止めないため
        )

    except Exception as e:
        LOG.error(f"notify_update() - Error: {e}")

# --- ブラウザ更新通知関数（WebSocket版） ---
async def notify_update_socket_dist(No, inserted_id=""):

    try:
        if not connected_clients:
            return
        
        DistData = ReceiveDistance(No,inserted_id)
        
        # 送信するメッセージの作成
        message = json.dumps({
            "type": "dist",
            "no": No,
            "alert": DistData["alert"],
            "dist": DistData["dist"]
        })

        #LOG.info(f"Sent distance: No={No}, alert={DistData['alert']}, dist={DistData['dist']}")

        # 全クライアントに一斉送信
        # waitを使って並列に処理すると効率的です
        await asyncio.gather(
            *[client.send(message) for client in connected_clients],
            return_exceptions=True # 一部の送信失敗で全体を止めないため
        )

    except Exception as e:
        LOG.error(f"notify_update_socket_dist() - Error: {e}")

# --- ブラウザ更新通知関数（WebSocket版） ---
async def notify_update_socket_distenv(No):

    try:
        if not connected_clients:
            return
        
        EnvData = GetDistanceEnv(No)
        
        # 送信するメッセージの作成
        message = json.dumps({
            "type": "distenv",
            "no": No,
            "dist": EnvData["dist"],
            "sec": EnvData["sec"]
        })

        # 全クライアントに一斉送信
        # waitを使って並列に処理すると効率的です
        await asyncio.gather(
            *[client.send(message) for client in connected_clients],
            return_exceptions=True # 一部の送信失敗で全体を止めないため
        )

    except Exception as e:
        LOG.error(f"notify_update_socket_dist() - Error: {e}")

# --- データベース初期化関数 ---
def init_db():
    global db_connect

    if db_connect is None:
        db_connect = sqlite3.connect(DB_NAME, check_same_thread=False)

    cursor = db_connect.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            no INTEGER NOT NULL,
            val INTEGER NOT NULL,
            savetime TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    db_connect.commit()

# --- データベース初期化関数(距離計測版) ---
def init_db_dist():
    global db_connect
    try:

        if db_connect is None:
            db_connect = sqlite3.connect(DB_NAME, check_same_thread=False)

        cursor = db_connect.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS distancements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                no INTEGER NOT NULL,
                dist REAL NOT NULL,
                sec REAL NOT NULL,
                savetime TIMESTAMP NOT NULL
            )
        ''')
        db_connect.commit()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS distanceenv (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                no INTEGER NOT NULL,
                dist REAL NOT NULL,
                sec REAL NOT NULL,
                savetime TIMESTAMP NOT NULL
            )
        ''')
        db_connect.commit()
    
    except Exception as e:
        LOG.error(f"init_db_dist() - Database error: {e}")

# --- データ保存関数 ---
def save_to_db(no,value):
    global db_connect
    try:
        cursor = db_connect.cursor()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO measurements (no, val, savetime, is_active) VALUES (?, ?, ?, ?)",
            (no, value, now, True)
        )
        db_connect.commit()
        LOG.info(f"Saved: {value} at {now}")
    except Exception as e:
        LOG.error(f"save_to_db() - Database error: {e}")

# --- データ保存関数 ---
def save_to_db_dist(no,dist,sec):

    global db_connect

    inserted_id = ""
    try:
        cursor = db_connect.cursor()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO distancements (no, dist, sec, savetime) VALUES (?, ?, ?, ?)",
            (no, dist, sec, now)
        )
        db_connect.commit()

        inserted_id = cursor.lastrowid

        LOG.info(f"Saved: id: {inserted_id}, no: {no}, dist: {dist}, sec: {sec} at {now}")
    except Exception as e:
        LOG.error(f"save_to_db_dist() - no: {no}, dist: {dist}, sec: {sec} - Database error: {e}")

    return inserted_id

# --- カウンターリセット関数---
def reset_counter(No):
    global db_connect
    try:
        cursor = db_connect.cursor()
        sql = "UPDATE measurements SET is_active = 0 WHERE is_active = 1 AND no = ?"
        cursor.execute(sql, (No,))
        db_connect.commit()
        LOG.info(f"Counter Reset")
    except Exception as e:
        LOG.error(f"Database error: {e}")

# --- アクティブなカウンターの取得関数 ---
def get_active_counter(No):
    global db_connect
    try:
        db_connect.row_factory = sqlite3.Row
        cursor = db_connect.cursor()
        sql = "SELECT IFNULL(sum(val), 0) AS total FROM measurements WHERE is_active = 1 AND no = ?"
        cursor.execute(sql, (No,))
        result = cursor.fetchone()
        return result["total"] if result else 0

    except Exception as e:
        LOG.error(f"Database error: {e}")
        #raise  # 呼び出し元にエラーを伝える

# --- 距離情報の取得処理 ---
def ReceiveDistance(No, inserted_id=""):
    global db_connect
    try:

        Env = GetDistanceEnv(No)

        db_connect.row_factory = sqlite3.Row
        cursor = db_connect.cursor()

        # 過去READ_TIME秒のデータの内、距離がEnv["dist"]以下のものを合計する
        sql = """
            SELECT IFNULL(sum(sec), 0) AS total 
            FROM distancements 
            WHERE no = ? 
            AND dist <= ?
            AND savetime >= DATETIME('now','localtime', '-' || ? || ' seconds')
        """

        cursor.execute(sql, (No, Env["dist"], READ_TIME))
        row = cursor.fetchone()
        sec = row["total"] if row else 0

        latest_dist = get_latest_distance(No,inserted_id)

        #LOG.info(f"READ_TIME:{READ_TIME}, env.dist:{Env['dist']}, env.sec:{Env['sec']} / total sec: {sec}")

        if sec >= Env["sec"]:
            result = {
                "type": "distance",
                "no": No,
                "alert": "full", 
                "dist": latest_dist["dist"], 
            }

            # Slackへの通知の制御
            current_time = datetime.datetime.now()
            if No not in last_sent_times or (current_time - last_sent_times[No]).seconds >= SLACK_SEND_INTERVAL:
                IsSendMsg = SendSlackMessage(f"成型機：{No} が満杯になりました。")
                if IsSendMsg:
                    last_sent_times[No] = current_time

        else:
            result = {
                "type": "distance",
                "no": No,
                "alert": "", 
                "dist": latest_dist["dist"], 
            }

        return result

    except Exception as e:
        LOG.error(f"ReceiveDistance() - Database error: {e}")
        #raise  # 呼び出し元にエラーを伝える

# --- Slack通知関数 ---
def SendSlackMessage(message):
    result = False
    try:
        if SLACK_WEBHOOK_URL is None:
            LOG.warning("SLACK_WEBHOOK_URL が設定されていません。Slack通知をスキップします。")
            return result

        payload = {"text": message}
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)

        if response.status_code != 200:
            LOG.error(f"Failed to send Slack message: {response.status_code} - {response.text}")
        else:
            LOG.info("Slack message sent successfully.")
            result = True

    except Exception as e:
        LOG.error(f"Error sending Slack message: {e}")
    
    return result

# --- 最新の距離情報の取得関数 ---
def get_latest_distance(No, inserted_id=""):

    global db_connect
    try:
        db_connect.row_factory = sqlite3.Row
        cursor = db_connect.cursor()

        if inserted_id == "":
            sql = '''
            SELECT * FROM distancements 
            WHERE 
            no = ? 
            AND savetime >= DATETIME('now','localtime', '-' || ? || ' seconds')
            ORDER BY 
            savetime DESC 
            LIMIT 1
            '''
            cursor.execute(sql, (No, READ_TIME))
        else:
            sql = '''
            SELECT * FROM distancements 
            WHERE 
            id = ?
            '''
            cursor.execute(sql, (inserted_id,))

        row = cursor.fetchone()
        Result = None
        if row is None:
            Result = {"dist": "---"}
        else:
            Result = {"dist": row["dist"]}
        
        return Result

    except Exception as e:
        LOG.error(f"get_latest_distance() - Database error: {e}")
        #raise  # 呼び出し元にエラーを伝える

# --- 距離情報の取得処理 ---
def GetDistanceEnv(No):
    global db_connect
    try:
        db_connect.row_factory = sqlite3.Row
        cursor = db_connect.cursor()
        sql = "SELECT dist, sec FROM distanceenv WHERE no = ?"
        cursor.execute(sql, (No,))
        row = cursor.fetchone()
        if row is None:
            result_dict = {"dist": INIT_DISTANCE, "sec": INIT_SEC}
        else:
            result_dict = dict(row)

        return result_dict

    except Exception as e:
        LOG.error(f"GetDistanceEnv() - Database error: {e}")
        #raise  # 呼び出し元にエラーを伝える

# --- 距離環境設定の保存処理 ---
def SetDistanceEnv(No, dist, sec):
    global db_connect
    try:
        cursor = db_connect.cursor()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 既に環境設定が存在するか確認
        cursor.execute("SELECT id FROM distanceenv WHERE no = ?", (No,))
        row = cursor.fetchone()

        if row is None:
            # 存在しない場合は新規挿入
            cursor.execute(
                "INSERT INTO distanceenv (no, dist, sec, savetime) VALUES (?, ?, ?, ?)",
                (No, dist, sec, now)
            )
        else:
            # 存在する場合は更新
            cursor.execute(
                "UPDATE distanceenv SET dist = ?, sec = ?, savetime = ? WHERE no = ?",
                (dist, sec, now, No)
            )

        db_connect.commit()
        LOG.info(f"SetDistanceEnv: No={No}, dist={dist}, sec={sec} at {now}")
    except Exception as e:
        LOG.error(f"SetDistanceEnv: DB error: {e}")

# --- WebSocketハンドラー関数 ---
async def handler(websocket):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            try:

                data = json.loads(message)
                DataType = data.get("type")
                No = data.get("no")

                ###################
                #カウント
                ###################
                if DataType == "counter":
                    number = data.get("value")
                    save_to_db(No, number)
                    response = {
                                "type": "counter",
                                "no": No,
                                "value": number,
                            }
                    await websocket.send(json.dumps(response))
                    await notify_update_socket(No)  # ブラウザ更新通知

                ###################
                #カウントのリセット
                ###################
                if DataType == "reset":
                    reset_counter(No)
                    response = {
                                "type": "reset",
                                "no": No,
                                "value": "Counter reset."
                            }
                    await websocket.send(json.dumps(response))
                    await notify_update_socket(No)  # ブラウザ更新通知

                ###################
                #カウントの取得
                ###################
                if DataType == "get_counter":
                    counter_value = get_active_counter(No)
                    response = {
                                "type": "counter",
                                "no": No,
                                "value": counter_value
                            }
                    await websocket.send(json.dumps(response))

                ###################
                #カウントの更新
                ###################
                if DataType == "update_counter":
                    response = {
                                "type": "update_counter",
                                "no": No,
                                "value": "update_counter",
                            }
                    await websocket.send(json.dumps(response))
                    await notify_update_socket(No)  # ブラウザ更新通知
                
                ###################
                #距離情報の受信
                ###################
                if DataType == "dist":
                    dist = data.get("dist")
                    sec = data.get("sec")
                    inserted_id = save_to_db_dist(No, dist, sec)
                    response = {
                                "type": "dist",
                                "no": No,
                                "dist": dist,
                                "sec": sec
                            }
                    #await websocket.send(json.dumps(response))
                    await notify_update_socket_dist(No,inserted_id)  # ブラウザ更新通知
                
                #####################
                #距離情報をクライアントに返す
                #####################
                if DataType == "getdistance":
                    response = {
                                "type": "getdistance",
                            }
                    #await websocket.send(json.dumps(response))
                    await notify_update_socket_dist(No)  # ブラウザ更新通知

                ######################
                #距離環境設定の保存
                ######################
                if DataType == "setenv":
                    dist = data.get("dist")
                    sec = data.get("sec")
                    SetDistanceEnv(No, dist, sec)
                    response = {
                                "type": "setenv",
                                "no": No,
                                "dist": dist,
                                "sec": sec,
                            }
                    await websocket.send(json.dumps(response))
                
                #######################
                #距離環境設定の取得
                #######################
                if DataType == "getenv":
                    await notify_update_socket_distenv(No)  # ブラウザ更新通知
                    response = {
                                "type": "getenv",
                                "no": No,
                            }
                    #await websocket.send(json.dumps(response))

            except (ValueError, TypeError):
                response = {
                            "type": "error",
                            "value": "Invalid input. Please send a valid integer."
                        }
                await websocket.send(json.dumps(response))

    except websockets.exceptions.ConnectionClosed:
        #LOG.info("Client connection closed normally.")
        pass
    except Exception as e:
        LOG.error(f"Handler error: {e}")
    finally:
        connected_clients.remove(websocket)
        #LOG.info(f"Client disconnected. Total clients: {len(connected_clients)}")

# --- メイン関数 ---
async def main():

    LOG.info("■" * 20)
    LOG.info("Server started.")
    LOG.info("■" * 20)

    init_db_dist()
    
    # サーバーを起動し、そのオブジェクトを保持
    async with websockets.serve(handler, "0.0.0.0", PORT_NO):

        LOG.info(f"WebSocket Server started on ws://0.0.0.0:{PORT_NO} ")
        LOG.info("Press Ctrl+C to stop the server.")
        
        try:
            # 終了信号を待機する仕組み
            await asyncio.Future() 
        except asyncio.CancelledError:
            # Ctrl+C などによるキャンセルをここでキャッチ
            LOG.info("Shutting down server.")

    close_db() 

    LOG.info("■" * 20)
    LOG.info("Server stopped.")
    LOG.info("■" * 20)

if __name__ == "__main__":
    try:

        asyncio.run(main())

        #デバッグ用 ----------------------
        #カウンターのリセット
        #reset_counter() 
        #カウントの追加
        #save_to_db(10)
        #カウントの表示
        #print(get_active_counter())

        #init_db_dist()
        
        #print(GetDistanceEnv(1))

        #               No , 距離 , 経過秒
        #save_to_db_dist(1, 5.0, 4.0)
        #print(get_latest_distance(1))
        #print(ReceiveDistance(1))
        #              No , 距離 , 経過秒
        #SetDistanceEnv(1, 10.0, 5.0)
        #print(GetDistanceEnv(1))
        
        #close_db()

    except KeyboardInterrupt:
        # Ctrl+Cによるエラー出力をここで食い止める
        close_db() 
        LOG.info("■" * 20)
        LOG.info("Server stopped.")
        LOG.info("■" * 20)