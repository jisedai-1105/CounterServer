import asyncio
import websockets
import json
import random
import threading

# 停止フラグ
stop_event = threading.Event()


async def send_data(line: int):
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:

        sleepVal = 0.1

        while not stop_event.is_set():
            try:
                dist = random.randint(10, 20)
                SendData = {"type": "dist", "no": line, "dist": dist, "sec": sleepVal}
                await websocket.send(json.dumps(SendData))
                print(f"[line={line}] Sending data: {SendData}")

                # stop_eventをこまめにチェックしながらスリープ
                for _ in range(int(sleepVal / 0.01)):
                    if stop_event.is_set():
                        break
                    await asyncio.sleep(0.01)

            except websockets.exceptions.ConnectionClosed:
                print(f"[line={line}] Connection closed by the server.")
                break
            except Exception as e:
                print(f"[line={line}] An error occurred: {e}")
                break

    print(f"[line={line}] スレッド終了")


def run_send_data(line: int):
    """スレッド内で asyncio イベントループを作成して send_data を実行する"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(send_data(line))
    except asyncio.CancelledError:
        pass
    finally:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()


if __name__ == "__main__":
    # 使用するライン番号のリストを指定（ここを変更する）
    LINE_NUMBERS = [1, 2, 3 ,4 ,5 ,6 ,7 ,8 ,9 ,10]

    threads = []
    for line in LINE_NUMBERS:
        thread = threading.Thread(target=run_send_data, args=(line,), daemon=True)
        threads.append(thread)
        thread.start()
        print(f"スレッド開始: line={line}")

    print(f"\n{len(LINE_NUMBERS)} 本のスレッドを開始しました。Ctrl+C で終了します。\n")

    try:
        while True:
            # 全スレッドが終了していたらメインループを抜ける
            if all(not t.is_alive() for t in threads):
                break
            threading.Event().wait(0.1)  # 短いインターバルでチェック
    except KeyboardInterrupt:
        print("\n停止シグナルを受信しました。終了処理中...")
        stop_event.set()  # 全スレッドに停止を通知

    # タイムアウト付きで各スレッドの終了を待つ
    for thread in threads:
        thread.join(timeout=3.0)
        if thread.is_alive():
            print(f"スレッド {thread.name} がタイムアウトしました。")

    print("全スレッドが終了しました。")