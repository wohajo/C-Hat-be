from cerberus import Validator
from flask import Blueprint, request, jsonify, url_for, abort, make_response
from sqlalchemy import or_

from database import auth, db
from domain.models import User
from utils.api_utils import abort_with_message, ThreadedEmail, get_json

user_api = Blueprint('user_api', __name__)


@user_api.route('/api/users/register', methods=['POST'])
def register_user():
    first_name = request.json.get('firstName')
    last_name = request.json.get('lastName')
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')

    user_validator = Validator()
    user_validator.validate(request.json, get_json("user_schema"))
    if user_validator.errors:
        abort(make_response(jsonify(errors=user_validator.errors), 403))

    if None in [first_name, last_name, username, password, email]:
        abort_with_message("Form not complete", 400)
    if User.query.filter_by(username=username).first() is not None:
        abort_with_message("Taki użytkownik już istnieje", 400)

    user = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email)
    user.hash_password(password)

    db.session.add(user)
    db.session.commit()
    ThreadedEmail(email).start()
    return jsonify({'id': user.id}), 201, {'Location': url_for('user_api.get_user_by_id', _id=user.id, _external=True)}


@user_api.route('/api/users/<_id>', methods=['GET'])
@auth.login_required
def get_user_by_id(_id):
    user = User.query.get(_id)
    if not user:
        abort(make_response(jsonify(message="User not found"), 404))
    return user.serialize_for_other(), 201


@user_api.route('/api/users/find/<string:option>/<string:searched_user>', methods=['GET'])
@auth.login_required
def find_users_with_username(option, searched_user):
    if option == "username":
        users = User.query.filter(User.username.ilike(f'%{searched_user}%')).all()
        users_serialized = [u.serialize() for u in users]
        return jsonify({'users': users_serialized}), 200
    elif option == "name":
        users = User.query.filter(or_(User.first_name.ilike(f'%{searched_user}%'), User.last_name.ilike(f'%{searched_user}%'))).all()
        users_serialized = [u.serialize() for u in users]
        return jsonify({'users': users_serialized}), 200
    else:
        abort(404)
