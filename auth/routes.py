from flask import render_template, redirect, url_for, flash, request, session, jsonify
from . import auth_bp
from .forms import RegisterForm, LoginForm
import pyrebase
from config.firebase_config import FIREBASE_CONFIG

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
auth = firebase.auth()

@auth_bp.route('/test')
def auth_test():
    return "Auth blueprint is working!"

# Email existence check route
@auth_bp.route('/check-email', methods=['POST'])
def check_email():
    email = request.json.get('email')
    if not email:
        return jsonify({'exists': False, 'message': 'No email provided'})
    
    try:
        # Try to sign in with a dummy password to check if email exists
        # This will fail but give us different error messages
        try:
            auth.sign_in_with_email_and_password(email, "dummy_password_123456")
        except Exception as auth_error:
            error_str = str(auth_error)
            if "INVALID_PASSWORD" in error_str or "WRONG_PASSWORD" in error_str:
                # Email exists but password is wrong - this means email is registered
                return jsonify({'exists': True, 'message': 'Email is already registered'})
            elif "USER_NOT_FOUND" in error_str or "EMAIL_NOT_FOUND" in error_str or "INVALID_EMAIL" in error_str:
                # Email doesn't exist
                return jsonify({'exists': False, 'message': 'Email is available'})
            else:
                # Other errors, assume email doesn't exist to be safe
                return jsonify({'exists': False, 'message': 'Email is available'})
    except Exception as e:
        # For any other errors, assume email is available
        return jsonify({'exists': False, 'message': 'Email is available'})

# Home route for authentication module (for testing)

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session['user'] = {
                'email': email,
                'token': user['idToken'],
                'refreshToken': user['refreshToken'],
                'userId': user['localId']
            }
            session['just_logged_in'] = True
            flash('Login successful! Welcome to Invest Genie.', 'success')
            # Clear any modal flags since user is now logged in
            session.pop('show_login_modal', None)
            session.pop('show_register_modal', None)
            session.pop('show_forgot_modal', None)
            return redirect(url_for('home'))
        except Exception as e:
            print(f"Login error: {str(e)}")  # Debug logging
            flash('Login failed. Please check your credentials and try again.', 'danger')
            session['show_login_modal'] = True  # Keep login modal open
            return redirect(url_for('home'))
    else:
        if request.method == 'POST':
            # Show specific login validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field.title()}: {error}', 'danger')
            session['show_login_modal'] = True  # Keep login modal open for errors

    return redirect(url_for('home'))

# Registration route
from flask import session

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        # First check if user already exists
        try:
            # Try to get user info to see if email exists
            existing_user = auth.get_user_by_email(email)
            if existing_user:
                flash('This email is already registered. Please login instead or use a different email.', 'warning')
                session.pop('show_register_modal', None)
                session['show_login_modal'] = True
                return redirect(url_for('home'))
        except Exception as e:
            # User doesn't exist, which is what we want for registration
            pass
        
        # Proceed with registration
        try:
            user = auth.create_user_with_email_and_password(email, password)
            print(f"User registered successfully: {user['localId']}")  # Debug logging
            flash('Registration successful! Please log in with your new account.', 'success')
            session.pop('show_register_modal', None)  # Clear register modal flag
            session['show_login_modal'] = True  # Set flag to show login modal
            return redirect(url_for('home'))
        except Exception as e:
            print(f"Registration error: {str(e)}")  # Debug logging
            error_message = str(e)
            if "EMAIL_EXISTS" in error_message:
                flash('This email is already registered. Please login instead or use a different email.', 'warning')
                session.pop('show_register_modal', None)  # Clear register modal
                session['show_login_modal'] = True  # Show login modal instead
            elif "WEAK_PASSWORD" in error_message:
                flash('Password is too weak. Please choose a stronger password.', 'danger')
                session['show_register_modal'] = True  # Keep register modal open
            elif "INVALID_EMAIL" in error_message:
                flash('Please enter a valid email address.', 'danger')
                session['show_register_modal'] = True  # Keep register modal open
            else:
                flash('Registration failed. Please try again.', 'danger')
                session['show_register_modal'] = True  # Keep register modal open
            return redirect(url_for('home'))
    else:
        if request.method == 'POST':
            # Show specific validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field.title()}: {error}', 'danger')
            session['show_register_modal'] = True  # Keep register modal open for errors
            
    session.pop('show_register_modal', None)  # Clear flag if not submitting
    return redirect(url_for('home'))


@auth_bp.route('/logout')
def logout():
    # Clear the user from session
    session.pop('user', None)
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('home'))

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    try:
        auth.send_password_reset_email(email)
        flash('If this email is registered, a password reset link has been sent.', 'success')
    except Exception as e:
        flash('Failed to send reset email. Please try again.', 'danger')
    session['show_forgot_modal'] = True  # (Optional: to show the modal again if needed)
    return redirect(url_for('home'))