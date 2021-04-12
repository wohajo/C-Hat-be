import os

from flask import abort, jsonify, url_for, g, make_response
from flask import render_template, request
from flask_mail import Message

from database import app, db, auth, mail, socketio
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

# TODO fix error handling to return good json message
# error handlers


@app.errorhandler(405)
def method_not_allowed_handler(e):
    return jsonify(message="Invalid request"), 405


@app.errorhandler(500)
def internal_error_handler(e):
    return jsonify(message="Something went wrong"), 500


@app.errorhandler(401)
def internal_error_handler(e):
    return jsonify(message="Wrong credentials"), 401


# end of error handlers


@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({'hello': 'world'})


@app.route('/api/auth/login', methods=['POST'])
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

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


def message_received(methods=['GET', 'POST']):
    print('received message')


@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received event: ' + str(json))
    socketio.emit('my response', json, callback=message_received)


# end of socket test


if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=8081, debug=True)
