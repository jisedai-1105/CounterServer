import socketio
import time

# Socket.IO クライアントの初期化
sio = socketio.Client()

# サーバーに接続されたときのイベント
@sio.event
def connect():
    print("Connected to server!")
    
    # 送信するデータ
    send_data = {"type": "counter", "value": 1}
    
    # Flask-SocketIOのイベント名（例として 'message' やカスタムイベント名）で送信
    # ※サーバー側の @socketio.on('...') の名前に合わせてください
    sio.emit('message', send_data)
    print(f"Sent data: {send_data}")

# サーバーから返答（データ）を受信したときのイベント
@sio.event
def response(data):  # ※サーバー側が 'response' という名前で返してくる場合
    print(f"Server says: {data}")

if __name__ == "__main__":
    # URLとポートをFlaskサーバーに合わせる（例: 5000）
    # ※192.168.3.138 がラズパイの正しいIPアドレス、5000がPORT_NOの場合
    server_url = "http://192.168.3.138:5000"
    
    try:
        sio.connect(server_url)
        # 接続を維持してイベントを待つための待機
        #sio.wait()
    except Exception as e:
        print(f"Connection failed: {e}")