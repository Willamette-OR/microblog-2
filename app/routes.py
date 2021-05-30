from flask import render_template, flash, redirect, url_for, request, g, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from flask_babel import _, get_locale
from werkzeug.urls import url_parse
from datetime import datetime 
from guess_language import guess_language
from app import app, db
from app.form import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, Post
from app.email import send_password_reset_email
from app.translate import translate


@app.before_request
def before_request():
    """
    This function implements logic to be executed right after each request, before calling the view functions,
    and then is registered with Flask using a built-in decorator 'before_request' of Flask.
    """

    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

    # For any request, add to the g object the selected language returned by Flask-Babel via the get_locale() function.
    # The purpose is to make the selected language accessible from the base template.
    # The get_locale() function returns a locale object, but since we only need the language code we will 
    # convert the object to a string using str()
    g.locale = str(get_locale()) if str(get_locale()) != 'zh' else 'zh-cn'
    


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    """This function implements what the index page displays."""

    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        elif language == 'zh':
            language = 'zh-cn'
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    # The paginate() call returns an object of the Paginate class.
    # The items attribute of this object contains the list of items retrieved for the selected page.
    posts = current_user.followed_posts().paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None

    return render_template('index.html', title='Home', posts=posts.items, form=form, next_url=next_url, prev_url=prev_url)


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
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            return redirect(url_for('index'))
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    """This function logs out users."""

    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """This function provides a view to register new users."""

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        u = User(username=form.username.data, email=form.email.data)
        u.set_password(form.password.data)
        db.session.add(u)
        db.session.commit()
        flash("Your are now a registered user!")
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
def user(username):
    """This function provides a view for the profile of the logged in user."""

    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.datetime.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) if posts.has_next else None 
    prev_url = url_for('user', username=user.username, page=posts.prev_num) if posts.has_prev else None 
    form = EmptyForm()

    return render_template('user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url, form=form)


@app.route('/edit_profile', methods=['POST', 'GET'])
def edit_profile():
    """This function handles the logic and rendering for profile editing."""

    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    """This function handles requests to follow a specified user."""

    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('index'))
        if user == current_user:
            flask('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are now following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    """This functions handles requests to unfollow a specified user."""

    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect('index')
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are no longer following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/explore')
@login_required
def explore():
    """This function handles requests to explore all user posts."""

    page = request.args.get('page', 1, type=int)
    # The paginate() call returns an object of the Paginate class.
    # The items attribute of this object contains the list of items retrieved for the selected page.
    posts = Post.query.order_by(Post.datetime.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) if posts.has_prev else None

    return render_template('index.html', title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """This function handles requests to email a link to reset user passwords."""

    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash("Check your email for instructions to reset your password.")
        return redirect(url_for('login'))

    return render_template('reset_password_request.html', title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """This function handles requests to reset passwords."""

    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset.")
        return redirect(url_for('login'))

    return render_template('reset_password.html', title='Reset Password', form=form)


@app.route('/translate', methods=['POST'])
@login_required
def translate_text():
    """
    This function takes arguments from POST requests for user post translations, 
    calls the pre-defined python function to translate, 
    jsonify the payload and returns the translated text to clients
    """

    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})
