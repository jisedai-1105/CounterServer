import requests
from dotenv import load_dotenv
import os
 
load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# 1. 送信先のURL（Webhook URL）を設定
url = SLACK_WEBHOOK_URL

# 2. 送信するデータを辞書（ディクショナリ）型で定義
data = {
    "text": "Hello, World!"
}

# 3. POSTリクエストを送信
# json= 引数を使うと、自動的に Content-type を application/json に設定し、
# データをJSON文字列に変換して送信してくれます。
response = requests.post(url, json=data)

# 4. 結果の確認（200なら成功、Slackの場合は成功すると「ok」と返ってきます）
if response.status_code == 200:
    print("送信成功:", response.text)
else:
    print(f"エラーが発生しました (ステータスコード: {response.status_code}):", response.text)