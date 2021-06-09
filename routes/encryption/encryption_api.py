import os

from flask import Blueprint, g, request, abort

from database import auth, db
from domain.models import User

encryption_api = Blueprint('encryption_api', __name__)


@encryption_api.route('/api/encryption/base', methods=['GET'])
@auth.login_required()
def get_base():
    base = os.environ['G_BASE']
    return {'base': base}, 200


@encryption_api.route('/api/encryption/update-public-key/<int:user_id>', methods=['PUT'])
@auth.login_required()
def update_public_key(user_id):
    logged_user = g.user
    public_key = request.json.get('publicKey')

    if logged_user.id != user_id:
        abort(401, "Brak autoryzacji")

    if not public_key or len(public_key) == 0:
        abort(403, "Klucz publiczny nie może być pusty")

    user = User.query.get(user_id)
    user.public_key = public_key

    db.session.commit()
    return {'publicKey': public_key}, 200
