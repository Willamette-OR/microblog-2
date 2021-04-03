from app import app

@app.route('/')
@app.route('/index')
def index():
    """This function implements what the index page displays."""

    user = {'username': 'Peipei'}

    return """
<html>
    <head>
        <title>Home Page - Microblog</title>
    </head>
    <body>
        <h1>Hello, """ + user['username'] + """!</h1>
    </body>
</html>"""