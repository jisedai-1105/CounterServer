import asyncio
import websockets
import json

async def send_data():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        
        SendData = {"type": "counter", "value": 1} # 送信するデータ
        await websocket.send(json.dumps(SendData)) # 文字列として送信
        
        # サーバーからの返答を受信
        response = await websocket.recv()
        print(f"Server says: {response}")

if __name__ == "__main__":
    asyncio.run(send_data())