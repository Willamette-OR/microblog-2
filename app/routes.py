from flask import render_template, flash, redirect
from app import app
from app.form import LoginForm

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
        # The flash() function is a useful way to show a message to the user. 
        # A lot of applications use this technique to let the user know if some action has been successful or not. 
        #
        # When you call the flash() function, Flask stores the message, but flashed messages will not magically appear in web pages. 
        # The templates of the application need to render these flashed messages in a way that works for the site layout.
        flash("Login requested for user {}, remember_me={}".format(form.username.data, form.remember_me.data))
        return redirect('/index')
    
    return render_template('login.html', title='Sign In', form=form)