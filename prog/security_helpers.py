#!/usr/bin/env python3
"""
Security Helpers Module
Input validation, CSRF protection, and security headers
"""
import re
from functools import wraps
from flask import request, jsonify, session
from werkzeug.security import generate_password_hash
import secrets


def validate_voucher_code(code):
    """Validate voucher code format"""
    if not code:
        return False, "Voucher code is required"
    
    if not isinstance(code, str):
        return False, "Voucher code must be a string"
    
    # Check length (12 characters for standard, or longer for secure codes)
    if len(code) < 12 or len(code) > 100:
        return False, "Invalid voucher code length"
    
    # Check format (alphanumeric or with separators for secure codes)
    if not re.match(r'^[A-Za-z0-9|_\-\.]+$', code):
        return False, "Voucher code contains invalid characters"
    
    return True, "Valid"


def validate_phone_number(phone):
    """Validate phone number format"""
    if not phone:
        return False, "Phone number is required"
    
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Check if it's numeric (with optional leading +)
    if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
        return False, "Invalid phone number format"
    
    return True, "Valid"


def validate_employee_id(employee_id):
    """Validate employee ID format"""
    if not employee_id:
        return False, "Employee ID is required"
    
    if not isinstance(employee_id, str):
        return False, "Employee ID must be a string"
    
    if len(employee_id) < 3 or len(employee_id) > 20:
        return False, "Employee ID must be 3-20 characters"
    
    if not re.match(r'^[A-Za-z0-9_\-]+$', employee_id):
        return False, "Employee ID contains invalid characters"
    
    return True, "Valid"


def validate_date_format(date_str, format='%Y-%m-%d'):
    """Validate date format"""
    from datetime import datetime
    
    if not date_str:
        return False, "Date is required"
    
    try:
        datetime.strptime(date_str, format)
        return True, "Valid"
    except ValueError:
        return False, f"Invalid date format. Expected {format}"


def sanitize_input(text, max_length=500):
    """Sanitize user input"""
    if not text:
        return ''
    
    if not isinstance(text, str):
        text = str(text)
    
    # Remove null bytes and trim
    text = text.replace('\x00', '').strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_json_request():
    """Validate JSON request"""
    if not request.is_json:
        return False, "Content-Type must be application/json"
    return True, "Valid"


def generate_csrf_token():
    """Generate CSRF token"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    return session['csrf_token']


def validate_csrf_token(token=None):
    """Validate CSRF token"""
    if token is None:
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
    
    if not token:
        return False, "CSRF token missing"
    
    if token != session.get('csrf_token'):
        return False, "Invalid CSRF token"
    
    return True, "Valid"


def csrf_protect(f):
    """Decorator for CSRF protection"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip CSRF for GET requests
        if request.method == 'GET':
            return f(*args, **kwargs)
        
        # Validate CSRF token
        is_valid, message = validate_csrf_token()
        if not is_valid:
            return jsonify({'success': False, 'message': message}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def add_security_headers(response):
    """Add security headers to response"""
    #response.headers['X-Content-Type-Options'] = 'nosniff'
    #response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    #response.headers['X-XSS-Protection'] = '1; mode=block'
    #response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    #response.headers['Content-Security-Policy'] = "default-src 'self'"

    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline';"
    # other security headers you may keep:
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer-when-downgrade'
    

    
    
    return response


def validate_input(data, schema):
    """
    Validate input data against schema
    
    Example schema:
    {
        'code': {'required': True, 'validator': validate_voucher_code},
        'phone': {'required': False, 'validator': validate_phone_number}
    }
    """
    errors = {}
    
    for field, rules in schema.items():
        value = data.get(field)
        
        # Check required
        if rules.get('required', False) and not value:
            errors[field] = f"{field} is required"
            continue
        
        # Skip validation if not required and not provided
        if not value and not rules.get('required', False):
            continue
        
        # Run validator
        validator = rules.get('validator')
        if validator:
            is_valid, message = validator(value)
            if not is_valid:
                errors[field] = message
    
    if errors:
        return False, errors
    
    return True, {}

