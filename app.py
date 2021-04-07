from flask import request, abort, jsonify, url_for, g
from database import app, db, auth
from models import User


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
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token, 'duration': 600})


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
        abort(400, 'Missing registration arguments')
    if User.query.filter_by(username=username).first() is not None:
        abort(400, 'User already registered')

    user = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email)
    user.hash_password(password)

    db.session.add(user)
    db.session.commit()
    return jsonify({'id': user.id}), 201, {'Location': url_for('get_user_by_id', id=user.id, _external=True)}


@app.route('/api/users/<int:id>')
def get_user_by_id(id):
    user = User.query.get(id)
    if not user:
        abort(404, 'User not found')
    return jsonify({'username': user.username})


@app.route('/api/test')
@auth.login_required
def get_resource():
    return jsonify({'data': 'Hello, %s!' % g.user.username})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8081, debug=True)
