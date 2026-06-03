import os
from flask import Flask, render_template
from flask_socketio import SocketIO
from dotenv import load_dotenv

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

load_dotenv()
SERVER_WS_URL = os.getenv("SERVER_WS_URL")
PORT_NO = int(os.getenv("PORT_NO"))
LINE_MAX = int(os.getenv("LINE_MAX"))

def CreateLineList(line_max):
    return [
        os.getenv(f"LINE{i}") if os.getenv(f"LINE{i}") is not None else i 
        for i in range(1, line_max + 1)
    ]

@app.route('/')
def counter():
    return render_template('distance.html', SERVER_WS_URL=SERVER_WS_URL, LINE_MAX=LINE_MAX, LINE_LIST=CreateLineList(LINE_MAX))

@app.route('/home')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True, port=PORT_NO, allow_unsafe_werkzeug=True)