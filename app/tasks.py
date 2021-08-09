import time
import sys
import json
from rq import get_current_job
from flask import render_template
from app import db, create_app
from app.models import User, Post, Task
from app.email import send_mail


app = create_app()
app.app_context().push()


def example(user_id, seconds):
    job = get_current_job()
    print("Starting task")
    for i in range(seconds):
        job.meta['progress'] = 100.0 * i / seconds
        job.save_meta()
        print(i)
        time.sleep(1)
    job.meta['progress'] = 100
    job.save_meta()
    print("Task completed")


def _set_task_progress(progress):
    """
    This helper function pushes the given progress value to notification 
    records associated with the same user, and flags the task as complete 
    if the input progress value shows so.
    """

    job = get_current_job()
    if job:
        # save progress info for the job
        job.meta['progress'] = progress
        job.save_meta()

        # push progress info to the associated user's notifications
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(), 
                                                     'progress': progress})

        # flag the task as completed if progress is greater than 100
        if progress >= 100:
            task.complete = True

        # commit database changes
        db.session.commit()


def export_posts(user_id):
    """
    This function exports the archive of posts for a given user, updates the 
    progress, emails the archive once completing the task, and also handles
    exceptions that occur within the worker process for the task.
    """

    try:
        user = User.query.get(user_id)

        # read the user's posts
        _set_task_progress(0)
        data = []
        i = 0
        total_posts = user.posts.count()
        for post in user.posts.order_by(Post.timestamp.asc()):
            data.append({'body': post.body})
            time.sleep(1)
            i += 1
            _set_task_progress(100.0 * i / total_posts)
        
        # email out the archive of posts
        send_mail(subject='Exported Posts', sender=app.config['ADMINS'][0],
                  recipients=[user.email],
                  text_body=render_template('email/export_posts.txt', 
                                            user=user),
                  html_body=render_template('email/export_posts.html',
                                            user=user), 
                  attachments=[('posts.json', 'application/json', 
                               json.dumps({'posts': data}, indent=4))],
                  sync=True)

    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)

