import secrets
import os
from PIL import Image
import socket
from flask import render_template, redirect, url_for, flash, request, abort
from flaskblog import app, db, bcrypt, mail
from flaskblog.forms import (SignupForm, SigninForm, UpdateAccountForm,
                             PostForm, RequestResetForm, ResetPasswordForm)
from flaskblog.models import User, Post
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message


@app.route('/')
@app.route('/home')
def index():
    posts = Post.query.all()
    return render_template('index.html', title="Welcome", posts=posts)


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


@app.route('/about')
def about():
    return render_template('about.html', title="About")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = \
            bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created! You are now able to login',
              'success')
        return redirect(url_for('signin'))

    return render_template('signup.html', title="Sign Up", form=form)


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SigninForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash(f'Login Failed. Please check email & password', 'danger')

    return render_template('signin.html', title="Sign In", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path,
                                'static/img/profile_pics',
                                picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if current_user.username != form.username.data or \
                current_user.email != form.email.data or \
                (form.picture.data and
                 current_user.img_file != form.picture.data.filename):
            current_user.username = form.username.data
            current_user.email = form.email.data
            old_image = os.path.join(app.root_path,
                                     'static/img/profile_pics',
                                     current_user.img_file)
            current_user.img_file = save_picture(form.picture.data)
            try:
                if os.path.basename(old_image) != 'default.jpg':
                    os.remove(old_image)
            except FileNotFoundError:
                pass
            db.session.commit()
            flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))

    image_file = url_for('static',
                         filename=f'img/profile_pics/{current_user.img_file}')
    return render_template('account.html', title="Account",
                           image_file=image_file, form=form)


@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data.title(),
                    content=form.content.data.replace('\n', '<br>'),
                    author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('index'))
    return render_template('manage_post.html', title="New Post", form=form,
                           legend="New Post")


@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data.replace('\n', '<br>')
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content.replace('<br>', '\n')

    return render_template('manage_post.html', title="Update Post", form=form,
                           legend="Update Post")


@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('index'))


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='eutesfaye10@gmail.com', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email & no changes will be made.
'''
    mail.send(msg)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        try:
            send_reset_email(user)
        except socket.gaierror:
            return redirect(url_for('no_internet'))
        else:
            flash('An email sent with instructions to reset your password',
                  'info')
            return redirect(url_for('signin'))
    return render_template('reset_request.html', title="Reset Password", form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token.', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = \
            bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Your password has been updated! You are now able to login',
              'success')
        return redirect(url_for('signin'))

    return render_template('reset_token.html', title="Reset Password", form=form)


@app.route('/no internet')
def no_internet():
    return render_template('errors/no_internet.html')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(403)
def permission_error(error):
    return render_template('errors/403.html'), 403


@app.errorhandler(505)
def internal_server_error(error):
    return render_template('errors/505.html'), 505


