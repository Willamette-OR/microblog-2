from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Length 
from app.models import User 


class EditProfileForm(FlaskForm):
    """This child class of FlaskForm implement a form for editing usernames and about-me's""" 

    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About Me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        """This function will be called automatically when validating the 'username' field."""

        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError("Please use a different username.")


class EmptyForm(FlaskForm):
    """This child class of FlaskForm implement an empty form, as a tool to prevent CSRF attacks 
    when handling requests to change the state of the app."""

    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    """This child class of FlaskForm implements a form to take in new posts from users."""

    post = TextAreaField('Say something', validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')
