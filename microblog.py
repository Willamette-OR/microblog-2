from app import create_app, db, cli
from app.models import User, Post 


app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context():
    """This function is decorated and registered as a shell context function."""

    return {'db': db, 'User': User, 'Post': Post}