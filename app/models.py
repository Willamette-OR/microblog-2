from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db 


class User(db.Model):
    """This class implements the database model for users, derived from the parent class of db.Model."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    # The User class has a new posts field, that is initialized with db.relationship. This is not an actual database field, 
    # but a high-level view of the relationship between users and posts.
    # 
    # For a one-to-many relationship, a db.relationship field is normally defined on the "one" side, 
    # and is used as a convenient way to get access to the "many".
    #
    # In some instances such as in a db.relationship() call, the model is referenced by the model class, 
    # which typically starts with an uppercase character.
    # 
    # The backref argument defines the name of a field that will be added to the objects of the "many" class 
    # that points back at the "one" object. 
    # This will add a post.author expression that will return the user given a post. 
    # 
    # The lazy argument defines how the database query for the relationship will be issued, which is something that I will discuss later. 
    # Don't worry if these details don't make much sense just yet, I'll show you
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __repr__(self):
        return "<User: {}>".format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Post(db.Model):
    """This class implements the database model for posts, derived from the parent class of db.Model."""

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    # When you pass a function as a default, SQLAlchemy will set the field to the value of calling that function 
    # (note that I did not include the () after utcnow, so I'm passing the function itself, and not the result of calling it)
    datetime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # The user_id field was initialized as a foreign key to user.id, which means that it references an id value from the users table. 
    # In this reference the user part is the name of the database table for the model.
    # For multi-word model names, snake case.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))