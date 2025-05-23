# /flask_app/app/auth/routes.py
from flask import render_template, redirect, url_for, flash, request, session, current_app
from . import bp
from ..core.credentials import load_credentials, save_credentials, hash_password
from ..core.clients import clear_user_clients # For logout
import os

@bp.route('/login_signup', methods=['GET'])
def login_signup_page():
    if 'logged_in' in session:
        return redirect(url_for('main.main_app_page'))
    session['viewed_front_page'] = True # Assume if they reach here, welcome is passed
    return render_template('auth/login_signup.html')

@bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Username and password are required.", "warning")
        return redirect(url_for('.login_signup_page'))

    credentials = load_credentials()
    hashed_password_attempt = hash_password(password)
    user_creds = credentials.get(username)

    if user_creds and user_creds.get('password') == hashed_password_attempt:
        session.clear() # Clear old session data before setting new
        session['logged_in'] = True
        session['username'] = username
        session['folder_path'] = user_creds.get('folder_path')
        session['chat_messages'] = []
        session['search_results'] = None
        session.pop('clients_initialized', None) 

        if not session['folder_path'] or not os.path.isdir(session['folder_path']):
            flash(f"Welcome, {username}! Your configured folder ('{session.get('folder_path', 'Not Set')}') is invalid. Please update it.", "warning")
            return redirect(url_for('main.change_folder_page'))

        flash(f"Logged in successfully as {username}!", "success")
        return redirect(url_for('main.main_app_page'))
    else:
        flash("Invalid username or password.", "danger")
        return redirect(url_for('.login_signup_page'))

@bp.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    folder_path = request.form.get('folder_path')

    if not all([username, password, folder_path]):
        flash("All fields are required for signup.", "warning")
        return redirect(url_for('.login_signup_page'))

    credentials = load_credentials()
    if username in credentials:
        flash("Username already exists.", "danger")
        return redirect(url_for('.login_signup_page'))

    if not os.path.isdir(folder_path):
        flash(f"The folder path '{folder_path}' is not a valid directory.", "danger")
        return redirect(url_for('.login_signup_page'))

    hashed_password = hash_password(password)
    credentials[username] = {'password': hashed_password, 'folder_path': folder_path}
    
    if not save_credentials(credentials):
        return redirect(url_for('.login_signup_page')) # save_credentials flashes its own error

    session.clear() # Clear any previous session data
    session['logged_in'] = True
    session['username'] = username
    session['folder_path'] = folder_path
    session['chat_messages'] = []
    session['search_results'] = None
    session.pop('clients_initialized', None)

    flash(f"Welcome, {username}! Signup successful.", "success")
    return redirect(url_for('main.main_app_page'))

@bp.route('/logout')
def logout():
    username_to_logout = session.get('username')
    if username_to_logout:
        clear_user_clients(username_to_logout)
    
    session.clear() # Clears all session data
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('.login_signup_page'))