import asyncio
import websockets
import json
from time import sleep

async def send_data():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        
        SendData = {"type": "dist","no": 1,"dist": 5.10, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(1.0) 

        SendData = {"type": "dist","no": 1,"dist": 5.00, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(1.0) 

        SendData = {"type": "dist","no": 1,"dist": 4.00, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(1.0) 

        SendData = {"type": "dist","no": 1,"dist": 3.00, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(1.0) 

        SendData = {"type": "dist","no": 1,"dist": 4.50, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(1.0) 

        SendData = {"type": "dist","no": 1,"dist": 5.50, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(1.0) 

        SendData = {"type": "dist","no": 1,"dist": 5.50, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(1.0) 
        
        # サーバーからの返答を受信

if __name__ == "__main__":
    asyncio.run(send_data())