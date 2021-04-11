from flask import abort, make_response, jsonify


def abort_with_message(message, status):
    """
    Creates error status based on parameters.

    :param message: string containing message for API
    :param status: integer HTTP status code
    """
    abort(make_response(jsonify(message=message), status))
