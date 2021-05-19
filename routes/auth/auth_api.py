import os

from flask import Blueprint, jsonify, g

from database import auth

auth_api = Blueprint('auth_api', __name__)


@auth_api.route('/api/auth/login', methods=['POST'])
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(os.environ['TOKEN_TIME_VALIDITY'])
    return jsonify({'token': token,
                    'duration': os.environ['TOKEN_TIME_VALIDITY'],
                    'username': g.user.username,
                    'id': g.user.id})
