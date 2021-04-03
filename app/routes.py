from app import app

@app.route('/')
@app.route('/index')
def index():
    """This function implements what the index page displays."""

    return "Hello World!"