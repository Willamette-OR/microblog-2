from flask import render_template
from app import app, db 


@app.errorhandler(404)
def not_found_error(error):
    """This function renders a page to display 404 errors."""

    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """This function handles 500 errors and renders a page to display error messages."""

    db.session.rollback()
    return render_template('500.html'), 500