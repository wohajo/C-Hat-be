from flask import Blueprint, g
from sqlalchemy import or_, and_

from database import auth
from domain.models import User, ChatMessage
from utils.api_utils import abort_with_message

messages_api = Blueprint("messages_api", __name__)


@messages_api.route('/api/messages/with/<int:user_id>/<int:page>', methods=['GET'])
@auth.login_required()
def get_messages_with(user_id, page):
    user = g.user

    user_with = User.query.get(user_id)
    if not user_with:
        abort_with_message("User not found", 404)

    messages_query = ChatMessage.query \
        .filter(and_(or_(ChatMessage.message_sender == user, ChatMessage.message_receiver == user),
                     or_(ChatMessage.message_sender == user_with, ChatMessage.message_receiver == user_with))) \
        .paginate(page=page, error_out=False, per_page=80)

    messages = dict(datas=[item.serialize() for item in messages_query.items],
                    total=messages_query.total,
                    current_page=messages_query.page,
                    per_page=messages_query.per_page,
                    pages=messages_query.pages)

    return {'messages': messages}, 200
