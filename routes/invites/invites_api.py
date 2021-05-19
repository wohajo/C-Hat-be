from flask import Blueprint, g, make_response, abort, jsonify

from database import auth, db
from domain.enums import FriendsRequestStatus
from domain.models import FriendsRequest

invites_api = Blueprint("invites_api", __name__)


@invites_api.route('/api/invites/my/<route>', methods=['GET'])
@auth.login_required()
def get_my_invites(route):
    user = g.user

    if not user:
        abort(make_response(jsonify(message="User not found"), 404))

    friends_requests = []

    if route == "pending":
        friends_requests = FriendsRequest.query.filter_by(user_to_id=user.id).filter_by(
            status=FriendsRequestStatus.pending).all()
    elif route == "sent":
        friends_requests = FriendsRequest.query.filter_by(user_from_id=user.id).filter_by(
            status=FriendsRequestStatus.pending).all()
    else:
        abort(make_response(jsonify(message="Not found"), 404))

    friends_requests_serialized = [fr.serialize() for fr in friends_requests]
    return jsonify({'invites': friends_requests_serialized})


@invites_api.route('/api/invites/<action>/<int:invite_id>', methods=['PUT'])
@auth.login_required()
def accept_or_reject_invite(action, invite_id):
    if action != 'accept' and action != 'reject':
        abort(make_response(jsonify(message="Page not found"), 404))

    friends_request = FriendsRequest.query.filter_by(id=invite_id).first()

    if not friends_request:
        abort(make_response(jsonify(message="Invite not found"), 404))

    if action == "accept":
        friends_request.status = FriendsRequestStatus.accepted
    else:
        friends_request.status = FriendsRequestStatus.rejected
    db.session.commit()

    # TODO change timestamp to accept/reject time?

    return jsonify(message="OK"), 200
