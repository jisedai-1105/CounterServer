import asyncio
import websockets
import json
from time import sleep

async def send_data():
    #uri = "ws://192.168.3.136:8765"
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:

        SendData = {"type": "RstDist","no": 1,"dist": 10.00} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        print(f"送信しました：{SendData}")

if __name__ == "__main__":
    asyncio.run(send_data())