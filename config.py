import os 
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """This class implements configuration variables for Microblog's flask objects."""

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess-it'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    # The SQLALCHEMY_TRACK_MODIFICATIONS configuration option is set to False to disable a feature of Flask-SQLAlchemy that I do not need, 
    # which is to signal the application every time a change is about to be made in the database.
    SQLALCHEMY_TRACK_MODIFICATIONS = False 
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None 
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['your-email@example.com']
    POSTS_PER_PAGE = 3
    LANGUAGES = ['en', 'zh']
    