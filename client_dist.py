import asyncio
import websockets
import json
from time import sleep

async def send_data():
    #uri = "ws://192.168.3.136:8765"
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:

        sleepVal = 0.5
        
        SendData = {"type": "dist","no": 1,"dist": 5.00, "sec": 20} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        #response = await websocket.recv()
        #print(f"Server says: {response}")
        await asyncio.sleep(sleepVal)
        
        SendData = {"type": "dist","no": 1,"dist": 5.00, "sec": 20} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        #response = await websocket.recv()
        #print(f"Server says: {response}")
        await asyncio.sleep(sleepVal)

        SendData = {"type": "dist","no": 1,"dist": 5.00, "sec": 20} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        #response = await websocket.recv()
        #print(f"Server says: {response}")
        await asyncio.sleep(sleepVal)

        # サーバーからの返答を受信

if __name__ == "__main__":
    asyncio.run(send_data())