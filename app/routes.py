from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_user
from app import app
from app.form import LoginForm
from app.models import User

@app.route('/')
@app.route('/index')
def index():
    """This function implements what the index page displays."""

    user = {'username': 'Peipei'}
    posts = [
        {
            'username': 'Baiber',
            'body': 'Beautiful day in Portland!'
        },
        {
            'username': 'Peipei',
            'body': 'The new movie on Netflix is great!'
        }
    ]

    return render_template('index.html', title='Home', user=user, posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """This function implements the login view."""

    if current_user.is_authenticated:
            return redirect(url_for('index'))

    form = LoginForm()

    # The form.validate_on_submit() method does all the form processing work. 
    # When the browser sends the GET request to receive the web page with the form, this method is going to return False, 
    # so in that case the function skips the if statement and goes directly to render the template in the last line of 
    # the function.
    # 
    # When the browser sends the POST request as a result of the user pressing the submit button, 
    # form.validate_on_submit() is going to gather all the data, run all the validators attached to fields, 
    # and if everything is all right it will return True, indicating that the data is valid and can be processed 
    # by the application. But if at least one field fails validation, then the function will return False, 
    # and that will cause the form to be rendered back to the user, like in the GET request case. 
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            # The flash() function is a useful way to show a message to the user. 
            # A lot of applications use this technique to let the user know if some action has been successful or not. 
            #
            # When you call the flash() function, Flask stores the message, but flashed messages will not magically appear in web pages. 
            # The templates of the application need to render these flashed messages in a way that works for the site layout.
            flash("Invalid user or password.")

            # One problem with writing links directly in templates and source files is that if one day you decide to 
            # reorganize your links, 
            # then you are going to have to search and replace these links in your entire application.
            # To have better control over these links, Flask provides a function called url_for(), 
            # which generates URLs using its internal mapping of URLs to view functions.
            # The argument to url_for() is the endpoint name, which is the name of the view function.
            # The fact is that URLs are much more likely to change than view function names, which are completely internal. 
            # A secondary reason is that as you will learn later, some URLs have dynamic components in them, 
            # so generating those URLs by hand would require concatenating multiple elements, which is tedious and error prone. 
            # The url_for() is also able to generate these complex URLs.
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    
    return render_template('login.html', title='Sign In', form=form)