from threading import Lock

from flask_httpauth import HTTPBasicAuth
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = os.environ['MAIL_HOST']
app.config['MAIL_PORT'] = os.environ['MAIL_PORT']
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_SUPPRESS_SEND'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

app.app_context().push()

db = SQLAlchemy(app)
auth = HTTPBasicAuth()
mail = Mail(app)
chat_rooms = {}
users_sids = {}
cors = CORS(app)

async_mode = "eventlet"
socketIO = SocketIO(app, async_mode=async_mode, cors_allowed_origins='*')
thread_lock = Lock()
