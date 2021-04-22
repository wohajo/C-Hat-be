import time

import jwt
from werkzeug.security import generate_password_hash, check_password_hash

from database import db, app
from enums import InvitationStatus


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    username = db.Column(db.String(64), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True)

    def __repr__(self):
        return '<id {}, first name: {}, last name: {}, username: {}, email: {}>'.format(
            self.id, self.first_name, self.last_name, self.username, self.email)

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expires_in=600):
        return jwt.encode(
            {'id': self.id, 'exp': time.time() + int(expires_in), 'username': self.username},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_auth_token(token):
        try:
            data = jwt.decode(token,
                              app.config['SECRET_KEY'],
                              algorithms=['HS256'])
        except:
            return
        return User.query.get(data['id'])

    def serialize(self):
        return {
            'id': self.id,
            'firstName': self.first_name,
            'lastName': self.last_name,
            'username': self.username,
            'email': self.email
        }


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    user_from_id = db.Column(db.Integer, nullable=False)
    user_to_id = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    contents = db.Column(db.String(), nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'user_from_id': self.user_from_id,
            'user_to_id': self.user_to_id,
            'timestamp': self.timestamp,
            'contents': self.contents
        }


class Invitation(db.Model):
    __tablename__ = 'invitations'

    id = db.Column(db.Integer, primary_key=True)
    user_from_id = db.Column(db.Integer, nullable=False)
    user_to_id = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(InvitationStatus), nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'user_from_id': self.user_from_id,
            'user_to_id': self.user_to_id,
            'timestamp': self.timestamp,
            'contents': self.contents
        }
