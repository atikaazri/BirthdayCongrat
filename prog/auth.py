#!/usr/bin/env python3
"""
Authentication and Authorization Module
Handles user authentication, JWT tokens, and role-based access control
"""
import os
import csv
import jwt
import bcrypt
from functools import wraps
from datetime import datetime, timedelta
from flask import request, jsonify, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from config import Config

# Flask-Login setup
login_manager = LoginManager()
#login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.session_protection = "strong"

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production-12345')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = timedelta(hours=24)

# User storage file
USERS_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'users.csv')


class User(UserMixin):
    """User model for Flask-Login"""
    
    def __init__(self, username, password_hash, role, full_name):
        self.id = username
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.full_name = full_name
    
    @staticmethod
    def get_by_username(username):
        """Get user by username from CSV"""
        try:
            with open(USERS_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['username'] == username:
                        return User(
                            username=row['username'],
                            password_hash=row['password'],
                            role=row['role'],
                            full_name=row['full_name']
                        )
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading user: {e}")
        return None
    
    @staticmethod
    def verify_password(password_hash, password):
        """Verify password against bcrypt hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            print(f"Password verification error: {e}")
            return False
    
    def check_password(self, password):
        """Check if password matches"""
        return self.verify_password(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.get_by_username(user_id)


def generate_password_hash(password):
    """Generate bcrypt hash for password"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def create_user(username, password, role, full_name):
    """Create a new user and save to CSV"""
    try:
        password_hash = generate_password_hash(password)
        
        # Check if user exists
        if User.get_by_username(username):
            return False, "User already exists"
        
        # Append to CSV
        file_exists = os.path.exists(USERS_CSV)
        with open(USERS_CSV, 'a', newline='', encoding='utf-8') as f:
            fieldnames = ['username', 'password', 'role', 'full_name']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'username': username,
                'password': password_hash,
                'role': role,
                'full_name': full_name
            })
        
        return True, "User created successfully"
    except Exception as e:
        return False, f"Error creating user: {str(e)}"


def authenticate_user(username, password):
    """Authenticate user with username and password"""
    user = User.get_by_username(username)
    if user and user.check_password(password):
        return user
    return None


def generate_jwt_token(user):
    """Generate JWT token for user"""
    payload = {
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + JWT_EXPIRATION_DELTA,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_token_from_request():
    """Extract JWT token from request header"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return None


def jwt_required(f):
    """Decorator for JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            return jsonify({'success': False, 'message': 'No token provided'}), 401
        
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401
        
        # Add user info to request
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated_function


def role_required(required_role):
    """Decorator for role-based access control"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role != required_role and current_user.role != 'admin':
                return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator for admin-only access"""
    return role_required('admin')(f)


def cafe_required(f):
    """Decorator for cafe staff access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session-based auth (for web interface)
        if hasattr(current_user, 'role'):
            if current_user.role in ['cafe', 'admin']:
                return f(*args, **kwargs)
        
        # Check JWT auth (for API)
        token = get_token_from_request()
        if token:
            payload = verify_jwt_token(token)
            if payload and payload.get('role') in ['cafe', 'admin']:
                request.current_user = payload
                return f(*args, **kwargs)
        
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    return decorated_function

