from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from models import User
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({'hello': 'world'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8081, debug=True)
