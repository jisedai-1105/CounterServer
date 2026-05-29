import asyncio
import aiosqlite
import datetime
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

# --- Slackへの最後の通知時間を記録する辞書 ---
last_sent_times = {}

# --- センサーからの接続を記録するセット（将来の拡張用） ---
sensor_clients = set()

# --- ブラウザからの接続を記録するセット（将来の拡張用） ---
browser_clients = set()

# --- データベース接続関数 ---
def get_db_conn():  
    """WALモードと同期モードを毎回有効にしてコネクションを返す"""
    return aiosqlite.connect(DB_NAME)

# --- データベース初期化関数(距離計測版) ---
async def init_db_dist():

    try:

        async with get_db_conn() as db:
        
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")

            await db.execute('''
                CREATE TABLE IF NOT EXISTS distancements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    no INTEGER NOT NULL,
                    dist REAL NOT NULL,
                    sec REAL NOT NULL,
                    savetime TIMESTAMP NOT NULL
                )
            ''')

            await db.execute('''
                CREATE TABLE IF NOT EXISTS distanceenv (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    no INTEGER NOT NULL,
                    dist REAL NOT NULL,
                    sec REAL NOT NULL,
                    savetime TIMESTAMP NOT NULL
                )
            ''')

            # クライアント増による遅延を完全に防ぐインデックスの追加
            await db.execute("CREATE INDEX IF NOT EXISTS idx_dist_no_time ON distancements (no, savetime);")
            await db.commit()

    except Exception as e:
        LOG.error(f"init_db_dist() - Database error: {e}")


# --- ブラウザ更新通知関数（WebSocket版） ---
async def notify_update_socket_dist(No, inserted_id=""):

    try:
        if not browser_clients:
            return
        
        DistData = await ReceiveDistance(No,inserted_id)
        
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
            *[client.send(message) for client in browser_clients],
            return_exceptions=True # 一部の送信失敗で全体を止めないため
        )

    except Exception as e:
        LOG.error(f"notify_update_socket_dist() - Error: {e}")

# --- ブラウザ更新通知関数（WebSocket版） ---
async def notify_update_socket_distenv(No):

    try:
        if not browser_clients:
            return
        
        EnvData = await GetDistanceEnv(No)
        
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
            *[client.send(message) for client in browser_clients],
            return_exceptions=True # 一部の送信失敗で全体を止めないため
        )

    except Exception as e:
        LOG.error(f"notify_update_socket_dist() - Error: {e}")

# --- データ保存関数 ---
async def save_to_db_dist(no,dist,sec):

    inserted_id = ""
    try:
        async with get_db_conn() as db:

            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            #LOG.info(f"Saved bef: id: ?, no: {no}, dist: {dist}, sec: {sec} at {now}")

            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")

            cursor = await db.execute(
                "INSERT INTO distancements (no, dist, sec, savetime) VALUES (?, ?, ?, ?)",
                (no, dist, sec, now)
            )
            await db.commit()
            inserted_id = cursor.lastrowid
            
            LOG.info(f"Saved aft: id: {inserted_id}, no: {no}, dist: {dist}, sec: {sec} at {now}")

    except Exception as e:
        LOG.error(f"save_to_db_dist() - no: {no}, dist: {dist}, sec: {sec} - Database error: {e}")

    return inserted_id

# --- 距離情報の取得処理 ---
async def ReceiveDistance(No, inserted_id=""):
    try:

        Env, sec = await ReceiveDistanceDB(No)
        latest_dist = await get_latest_distance(No, inserted_id)

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
                IsSendMsg = await asyncio.to_thread(SendSlackMessage, f"成型機：{No} が満杯になりました。")
                if IsSendMsg:
                    last_sent_times[No] = current_time
                pass

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

# --- 距離情報の取得処理 ---
async def ReceiveDistanceDB(No):
    Env = await GetDistanceEnv(No)

    async with get_db_conn() as db:

        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA synchronous=NORMAL;")

        db.row_factory = aiosqlite.Row
        sql = """
            SELECT IFNULL(sum(sec), 0) AS total 
            FROM distancements 
            WHERE no = ? 
            AND dist <= ?
            AND savetime >= DATETIME('now','localtime', '-' || ? || ' seconds')
        """
        async with db.execute(sql, (No, Env["dist"], READ_TIME)) as cursor:
            row = await cursor.fetchone()
            sec = row["total"] if row else 0
            return Env, sec

# --- Slack通知関数 ---
def SendSlackMessage(message):
    result = False
    try:
        if SLACK_WEBHOOK_URL is None:
            LOG.warning("SLACK_WEBHOOK_URL が設定されていません。Slack通知をスキップします。")
            return result

        payload = {"text": message}
        response = requests.post(SLACK_WEBHOOK_URL, json=payload , timeout=3)

        if response.status_code != 200:
            LOG.error(f"Failed to send Slack message: {response.status_code} - {response.text}")
        else:
            LOG.info("Slack message sent successfully.")
            result = True

    except Exception as e:
        LOG.error(f"Error sending Slack message: {e}")
    
    return result

# --- 最新の距離情報の取得関数 ---
async def get_latest_distance(No, inserted_id=""):

    try:

        async with get_db_conn() as db:
            db.row_factory = aiosqlite.Row
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
                params = (No, READ_TIME)
            else:
                sql = '''
                SELECT * FROM distancements 
                WHERE 
                id = ?
                '''
                params = (inserted_id,)

            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")

            async with db.execute(sql, params) as cursor:
                row = await cursor.fetchone()
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
async def GetDistanceEnv(No):
    try:
        async with get_db_conn() as db:
 
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")

            db.row_factory = aiosqlite.Row
            sql = "SELECT dist, sec FROM distanceenv WHERE no = ?"

            async with db.execute(sql, (No,)) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    result_dict = {"dist": INIT_DISTANCE, "sec": INIT_SEC}
                else:
                    result_dict = dict(row)

            return result_dict

    except Exception as e:
        LOG.error(f"GetDistanceEnv() - Database error: {e}")
        #raise  # 呼び出し元にエラーを伝える

# --- 距離環境設定の保存処理 ---
async def SetDistanceEnv(No, dist, sec):

    try:
        async with get_db_conn() as db:

            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")

            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 既に環境設定が存在するか確認
            async with db.execute("SELECT id FROM distanceenv WHERE no = ?", (No,)) as cursor:
                row = await cursor.fetchone()

            if row is None:
                # 存在しない場合は新規挿入
                await db.execute(
                    "INSERT INTO distanceenv (no, dist, sec, savetime) VALUES (?, ?, ?, ?)",
                    (No, dist, sec, now)
                )
            else:
                # 存在する場合は更新
                await db.execute(
                    "UPDATE distanceenv SET dist = ?, sec = ?, savetime = ? WHERE no = ?",
                    (dist, sec, now, No)
                )

            await db.commit()

        LOG.info(f"SetDistanceEnv: No={No}, dist={dist}, sec={sec} at {now}")
    except Exception as e:
        LOG.error(f"SetDistanceEnv: DB error: {e}")

# --- WebSocketハンドラー関数 ---
async def handler(websocket):

    try:
        async for message in websocket:

            try:

                data = json.loads(message)
                DataType = data.get("type")
                No = data.get("no")

                ########################################
                # クライアントの種類に応じてセットに追加
                ########################################
                try:

                    if DataType == "dist":
                        if websocket in sensor_clients:
                            pass
                        else:
                            sensor_clients.add(websocket)
                    else:
                        if websocket in browser_clients:
                            pass
                        else:
                            browser_clients.add(websocket)
                except Exception as e:
                    LOG.error(f"handler() - Error : {e}")
                    return

                ###################
                #距離情報の受信
                ###################
                if DataType == "dist":
                    dist = data.get("dist")
                    sec = data.get("sec")
                    inserted_id = await save_to_db_dist(No, dist, sec)
                    response = {
                                "type": "dist",
                                "no": No,
                                "dist": dist,
                                "sec": sec
                            }
                    #await websocket.send(json.dumps(response))
                    asyncio.create_task(notify_update_socket_dist(No,inserted_id))  # ブラウザ更新通知
                
                #####################
                #距離情報をクライアントに返す
                #####################
                if DataType == "getdistance":
                    response = {
                                "type": "getdistance",
                            }
                    #await websocket.send(json.dumps(response))
                    asyncio.create_task(notify_update_socket_dist(No))  # ブラウザ更新通知

                ######################
                #距離環境設定の保存
                ######################
                if DataType == "setenv":
                    dist = data.get("dist")
                    sec = data.get("sec")
                    await SetDistanceEnv(No, dist, sec)
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
        try:
            if websocket in sensor_clients:
                sensor_clients.remove(websocket)
                #LOG.info(f"Client disconnected. Total sensor_clients: {len(sensor_clients)}")
            elif websocket in browser_clients:
                browser_clients.remove(websocket)
                #LOG.info(f"Client disconnected. Total browser_clients: {len(browser_clients)}")
        except Exception as e:
            pass

# --- メイン関数 ---
async def main():

    LOG.info("■" * 20)
    LOG.info("Server started.")
    LOG.info("■" * 20)

    await init_db_dist()

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

        #print(await ReceiveDistance(1))
        
        #print(GetDistanceEnv(1))

        #               No , 距離 , 経過秒
        #save_to_db_dist(1, 5.0, 4.0)
        #print(get_latest_distance(1))
        #print(ReceiveDistance(1))
        #              No , 距離 , 経過秒
        #SetDistanceEnv(1, 10.0, 5.0)
        #print(GetDistanceEnv(1))

    except KeyboardInterrupt:
        # Ctrl+Cによるエラー出力をここで食い止める
        LOG.info("■" * 20)
        LOG.info("Server stopped.")
        LOG.info("■" * 20)