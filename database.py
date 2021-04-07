from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask import Flask
import os


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
auth = HTTPBasicAuth()