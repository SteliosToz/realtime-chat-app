import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from dotenv import load_dotenv
import sockets 
from datetime import timedelta
from rooms import rooms_bp
from extensions import db, socketio
from models import User, Room, RoomMember, Message
from auth import auth_bp
from invitations import invitations_bp

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-change-me')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=2)


db.init_app(app)
jwt = JWTManager(app)
CORS(app)
socketio.init_app(app)
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(rooms_bp, url_prefix='/api/rooms')
app.register_blueprint(invitations_bp, url_prefix='/api/invitations')

@app.route('/')
def index():
    return {"status": "Backend is running"}


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, port=5000)