from flask import Flask, request
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_moment import Moment
from flask_jsglue import JSGlue
#from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'home'
moment = Moment(app)
jsglue = JSGlue(app)
#socketio = SocketIO(app)

from app import routes, models


# @socketio.on('connect')
# def test_connect():
#     emit('my response', {'data': 'Connected'})

# @socketio.on('my turn')
# def handle_my_turn():
#     emit('my response', {'data': 'My Turn!'})

# clients = []

# @socketio.on('connect')
# def handle_connect():
#     print('Client connected')
#     clients.append(request.sid)

# @socketio.on('disconnect')
# def handle_disconnect():
#     print('Client disconnected')
#     clients.remove(request.sid)

# def send_message(client_id, data):
#     socketio.emit('output', data, room=client_id)
#     print('sending message "{}" to client "{}".'.format(data, client_id))

#if __name__ == '__main__':
#    socketio.run(app)