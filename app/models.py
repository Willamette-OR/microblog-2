from datetime import datetime
from app import db 


class User(db.Model):
    """This class implements the database model for users, derived from the parent class of db.Model."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __repr__(self):
        return "<User: {}>".format(self.username)


class Post(db.Model):
    """This class implements the database model for posts, derived from the parent class of db.Model."""

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    datetime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))