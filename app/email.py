from flask import render_template
from flask_mail import Message
from app import app, mail


def send_mail(subject, sender, recipients, text_body, html_body):
    """This function implements a helper to send emails using Flask-Mail."""

    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body 
    mail.send(msg)


def send_password_reset_email(user):
    """This function sends password reset emails to specified users."""

    token = user.get_reset_password_token()
    send_mail('[Microblog] Reset Your Password',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt', user=user, token=token),
               html_body=render_template('email/reset_password.html', user=user, token=token))
