import os 

class Config:
    """This class implements configuration variables for Microblog's flask objects."""

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess-it'