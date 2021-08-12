from flask import current_app
from flask_mail import Message
from threading import Thread 
from app import mail


def send_async_mail(app, msg):
    with app.app_context():
        mail.send(msg)


def send_mail(subject, sender, recipients, text_body, html_body, 
              attachments=None, sync=False):
    """This function implements a helper to send emails using Flask-Mail."""

    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body 
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)    
    if sync:
        mail.send(msg)
    else:
        Thread(target=send_async_mail, 
               args=(current_app._get_current_object(), msg)).start()
