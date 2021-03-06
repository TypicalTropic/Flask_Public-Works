
import random
from flask_mail import Message
from flask import render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user
)

from app import db, login_manager, mail
from app.auth import blueprint
from app.auth.forms import LoginForm, CreateAccountForm, OtpForm
from app.models import Users,Employee
from app.auth.util import verify_pass

# Login & Registration

@blueprint.route('/auth/login', methods=['GET','POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        form_id = request.form['trn']
        password = request.form['password']

        # Locate user
        user = Users.query.filter_by(id=form_id).first()

        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('employee_blueprint.employee_index'))

        # Something (user or pass) is not ok
        return render_template('auth/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('auth/login.html',
                               form=login_form)

    return redirect(url_for('employee_blueprint.employee_index'))


@blueprint.route('/auth/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        form_user = request.form['trn']
        form_email = request.form['email']
        form_password = request.form['password']

        # Check usename exists
        user = Users.query.filter_by(id=form_user).first()
        employee = Employee.query.filter_by(trn=form_user).first()
        if user:
            return render_template('auth/register.html',
                                   msg='TRN already registered',
                                   success=False,
                                   form=create_account_form)
        if not employee:
            return render_template('auth/register.html',
                                   msg=f'{form_user}, Is not an employee',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = Users.query.filter_by(email=form_email).first()
        if user:
            return render_template('auth/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        user = Users(id=form_user,email=form_email,password=form_password)
        db.session.add(user)
        db.session.commit()

        return render_template('auth/register.html',
                               msg='User created please <a href="/login">login</a>',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('auth/register.html', form=create_account_form)

@blueprint.route('/auth/manager/login', methods=['GET','POST'])
def manager_login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        form_id = request.form['trn']
        password = request.form['password']

        # Locate user
        user = Users.query.filter_by(id=form_id).first()

        # Check the password
        if user and verify_pass(password, user.password):
            if user.manager == False:
                return render_template('auth/manager-login.html',msg='This account is not authorized',form=login_form)
            return redirect(url_for('auth_blueprint.otp_verify',email=user.email))

        # Something (user or pass) is not ok
        return render_template('auth/manager-login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('auth/manager-login.html',
                               form=login_form)

    return redirect(url_for('manager_blueprint.manager'))


@blueprint.route('/auth/otp/<string:email>', methods=['GET','POST'])
def otp_verify(email):
    form = OtpForm(request.form)
    global otp
    if request.method == 'POST':
        user = Users.query.filter_by(email=email).first()
        form_otp = int(request.form['otp'])
        if form_otp == otp:
            login_user(user)
            return redirect(url_for('manager_blueprint.manager'))
        else:
            return render_template('auth/otp.html',msg='Wrong OTP a New OTP Has Been Sent',form = form)

    otp = random.randint(100000,999999)
    mail.connect()
    msg = Message('Your One Time Password',sender='noreply@publicworks.com', recipients=[email])
    msg.body = f'Your OTP IS {otp}'
    mail.send(msg)
    return render_template('auth/otp.html',form = form)
    

@blueprint.route('/auth/logout')
def logout():
    logout_user()
    return redirect(url_for('user_blueprint.index'))


# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('error/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('error/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('error/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('error/page-500.html'), 500