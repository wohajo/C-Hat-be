import re
import jwt

from database import app


def can_perform_in_room(room_name, token, username, recipient):
    """
    Checks if user can perform action in given room.

    Parameters
    ----------
    room_name : string
        Name of the room to perform an action.
    token : string
        JWT token to validate.
    username : string
        Username to validate.
    recipient : string
        Recipient username to validate.
    Returns
    -------
    boolean
        Returns true if user can perform an action, false otherwise.
    """
    try:
        decoded_token = jwt.decode(token,
                                   app.config['SECRET_KEY'],
                                   algorithms=['HS256'])
        username_from_token = decoded_token.get('username')
        computed_room = hash(frozenset([recipient, username]))

        if username_from_token == username and computed_room == room_name:
            print("token_user: {}, user: {}".format(username_from_token, username))
            print("room_name: {}, hash: {}".format(room_name, computed_room))
            return True
        else:
            return False
    except:
        return False


def is_room_already_created(rooms, room_name):
    """
    Checks if room is already created.

    Parameters
    ----------
    rooms : dict
        Dictionary of rooms.
    room_name : string
        Name of the room to perform an action.
    Returns
    -------
    boolean
        Returns true if room is present in rooms, false otherwise.
    """

    return True if room_name in rooms else False
