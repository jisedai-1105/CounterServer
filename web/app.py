import os
from flask import Flask, render_template
from flask_socketio import SocketIO
from dotenv import load_dotenv

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

load_dotenv()
SERVER_WS_URL = os.getenv("SERVER_WS_URL")
PORT_NO = int(os.getenv("PORT_NO"))

@app.route('/')
def counter():
    return render_template('counter.html', SERVER_WS_URL=SERVER_WS_URL)

@app.route('/home')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    socketio.run(app, debug=True, port=PORT_NO)