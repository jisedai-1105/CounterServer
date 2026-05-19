import asyncio
import sqlite3
import datetime
import websockets
import json
import clsLog
from dotenv import load_dotenv
import os

load_dotenv()

# --- データベース設定 ---
DB_NAME = os.getenv("DB_NAME")
PORT_NO = int(os.getenv("PORT_NO"))

# --- ログ設定 ---
LOG = clsLog.AppLogger(log_dir=os.getenv("LOG_DIR"), log_name=os.getenv("LOG_NAME"))

# --- 接続中のクライアント情報初期化 ---
connected_clients = set()

# --- ブラウザ更新通知関数（WebSocket版） ---
async def notify_update_socket():

    try:
        if not connected_clients:
            return
        
        counter_value = get_active_counter()
        
        # 送信するメッセージの作成
        message = json.dumps({
            "type": "counter",
            "value": counter_value
        })

        # 全クライアントに一斉送信
        # waitを使って並列に処理すると効率的です
        await asyncio.gather(
            *[client.send(message) for client in connected_clients],
            return_exceptions=True # 一部の送信失敗で全体を止めないため
        )

    except Exception as e:
        LOG.error(f"notify_update(): {e}")

# --- データベース初期化関数 ---
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                val INTEGER NOT NULL,
                savetime TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        conn.commit()
    conn.close()

# --- データ保存関数 ---
def save_to_db(value):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "INSERT INTO measurements (val, savetime, is_active) VALUES (?, ?, ?)",
                (value, now, True)
            )
            conn.commit()
            LOG.info(f"Saved: {value} at {now}")
    except Exception as e:
        LOG.error(f"Database error: {e}")
    finally:
        conn.close()

# --- カウンターリセット関数---
def reset_counter():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            sql = "UPDATE measurements SET is_active = 0 WHERE is_active = 1"
            cursor.execute(sql)
            conn.commit()
            LOG.info(f"Counter Reset")
    except Exception as e:
        LOG.error(f"Database error: {e}")
    finally:
        conn.close()

# --- アクティブなカウンターの取得関数 ---
def get_active_counter():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            sql = "SELECT IFNULL(sum(val), 0) AS total FROM measurements WHERE is_active = 1"
            cursor.execute(sql)
            result = cursor.fetchone()
            return result["total"] if result else 0

    except Exception as e:
        LOG.error(f"Database error: {e}")
        raise  # 呼び出し元にエラーを伝える
    finally:
        conn.close()

# --- WebSocketハンドラー関数 ---
async def handler(websocket):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                DataType = data.get("type")

                ###################
                #カウント
                ###################
                if DataType == "counter":
                    number = data.get("value")
                    save_to_db(number)
                    response = {
                                "type": "counter",
                                "value": number
                            }
                    await websocket.send(json.dumps(response))
                    await notify_update_socket()  # ブラウザ更新通知

                ###################
                #カウントのリセット
                ###################
                if DataType == "reset":
                    reset_counter()
                    response = {
                                "type": "reset",
                                "value": "Counter reset."
                            }
                    await websocket.send(json.dumps(response))
                    await notify_update_socket()  # ブラウザ更新通知

                ###################
                #カウントの取得
                ###################
                if DataType == "get_counter":
                    counter_value = get_active_counter()
                    response = {
                                "type": "counter",
                                "value": counter_value
                            }
                    await websocket.send(json.dumps(response))

                ###################
                #カウントの更新
                ###################
                if DataType == "update_counter":
                    response = {
                                "type": "update_counter",
                                "value": "update_counter."
                            }
                    await websocket.send(json.dumps(response))
                    await notify_update_socket()  # ブラウザ更新通知

            except (ValueError, TypeError):
                response = {
                            "type": "error",
                            "value": "Invalid input. Please send a valid integer."
                        }
                await websocket.send(json.dumps(response))

    except websockets.exceptions.ConnectionClosed:
        LOG.info("Client connection closed normally.")
    except Exception as e:
        LOG.error(f"Handler error: {e}")
    finally:
        connected_clients.remove(websocket)
        LOG.info(f"Client disconnected. Total clients: {len(connected_clients)}")

# --- メイン関数 ---
async def main():

    init_db()
    
    # サーバーを起動し、そのオブジェクトを保持
    async with websockets.serve(handler, "localhost", PORT_NO):
        LOG.info(f"WebSocket Server started on ws://localhost:{PORT_NO} ")
        LOG.info("Press Ctrl+C to stop the server.")
        
        try:
            # 終了信号を待機する仕組み
            await asyncio.Future() 
        except asyncio.CancelledError:
            # Ctrl+C などによるキャンセルをここでキャッチ
            LOG.info("Shutting down server...")

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

    except KeyboardInterrupt:
        # Ctrl+Cによるエラー出力をここで食い止める
        LOG.info("\nServer stopped.")