from flask import Flask, request 
from config import Config
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate  
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
import logging
from logging.handlers import SMTPHandler


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# register blueprints
from app.errors import bp as errors_bp
app.register_blueprint(errors_bp)

login = LoginManager(app)
login.login_view = 'login'
login.login_message = _l("Please log in to access this page.")
mail = Mail(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
babel = Babel(app)


@babel.localeselector
def get_locale():
    """This function returns the selected language to be used for the requests, based on the Accept-Language header from clients"""

    return request.accept_languages.best_match(app.config['LANGUAGES'])


from app import routes, models


if not app.debug:
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
     