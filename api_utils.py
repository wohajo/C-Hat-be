import os
from threading import Thread

from flask import abort, make_response, jsonify
from flask_mail import Message

from database import mail, app


def abort_with_message(message, status):
    """
    Creates error status based on parameters.

    :param message: string containing message for API
    :param status: integer HTTP status code
    """
    abort(make_response(jsonify(message=message), status))


class ThreadedEmail(Thread):
    def __init__(self, email):
        self.email = email
        Thread.__init__(self)

    def run(self):
        msg = Message('Registration', sender=os.environ['MAIL_USERNAME'], recipients=[self.email])
        msg.body = "Thank You for registering to c-hat."
        with app.app_context():
            mail.send(msg)
