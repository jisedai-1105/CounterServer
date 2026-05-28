import asyncio
import websockets
import json
from time import sleep

async def send_data():
    uri = "ws://192.168.3.136:8765"
    async with websockets.connect(uri) as websocket:

        sleepVal = 0.1
        
        SendData = {"type": "dist","no": 1,"dist": 1.00, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(sleepVal) 

        SendData = {"type": "dist","no": 1,"dist": 2.00, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(sleepVal) 

        SendData = {"type": "dist","no": 1,"dist": 3.00, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(sleepVal) 

        SendData = {"type": "dist","no": 1,"dist": 4.00, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(sleepVal) 

        SendData = {"type": "dist","no": 1,"dist": 5.00, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(sleepVal) 

        SendData = {"type": "dist","no": 1,"dist": 6.00, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(sleepVal) 

        SendData = {"type": "dist","no": 1,"dist": 7.00, "sec": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        response = await websocket.recv()
        print(f"Server says: {response}")
        sleep(sleepVal) 
        
        # サーバーからの返答を受信

if __name__ == "__main__":
    asyncio.run(send_data())