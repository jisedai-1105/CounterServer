# CounterServer
カウントサーバ

# 環境設定ファイルについて
環境設定ファイルを以下のように設置してください。

- Counterサーバ用
```
CounterServer
 └ .env
```
- Webサーバ用
```
CounterServer
 └web
    └ .env
```

GitHub上では、env_sample.txtで環境設定ファイルを管理しています。
このファイルを .env と名前を変更して使用してください。

# インストールが必要なモジュール
- websocket
```bash
python -m pip install websockets
```

- Flask
```bash
python -m pip install Flask
```

- Flaskでwebsocketを使う為のツール
```bash
pip install flask-socketio
```

- requests
```bash
pip install requests
```

- env
```bash
pip install python-dotenv
```