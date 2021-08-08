from flask import Flask, request, current_app 
from config import Config
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate  
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from logging.handlers import SMTPHandler, RotatingFileHandler
from elasticsearch import Elasticsearch
from redis import Redis
import os
import logging
import rq


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = _l("Please log in to access this page.")
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
babel = Babel()


def create_app(config_class=Config):
    """This function creates an app with a specified config class, with the default set to be the default config class 'Config'."""

    # Initialize the app & config
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)

    # Initialize elasticsearch
    app.elasticsearch = Elasticsearch(app.config['ELASTICSEARCH_URL']) if app.config['ELASTICSEARCH_URL'] else None

    # Initialize Redis queue
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('microblog-tasks', connection=app.redis)

    # register the blueprint for authentication handling
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # register the blueprint for error handling
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    # register the blueprint for the main part of the app
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # create and add various loggers, and they won't be executed when debugging or testing
    if not app.debug and not app.testing:
        # create and add an email logger (for ERROR only) if the mail server has been configured
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='Microblog Failure',
                credentials=auth, secure=secure
            )   
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        # create and add a file logger
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Microblog startup')

    return app


@babel.localeselector
def get_locale():
    """This function returns the selected language to be used for the requests, based on the Accept-Language header from clients"""

    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


from app import models
