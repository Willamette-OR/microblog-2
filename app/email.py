from flask_mail import Message
from threading import Thread 
from app import app, mail


def send_async_mail(app, msg):
    with app.app_context():
        mail.send(msg)


def send_mail(subject, sender, recipients, text_body, html_body):
    """This function implements a helper to send emails using Flask-Mail."""

    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body 
    Thread(target=send_async_mail, args=(app, msg)).start()
