from datetime import datetime, timezone

from flask import jsonify, g
from flask import request
from flask_socketio import join_room

from database import app, db, auth, socketIO, chat_rooms, users_sids
from domain.models import User, ChatMessage
from routes.auth.auth_api import auth_api
from routes.encryption.encryption_api import encryption_api
from routes.friends.friends_api import friends_api
from routes.invites.invites_api import invites_api
from routes.messages.messages_api import messages_api
from routes.user.user_api import user_api
from utils.room_utils import can_perform_in_room, is_room_already_created

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


# ##############################
#       ERROR HANDLERS
# ##############################


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
def not_found_handler(e):
    return jsonify(message="Not found"), 404


# ##############################
#             API
# ##############################

app.register_blueprint(auth_api)
app.register_blueprint(user_api)
app.register_blueprint(encryption_api)
app.register_blueprint(friends_api)
app.register_blueprint(invites_api)
app.register_blueprint(messages_api)


# ##############################
#           SOCKETS
# ##############################


@socketIO.event
def room_message(json):
    print("=======================")
    print("sending message to room")
    print(json)

    room_name = json['roomName']
    sender_username = json['sender']
    sender_id = json['senderId']
    receiver_username = json['receiver']
    receiver_id = json['receiverId']
    contents = json['contents']
    timestamp = datetime.now(timezone.utc)

    if can_perform_in_room(room_name, json['token'], sender_username, receiver_username) is False:
        print("{} can not send message to {}".format(sender_username, room_name))
        return

    socketIO.emit("room_response", {
        'roomName': room_name,
        'senderId': sender_id,
        'receiverId': receiver_id,
        'timestamp': timestamp.isoformat(),
        'contents': contents
    }, to=room_name, include_self=True)

    msg = ChatMessage(
        senderId=sender_id,
        receiverId=receiver_id,
        timestamp=timestamp,
        contents=contents
    )

    db.session.add(msg)
    db.session.commit()
    print("message sent")
    print("chat rooms: {}".format(chat_rooms))
    print("=======================")


@socketIO.on('join')
def join(message):
    recipient = message['recipient']
    token = message['token']
    username = message['username']

    room_name = str(hash(frozenset([recipient, username])))
    sid = request.sid
    recipient_from_db = User.query.filter_by(username=recipient).first()

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
            print("{} already in {}, emitting room name response".format(username, room_name))
            join_room(room_name)
            socketIO.emit('room name response', {'roomName': room_name,
                                                 'recipientId': recipient_from_db.id,
                                                 'recipient': recipient}, to=sid)
        elif len(users_in_room) < 3:
            users_in_room.append(username)
            chat_rooms[room_name] = users_in_room
            join_room(room_name)
            print("{} joined to {}".format(username, room_name))

    print("chat rooms: {}".format(chat_rooms))

    socketIO.emit('room name response', {'roomName': room_name,
                                         'recipientId': recipient_from_db.id,
                                         'recipient': recipient}, to=sid)


@socketIO.event
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
        print("chat rooms: {}".format(chat_rooms))
    else:
        print("{} can not leave {}, as he is not in this room".format(username, room_name))

    if len(users_in_room) == 0:
        chat_rooms.pop(room_name)


@socketIO.event
def sid_event(json):
    username = json['username']
    sid = json['sid']
    users_sids[sid] = username


@socketIO.event
def connect():
    print(f"connected {request.sid}")
    socketIO.emit("sid", {"sid": request.sid}, to=request.sid)


@socketIO.event
def disconnect():
    sid = request.sid
    print(chat_rooms)
    print(f"user disconnected {sid}")
    for room_name, users_in_room in chat_rooms.items():
        temp_arr = chat_rooms[room_name]
        if sid in users_sids.keys():
            if users_sids[sid] in users_in_room:
                print("user was in room, removing...")
                temp_arr.remove(users_sids[sid])
                chat_rooms[room_name] = temp_arr
    print(chat_rooms)

    keys_to_delete = []
    for room_name, users_in_room in chat_rooms.items():
        if len(users_in_room) == 0:
            keys_to_delete.append(room_name)

    for key in keys_to_delete:
        chat_rooms.pop(key)

    users_sids.pop(sid, None)

    print(chat_rooms)


if __name__ == '__main__':
    socketIO.run(app, host='127.0.0.1', port=8081, debug=True)
