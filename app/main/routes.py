from flask import current_app, render_template, flash, redirect, url_for, request, g, jsonify
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from datetime import datetime 
from guess_language import guess_language
from app import db
from app.main import bp
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm, MessageForm
from app.models import User, Post, Message, Notification
from app.translate import translate


@bp.before_request
def before_request():
    """
    This function implements logic to be executed right after each request, before calling the view functions,
    and then is registered with Flask using a built-in decorator 'before_request' of Flask.
    """

    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()

    # For any request, add to the g object the selected language returned by Flask-Babel via the get_locale() function.
    # The purpose is to make the selected language accessible from the base template.
    # The get_locale() function returns a locale object, but since we only need the language code we will 
    # convert the object to a string using str()
    g.locale = str(get_locale()) if str(get_locale()) != 'zh' else 'zh-cn'
    

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
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
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    # The paginate() call returns an object of the Paginate class.
    # The items attribute of this object contains the list of items retrieved for the selected page.
    posts = current_user.followed_posts().paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None

    return render_template('index.html', title='Home', posts=posts.items, form=form, next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    """This function provides a view for the profile of the logged in user."""

    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) if posts.has_next else None 
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) if posts.has_prev else None 
    form = EmptyForm()

    return render_template('user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/user/<username>/popup')
def user_popup(username):
    """This view function renders user info on a popup window."""

    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()

    return render_template('user_popup.html', user=user, form=form)


@bp.route('/edit_profile', methods=['POST', 'GET'])
def edit_profile():
    """This function handles the logic and rendering for profile editing."""

    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Edit Profile', form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    """This function handles requests to follow a specified user."""

    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are now following {}!'.format(username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
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
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are no longer following {}.'.format(username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/explore')
@login_required
def explore():
    """This function handles requests to explore all user posts."""

    page = request.args.get('page', 1, type=int)
    # The paginate() call returns an object of the Paginate class.
    # The items attribute of this object contains the list of items retrieved for the selected page.
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None

    return render_template('index.html', title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/translate', methods=['POST'])
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


@bp.route('/search')
@login_required
def search():
    """This function handles requests to do full-text search."""

    # redirect to 'explore' if search form is empty
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    # get page number and run search
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page, 
                               current_app.config['POSTS_PER_PAGE'])
    # set up pagination
    next_url = url_for('main.search', q=g.search_form.q.data, page=page+1) \
        if page * current_app.config['POSTS_PER_PAGE'] < total else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page-1) \
        if page > 1 else None
    # return
    return render_template('search.html', title='Search', posts=posts,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    """This view function handles requests to send messages to other users."""

    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user, 
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification(name='unread_message_count', 
                              data=user.new_messages())
        db.session.commit()
        flash("Your message has been sent.")
        return redirect(url_for('main.user', username=recipient))

    return render_template('send_message.html', title='Send Message', 
                           recipient=recipient, form=form)


@bp.route('/messages')
@login_required
def messages():
    """This view function handles requests to view received messages."""

    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification(name='unread_message_count', data=0)
    db.session.commit()

    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(page, 
        current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    
    return render_template('messages.html', title='Messages', 
                           messages=messages.items, next_url=next_url, 
                           prev_url=prev_url)


@bp.route('/notifications')
@login_required
def notifications():
    """This view function handles Ajax requests to fetch notifications."""

    since = request.args.get('since', 1.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp 
        } for n in notifications])
