from flask import render_template
from app import app

@app.route('/')
@app.route('/index')
def index():
    """This function implements what the index page displays."""

    user = {'username': 'Peipei'}

    return render_template('index.html', title='Home', user=user)