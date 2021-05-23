from flask import Blueprint, g, jsonify
from sqlalchemy import or_, and_

from database import auth, db
from domain.enums import FriendsRequestStatus
from domain.models import FriendsRequest

friends_api = Blueprint("friends_api", __name__)


@friends_api.route('/api/friends/remove/<int:friend_id>', methods=['DELETE'])
@auth.login_required()
def remove_friend(friend_id):
    FriendsRequest.query \
        .filter(or_(and_(FriendsRequest.user_to_id == g.user.id, FriendsRequest.user_from_id == friend_id),
                    and_(FriendsRequest.user_from_id == g.user.id, FriendsRequest.user_to_id == friend_id))).delete()

    db.session.commit()

    return jsonify(message="OK"), 200


@friends_api.route('/api/friends/my', methods=['GET'])
@auth.login_required()
def get_my_friends():
    user = g.user

    fr = db.session.query(FriendsRequest) \
        .filter(or_(FriendsRequest.friends_request_sender == user, FriendsRequest.friends_request_receiver == user)) \
        .filter_by(status=FriendsRequestStatus.accepted) \
        .all()

    friends = [
        f.friends_request_sender.serialize_for_other() if f.friends_request_sender != user else f.friends_request_receiver.serialize_for_other()
        for f in fr]

    return jsonify({'friends': friends}), 200
