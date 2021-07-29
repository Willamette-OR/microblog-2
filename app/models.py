from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt 
from app import db, login 
from app.search import query_index, add_to_index, remove_from_index 


class SearchableMixin(object):
    """
    A class for SQLAlchemy data models to inherit from, with methods for full-text search and synchronizing database changes
    between SQLAlchemy and index.
    """

    @classmethod
    def search(cls, expression, page, per_page):
        """Class method to do full-text search and return a list of data objects."""

        # search, and return id's of objects in the search results & the total number of search results
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        # return null values if the search did not return any results
        if total == 0:
            return cls.query.filter_by(id=0), 0
        # return objects in the same order returned by the search, and the total number of search results
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        """
        Class method to save db session changes before committing, so that the same changes can be applied to the search 
        index after successfully committing
        """

        # save objects that are added, updated, or deleted into a dictionary attached to the session
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        """Class method to update the full-text search index based on changes made to the SQLAlchemy db."""

        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        """Class method to refresh a full-text search index with all the data from the relational db."""

        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


# set up event handlers that make SQLAlchemy call SearchableMixin's before_commit() and after_commit()
# before and after commits
db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    """
    This class implements the database model for users, derived from the parent class of db.Model.

    The Flask-Login extension works with the application's user model, and expects certain properties and 
    methods to be implemented in it. This approach is nice, because as long as these required items are added to the model, 
    Flask-Login does not have any other requirements, so for example, 
    it can work with user models that are based on any database system.

    The four required items are listed below:

    is_authenticated: a property that is True if the user has valid credentials or Falseotherwise.
    is_active: a property that is True if the user's account is active or False otherwise.
    is_anonymous: a property that is False for regular users, and True for a special, anonymous user.
    get_id(): a method that returns a unique identifier for the user as a string (unicode, if using Python 2).

    I can implement these four easily, but since the implementations are fairly generic, 
    Flask-Login provides a mixin class called UserMixin that includes generic implementations that 
    are appropriate for most user model classes.
    """

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
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship('User', secondary=followers, 
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic'
        )
    messages_sent = db.relationship('Message', 
        foreign_keys='Message.sender_id', backref='author', lazy='dynamic')
    messages_received = db.relationship('Message',
        foreign_keys='Message.recipient_id', backref='recipient', 
        lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)

    def __repr__(self):
        return "<User: {}>".format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        """
        This method currently leverages Gravatar to generate avatars for users.
        In the future, if it is decided to use something other than Gravatar, I can simply update this method,
        and avatars will be updated but without having to change all the templates where avatars are rendered.
        """
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def follow(self, user):
        """This method adds a user to the list of followed's of the self user, if not already followed."""

        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        """This method removes a user from the list of followe's of the self user, if still followed."""

        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        """This method checks if a user is being followed by the self user."""

        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        """This method queries all posts of self and self's followed users and order them by descending timestamps."""

        followed = Post.query.join(followers, (followers.c.followed_id==Post.user_id)).filter(
            followers.c.follower_id==self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        """This method gets a JWT token for password resets."""

        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in}, current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        """This method verifies JWT tokens for password resets."""

        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms='HS256')['reset_password']
        except:
            return 
        else:
            return User.query.get(id)

    def new_messages(self):
        """This method returns the number of unread messages."""

        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()


@login.user_loader
def load_user(id):
    """This function implements a user loader, required by Flask-Login, and returns the user object given a user id."""
    return User.query.get(int(id))


class Post(SearchableMixin, db.Model):
    """This class implements the database model for posts, derived from the parent class of db.Model."""

    # an attribute for the full-text search abstraction
    __searchable__ = ['body']

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    # When you pass a function as a default, SQLAlchemy will set the field to the value of calling that function 
    # (note that I did not include the () after utcnow, so I'm passing the function itself, and not the result of calling it)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # The user_id field was initialized as a foreign key to user.id, which means that it references an id value from the users table. 
    # In this reference the user part is the name of the database table for the model.
    # For multi-word model names, snake case.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post: {}>'.format(self.body)


class Message(db.Model):
    """
    This class implements the data model for messages, drived from the parent 
    class of db.Model.
    """

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message: {}>'.format(self.body)
