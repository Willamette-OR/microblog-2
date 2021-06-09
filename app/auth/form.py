from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_babel import lazy_gettext as _l 
from app.models import User


class LoginForm(FlaskForm):
    """This class implements login forms."""

    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """This class implements a registration form."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_2 = PasswordField('Repeat password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """This function will be automatically called when validating the 'username' field."""

        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        """This function will be automatically called when validating the 'email' field."""

        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Please use a different email address.")


class ResetPasswordRequestForm(FlaskForm):
    """This child class of FlaskForm implements a simple form to request password resets."""

    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Request')


class ResetPasswordForm(FlaskForm):
    """This child class of FlaskForm implements a form to reset user passwords."""

    password = PasswordField('Password', validators=[DataRequired()])
    repeat_password = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
