import os

from flask import abort, jsonify, url_for, g, make_response
from flask import render_template, session, request, \
    copy_current_request_context
from flask_mail import Message
from flask_socketio import emit, disconnect

from database import app, db, auth, mail, socketio, thread_lock
from models import User
from utils import abort_with_message

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


@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({'hello': 'world'})


@app.route('/api/auth/login')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(os.environ['TOKEN_TIME_VALIDITY'])
    return jsonify({'token': token, 'duration': os.environ['TOKEN_TIME_VALIDITY']})


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
    msg = Message('Registration', sender=os.environ['MAIL_USERNAME'], recipients=[email])
    msg.body = "Thank You for registering to c-hat."
    mail.send(msg)
    return jsonify({'id': user.id}), 201, {'Location': url_for('get_user_by_id', id=user.id, _external=True)}


@app.route('/api/users/<int:id>')
def get_user_by_id(id):
    user = User.query.get(id)
    if not user:
        abort(make_response(jsonify(message="User not found"), 404))
    return jsonify({'username': user.username})


@app.route('/api/test')
@auth.login_required
def get_resource():
    return jsonify({'data': 'Hello, %s!' % g.user.username})


# socket test

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count})


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.event
def my_broadcast_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.event
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)


@socketio.event
def my_ping():
    emit('my_pong')


@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)


# end of socket test


if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=8081, debug=True)
