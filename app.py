import os
from datetime import datetime, timezone

from flask import abort, jsonify, url_for, g, make_response
from flask import request
from flask_socketio import join_room, rooms
from sqlalchemy import or_

from api_utils import abort_with_message
from database import app, db, auth, socketio, chat_rooms
from enums import FriendsRequestStatus
from models import User, FriendsRequest
from room_utils import can_perform_in_room, is_room_already_created

thread = None


@auth.verify_password
def verify_password(username_or_token, password):
    user = User.verify_auth_token(username_or_token)
    if not user:
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


# TODO fix error handling to return good json message
# error handlers


@app.errorhandler(405)
def method_not_allowed_handler(e):
    return jsonify(message="Invalid request"), 405


@app.errorhandler(500)
def internal_error_handler(e):
    return jsonify(message="Something went wrong"), 500


@app.errorhandler(401)
def wrong_credentials_handler(e):
    return jsonify(message="Wrong credentials"), 401


@app.errorhandler(404)
def wrong_credentials_handler(e):
    return jsonify(message="Not found"), 404


# end of error handlers


@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({'hello': 'world'})


@app.route('/api/auth/login', methods=['POST'])
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(os.environ['TOKEN_TIME_VALIDITY'])
    return jsonify({'token': token, 'duration': os.environ['TOKEN_TIME_VALIDITY'], 'username': g.user.username})


@app.route('/api/users/register', methods=['POST'])
def register_user():
    first_name = request.json.get('firstName')
    last_name = request.json.get('lastName')
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')

    # TODO validate email and stuff
    # TODO return json on abort instead of html
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
    # TODO fix this long lasting email sending
    # msg = Message('Registration', sender=os.environ['MAIL_USERNAME'], recipients=[email])
    # msg.body = "Thank You for registering to c-hat."
    # mail.send(msg)
    return jsonify({'id': user.id}), 201, {'Location': url_for('get_user_by_id', id=user.id, _external=True)}


@app.route('/api/users/<_id>', methods=['GET'])
@auth.login_required
def get_user_by_id(_id):
    user = User.query.get(_id)
    if not user:
        abort(make_response(jsonify(message="User not found"), 404))
    return jsonify({'username': user.username})


@app.route('/api/users/find/<string:username>', methods=['GET'])
@auth.login_required
def find_users_with_username(username):
    _username = username
    users = User.query.filter(User.username.like('{}%'.format(username))).all()
    users_serialized = [u.serialize() for u in users]

    return jsonify({'users': users_serialized})


@app.route('/api/users/invite/<int:user_id>', methods=['POST'])
@auth.login_required
def invite_user(user_id):
    user_from = g.user
    user_to = User.query.get(user_id)
    if user_from == user_to:
        abort(make_response(jsonify(message="You cannot invite yourself"), 403))
    if not user_to:
        abort(make_response(jsonify(message="User not found"), 404))

    friends_request_check = FriendsRequest.query.filter_by(user_from_id=user_from.id,
                                                           user_to_id=user_to.id,
                                                           status=FriendsRequestStatus.pending).all()

    if friends_request_check:
        abort(make_response(jsonify(message="Invitation is already pending"), 409))

    friends_request = FriendsRequest(
        user_from_id=user_from.id,
        user_to_id=user_to.id,
        timestamp=datetime.now(timezone.utc),
        status=FriendsRequestStatus.pending,
    )

    db.session.add(friends_request)
    db.session.commit()

    return jsonify({'id': friends_request.id})


@app.route('/api/invites/my/<route>', methods=['GET'])
@auth.login_required()
def get_my_invites(route):
    user = g.user

    if not user:
        abort(make_response(jsonify(message="User not found"), 404))

    friends_requests = []

    if route == "incoming":
        friends_requests = FriendsRequest.query.filter_by(user_to_id=user.id).all()
    elif route == "sent":
        friends_requests = FriendsRequest.query.filter_by(user_from_id=user.id).all()
    else:
        abort(make_response(jsonify(message="Not found"), 404))

    friends_requests_serialized = [fr.serialize() for fr in friends_requests]
    return jsonify({'invites': friends_requests_serialized})


@app.route('/api/invites/<action>/<int:invite_id>', methods=['POST'])
@auth.login_required()
def accept_invite(action, invite_id):
    if action != 'accept' or action != 'reject':
        abort(make_response(jsonify(message="Not found"), 404))

    friends_request = FriendsRequest.query.filter_by(id=invite_id).first()

    if not friends_request:
        abort(make_response(jsonify(message="Invite not found"), 404))

    if action == "accept":
        friends_request.status = FriendsRequestStatus.accepted
    else:
        friends_request.status = FriendsRequestStatus.rejected
    db.session.commit()

    return jsonify(message="OK"), 200


@app.route('/api/friends/my', methods=['GET'])
@auth.login_required()
def get_my_friends():
    user = g.user

    fr = db.session.query(FriendsRequest) \
        .filter(or_(FriendsRequest.friends_request_sender == user, FriendsRequest.friends_request_receiver == user)) \
        .filter_by(status=FriendsRequestStatus.accepted) \
        .all()

    friends = [
        f.friends_request_sender.serialize() if f.friends_request_sender != user else f.friends_request_receiver.serialize()
        for f in fr]
    print(friends)

    return jsonify({'friends': friends}), 200


def message_received(methods=['GET', 'POST']):
    print('received message')


@socketio.on('global message')
def global_message(json, methods=['GET', 'POST']):
    print('received event: ' + str(json))
    socketio.emit('global response', json, callback=message_received)


# json of a message:
# roomName
# sender
# token
# receiver
# contents


@socketio.event
def send_to_room(json):
    print("sending message to room")

    if can_perform_in_room(json['roomName'], json['token'], json['sender'], json['receiver']) is False:
        print("{} can not send message to {}".format(json['sender'], json['roomName']))
        return

    new_json = {
        'roomName': json['roomName'],
        'sender': json['sender'],
        'receiver': json['receiver'],
        'contents': json['contents']
    }

    socketio.emit('room_name_response', new_json, to=new_json['roomName'])


@socketio.event
def join(message):
    recipient = message['recipient']
    token = message['token']
    username = message['username']
    room_name = str(hash(frozenset([recipient, username])))
    sid = request.sid

    print("{} {} {} to {}".format(room_name, token, username, recipient))

    if username == recipient:
        print("User cannot join room with himself")
        return

    if can_perform_in_room(room_name, token, username, recipient) is False:
        print("{} can not join {}".format(username, room_name))
        return

    if is_room_already_created(chat_rooms, room_name) is False:
        users_in_room = [username]
        chat_rooms[room_name] = users_in_room
        join_room(room_name)
        print("{} created and joined to {}".format(username, room_name))
    else:
        users_in_room = chat_rooms[room_name]

        if username in users_in_room:
            print("{} already in {}".format(username, room_name))
        elif len(users_in_room) < 3:
            users_in_room.append(username)
            chat_rooms[room_name] = users_in_room
            join_room(room_name)
            print("{} joined to {}".format(username, room_name))

    print("chat rooms: {}".format(chat_rooms))

    print("{}: {}".format(username, sid))
    print("{}: {}".format(username, rooms()))
    socketio.emit('room_name_response', {'roomName': room_name, 'recipient': recipient}, to=sid)


@socketio.event
def leave(message):
    recipient = message['recipient']
    token = message['token']
    username = message['username']
    room_name = str(hash(frozenset([recipient, username])))

    if can_perform_in_room(room_name, token, username, recipient) is False:
        print("{} can not leave {}".format(username, room_name))
        return

    if room_name in chat_rooms:
        users_in_room = chat_rooms[room_name]
    else:
        print("{} can not leave room as it not exists".format(username))
        return

    if username in users_in_room:
        users_in_room.remove(username)
        print("{} left {}".format(username, room_name))
        chat_rooms[room_name] = users_in_room
    else:
        print("{} can not leave {}, as he is not in this room".format(username, room_name))

    if len(users_in_room) == 0:
        chat_rooms.pop(room_name)


if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=8081, debug=True)
