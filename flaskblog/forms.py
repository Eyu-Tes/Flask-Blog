from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, \
    TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, \
    ValidationError
from flaskblog.models import User
from flask_login import current_user


class SignupForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(),
                                                 EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username_field):
        user = User.query.filter_by(username=username_field.data).first()
        if user:
            raise ValidationError('This username is taken. '
                                  'Please choose a different one.')

    def validate_email(self, email_field):
        user = User.query.filter_by(email=email_field.data).first()
        if user:
            raise ValidationError('This email already exists.')


class SigninForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update')
    picture = FileField('Update Profile Picture',
                        validators=[FileAllowed(['jpg', 'png', 'jpeg'],
                                                'This file is not an image!')])

    def validate_username(self, username_field):
        if username_field.data != current_user.username:
            user = User.query.filter_by(username=username_field.data).first()
            if user:
                raise ValidationError('This username is taken. '
                                      'Please choose a different one.')

    def validate_email(self, email_field):
        if email_field.data != current_user.email:
            user = User.query.filter_by(email=email_field.data).first()
            if user:
                raise ValidationError('This email already exists.')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')


class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email_field):
        user = User.query.filter_by(email=email_field.data).first()
        if user is None:
            raise ValidationError('There is no account with this email. '
                                  'You must signup first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(),
                                                 EqualTo('password')])
    submit = SubmitField('Reset Password')

