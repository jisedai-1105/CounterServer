import asyncio
import websockets
import json
from time import sleep
import random

async def send_data():
    uri = "ws://192.168.3.136:8765"
    async with websockets.connect(uri) as websocket:

        sleepVal = 0.5
        line = 3
        
        while True:
            try:
                dist = random.randint(10, 20)
                SendData = {"type": "dist","no": line,"dist": dist, "sec": sleepVal} # 送信するデータ
                await websocket.send(json.dumps(SendData)) # 文字列として送信
                print(f"Sending data: {SendData}")
                #response = await websocket.recv()
                #print(f"Server says: {response}")
                sleep(sleepVal)
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed by the server.")
            except Exception as e:
                print(f"An error occurred: {e}")
        
        # サーバーからの返答を受信

if __name__ == "__main__":
    asyncio.run(send_data())