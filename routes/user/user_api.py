from datetime import datetime
from time import timezone

from cerberus import Validator
from flask import Blueprint, request, jsonify, url_for, abort, make_response, g
from sqlalchemy import or_, and_

from database import auth, db
from domain.enums import FriendsRequestStatus
from domain.models import User, FriendsRequest
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
        abort_with_message("User already registered", 400)

    user = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email)
    user.hash_password(password)

    db.session.add(user)
    db.session.commit()
    ThreadedEmail(email).start()
    return jsonify({'id': user.id}), 201, {'Location': url_for('get_user_by_id', _id=user.id, _external=True)}


@user_api.route('/api/users/<_id>', methods=['GET'])
@auth.login_required
def get_user_by_id(_id):
    user = User.query.get(_id)
    if not user:
        abort(make_response(jsonify(message="User not found"), 404))
    return user.serialize_for_other(), 201


@user_api.route('/api/users/find/<string:username>', methods=['GET'])
@auth.login_required
def find_users_with_username(username):
    _username = username
    users = User.query.filter(User.username.like('{}%'.format(username))).all()
    users_serialized = [u.serialize() for u in users]

    return jsonify({'users': users_serialized})


@user_api.route('/api/users/invite/<int:user_id>', methods=['POST'])
@auth.login_required
def invite_user(user_id):
    user_from = g.user
    user_to = User.query.get(user_id)
    if user_from == user_to:
        abort(make_response(jsonify(message="You cannot invite yourself"), 403))
    if not user_to:
        abort(make_response(jsonify(message="User not found"), 404))

    friends_request_check_pending = FriendsRequest.query \
        .filter(and_(or_(and_(FriendsRequest.user_to_id == g.user.id, FriendsRequest.user_from_id == user_id),
                         and_(FriendsRequest.user_from_id == g.user.id, FriendsRequest.user_to_id == user_id)),
                     FriendsRequest.status == FriendsRequestStatus.pending)
                ).all()

    if len(friends_request_check_pending) != 0:
        abort(make_response(jsonify(message="Invitation is already pending"), 409))

    friends_request_check_accepted = FriendsRequest.query \
        .filter(and_(or_(and_(FriendsRequest.user_to_id == g.user.id, FriendsRequest.user_from_id == user_id),
                         and_(FriendsRequest.user_from_id == g.user.id, FriendsRequest.user_to_id == user_id)),
                     FriendsRequest.status == FriendsRequestStatus.accepted)
                ).all()

    if len(friends_request_check_accepted) != 0:
        abort(make_response(jsonify(message="You are already friends"), 409))

    friends_request = FriendsRequest(
        user_from_id=user_from.id,
        user_to_id=user_to.id,
        timestamp=datetime.now(timezone.utc),
        status=FriendsRequestStatus.pending,
    )

    db.session.add(friends_request)
    db.session.commit()

    return jsonify({'id': friends_request.id})
