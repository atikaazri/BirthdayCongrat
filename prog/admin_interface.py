#!/usr/bin/env python3
"""
Admin Interface - Full System Management
Complete interface for administrators to manage the voucher system

Admin Interface for BDVoucher System
Independent Flask app running on its own port (e.g. 5002)
Provides administrator login and voucher system management
"""

import os
import sys


from flask import Flask, render_template_string, request, jsonify, session, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import (
    login_user, logout_user, current_user, login_required
)

from config import Config
from database import (
    load_employees, 
    get_birthday_today, 
    create_voucher, 
    redeem_voucher, 
    generate_qr_code, 
    get_all_vouchers,
    get_voucher_history, 
    get_system_stats, 
    refresh_data
)

from auth import (
    login_manager,
    User, 
    authenticate_user, 
    login_user, 
    logout_user, 
    login_required, 
    admin_required, 
    generate_jwt_token
)


from security_helpers import (
    validate_voucher_code, 
    validate_phone_number, 
    validate_employee_id, 
    validate_input, 
    sanitize_input,
    add_security_headers, 
    generate_csrf_token
)


from whatsapp_service import send_whatsapp_message
import csv



# ============= ADMIN FLASK APPLICATION =============
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-this-secret-key-in-production-12345')

# Initialize Flask-Login
login_manager.init_app(app)
login_manager.login_view = 'admin_login'  # Set login view route name
login_manager.login_message = 'Please log in to access this page.'
login_manager.session_protection = "strong"

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)



# Add security headers to all responses
# Security headers
@app.after_request
def set_security_headers(response):
    return add_security_headers(response)
    

# ============= ADMIN HTML TEMPLATE =============

# Admin HTML template - Full management interface
ADMIN_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{cafe_name}} - Admin Panel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .header { 
            text-align: center; 
            margin-bottom: 40px; 
            border-bottom: 3px solid #3498db;
            padding-bottom: 20px;
        }
        h1 { 
            color: #2c3e50; 
            margin-bottom: 10px; 
            font-size: 2.5em;
        }
        .location {
            color: #7f8c8d;
            font-size: 1.2em;
        }
        .admin-badge {
            background: #e74c3c;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 10px;
            display: inline-block;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            border: 2px solid #e9ecef;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .voucher-table { 
            width: 100%; 
            margin-top: 15px; 
        }
        .voucher-table table { 
            width: 100%; 
            border-collapse: collapse; 
        }
        .voucher-table th, .voucher-table td { 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid #ddd; 
        }
        .voucher-table th { 
            background: #f8f9fa; 
            font-weight: bold; 
        }
        .voucher-table tr:hover { 
            background: #f5f5f5; 
        }
        
        /* Full-width voucher management styling */
        .voucher-management-full {
            width: 100%;
            margin: 20px 0;
            box-sizing: border-box;
        }
        .voucher-management-full .voucher-table {
            width: 100%;
            overflow-x: auto;
        }
        .card h3 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #dee2e6;
        }
        .stat-item:last-child {
            border-bottom: none;
        }
        .stat-label {
            font-weight: bold;
            color: #495057;
        }
        .stat-value {
            color: #28a745;
            font-weight: bold;
        }
        .btn {
            padding: 12px 25px;
            margin: 5px;
            border: none;
            border-radius: 6px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: #3498db;
            color: white;
        }
        .btn-primary:hover {
            background: #2980b9;
            transform: translateY(-2px);
        }
        .btn-success {
            background: #27ae60;
            color: white;
        }
        .btn-success:hover {
            background: #229954;
            transform: translateY(-2px);
        }
        .btn-warning {
            background: #f39c12;
            color: white;
        }
        .btn-warning:hover {
            background: #e67e22;
            transform: translateY(-2px);
        }
        .btn-danger {
            background: #e74c3c;
            color: white;
        }
        .btn-danger:hover {
            background: #c0392b;
            transform: translateY(-2px);
        }
        .btn-info {
            background: #17a2b8;
            color: white;
        }
        .btn-info:hover {
            background: #138496;
            transform: translateY(-2px);
        }
        .result { 
            margin-top: 15px; 
            padding: 15px; 
            border-radius: 6px; 
            font-size: 1.1em;
        }
        .success { 
            background: #d4edda; 
            color: #155724; 
            border: 1px solid #c3e6cb; 
        }
        .error { 
            background: #f8d7da; 
            color: #721c24; 
            border: 1px solid #f5c6cb; 
        }
        .warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 15px; 
        }
        th, td { 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid #dee2e6; 
        }
        th { 
            background: #f8f9fa; 
            font-weight: bold;
            color: #495057;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .voucher-code {
            font-family: monospace;
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 3px;
        }
        .status-created {
            color: #28a745;
            font-weight: bold;
        }
        .status-redeemed {
            color: #dc3545;
            font-weight: bold;
        }
        .employee-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .employee-item {
            padding: 10px;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            margin-bottom: 10px;
            background: white;
        }
        .employee-name {
            font-weight: bold;
            color: #2c3e50;
        }
        .employee-phone {
            color: #6c757d;
            font-size: 0.9em;
        }
        .birthday-badge {
            background: #ff6b6b;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{cafe_name}} Admin Panel</h1>
            <p class="location">📍 {{cafe_location}}</p>
            <div class="admin-badge">🔐 ADMINISTRATOR ACCESS</div>
        </div>
        
        <!-- First Row: System Statistics and Employee Management -->
        <div class="dashboard">
            <div class="card">
                <h3>📊 System Statistics</h3>
                <div class="stat-item">
                    <span class="stat-label">Total Employees:</span>
                    <span class="stat-value" id="totalEmployees">-</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Active Vouchers:</span>
                    <span class="stat-value" id="activeVouchers">-</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Total Redeemed:</span>
                    <span class="stat-value" id="totalRedeemed">-</span>
                </div>
                <button class="btn btn-info" onclick="loadStatus()">🔄 Refresh Stats</button>
            </div>
            
            <div class="card">
                <h3>👥 Employee Management</h3>
                <div id="employeeList" class="employee-list">
                    <p>Loading employees...</p>
                </div>
                <button class="btn btn-primary" onclick="loadEmployees()">🔄 Refresh Employees</button>
            </div>
        </div>
        
        <!-- Second Row: Voucher Management (Full Width) -->
        <div class="card voucher-management-full">
            <h3>🎫 Voucher Management</h3>
            <div id="voucherStats">
                <p>Loading voucher statistics...</p>
            </div>
            <button class="btn btn-warning" onclick="loadVouchers()">🔄 Refresh Vouchers</button>
        </div>
        
        <div class="card">
            <h3>📋 Voucher History</h3>
            <button class="btn btn-info" onclick="loadHistory()">🔄 Load History</button>
            <div id="historyResult"></div>
        </div>
        
        <div class="card">
            <h3>🔧 System Actions</h3>
            <button class="btn btn-primary" onclick="window.open('/', '_blank')">🏪 Open Cafe Interface</button>
            <button class="btn btn-warning" onclick="clearHistory()">🗑️ Clear History</button>
            <div id="systemResult" class="result" style="display: none;"></div>
        </div>
    </div>

    <script>
        function loadStatus() {
            fetch('/status')
            .then(res => res.json())
            .then(data => {
                document.getElementById('totalEmployees').textContent = data.employees_count;
                document.getElementById('activeVouchers').textContent = data.vouchers_count;
                document.getElementById('totalRedeemed').textContent = data.redeemed_count || 0;
            })
            .catch(error => {
                console.error('Error loading status:', error);
            });
        }
        
        function loadEmployees() {
            fetch('/employees')
            .then(res => res.json())
            .then(data => {
                let html = '';
                data.employees.forEach(emp => {
                    html += `
                        <div class="employee-item">
                            <div class="employee-name">${emp.employee_name}</div>
                            <div class="employee-phone">📞 ${emp.phone_number}</div>
                            <div class="employee-phone">🆔 ${emp.employee_id}</div>
                        </div>
                    `;
                });
                document.getElementById('employeeList').innerHTML = html;
            })
            .catch(error => {
                document.getElementById('employeeList').innerHTML = '<p>Error loading employees</p>';
            });
        }
        
        function loadVouchers() {
            fetch('/vouchers')
            .then(res => res.json())
            .then(data => {
                let html = '<div class="voucher-table"><table><tr><th>Code</th><th>Employee</th><th>Status</th><th>Created</th><th>Expires</th></tr>';
                data.vouchers.forEach(voucher => {
                    const status = voucher.redeemed ? 
                        '<span class="status-redeemed">Redeemed</span>' : 
                        '<span class="status-created">Active</span>';
                    const created = new Date(voucher.created_at).toLocaleString();
                    const expires = new Date(voucher.expires_at).toLocaleString();
                    html += `
                        <tr>
                            <td><span class="voucher-code">${voucher.code}</span></td>
                            <td>${voucher.employee_name}</td>
                            <td>${status}</td>
                            <td>${created}</td>
                            <td>${expires}</td>
                        </tr>
                    `;
                });
                html += '</table></div>';
                document.getElementById('voucherStats').innerHTML = html;
            })
            .catch(error => {
                document.getElementById('voucherStats').innerHTML = '<p>Error loading vouchers</p>';
            });
        }
        
        
        function loadHistory() {
            fetch('/history')
            .then(res => res.json())
            .then(data => {
                let html = '<table><tr><th>Time</th><th>Code</th><th>Employee</th><th>Status</th></tr>';
                data.history.forEach(record => {
                    const status = record.status === 'redeemed' ? 
                        '<span class="status-redeemed">Redeemed</span>' : 
                        '<span class="status-created">Created</span>';
                    html += `
                        <tr>
                            <td>${new Date(record.timestamp).toLocaleString()}</td>
                            <td><span class="voucher-code">${record.voucher_code}</span></td>
                            <td>${record.employee_name}</td>
                            <td>${status}</td>
                        </tr>
                    `;
                });
                html += '</table>';
                document.getElementById('historyResult').innerHTML = html;
            })
            .catch(error => {
                document.getElementById('historyResult').innerHTML = '<p>Error loading history</p>';
            });
        }
        
        function clearHistory() {
            if (confirm('Are you sure you want to clear all voucher history? This action cannot be undone.')) {
                fetch('/clear-history', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    showResult('systemResult', data.message, data.success);
                    if (data.success) {
                        loadHistory();
                        loadStatus();
                    }
                })
                .catch(error => {
                    showResult('systemResult', 'Error: ' + error.message, false);
                });
            }
        }
        
        function showResult(elementId, message, success) {
            const element = document.getElementById(elementId);
            element.textContent = message;
            element.className = 'result ' + (success ? 'success' : 'error');
            element.style.display = 'block';
        }
        
        // Load initial data
        loadStatus();
        loadEmployees();
        loadVouchers();
        loadHistory();
    </script>
</body>
</html>
"""
# =================== Login HTML template ===================
LOGIN_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - {{cafe_name}}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .login-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 25px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 450px;
            width: 100%;
            backdrop-filter: blur(10px);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2em;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header p {
            color: #7f8c8d;
            font-size: 1em;
        }
        
        .admin-badge {
            background: #e74c3c;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            margin-top: 10px;
            display: inline-block;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        label {
            display: block;
            margin-bottom: 10px;
            font-weight: 600;
            color: #495057;
            font-size: 0.95em;
        }
        
        input[type="text"], 
        input[type="password"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 15px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.8);
            box-sizing: border-box;
        }
        
        input[type="text"]:focus, 
        input[type="password"]:focus {
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
            background: white;
        }
        
        .btn {
            width: 100%;
            padding: 15px 25px;
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
        }
        
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
        }
        
        .btn:active {
            transform: translateY(-1px);
        }
        
        .error {
            background: linear-gradient(135deg, #f8d7da, #f5c6cb);
            color: #721c24;
            padding: 15px;
            border-radius: 15px;
            margin-bottom: 20px;
            display: none;
            font-weight: 600;
            text-align: center;
            border: 1px solid #f5c6cb;
        }
        
        .error.show {
            display: block;
        }
        
        .success {
            background: linear-gradient(135deg, #d4edda, #c3e6cb);
            color: #155724;
            padding: 15px;
            border-radius: 15px;
            margin-bottom: 20px;
            display: none;
            font-weight: 600;
            text-align: center;
            border: 1px solid #c3e6cb;
        }
        
        .success.show {
            display: block;
        }
        
        @media (max-width: 480px) {
            .login-container {
                padding: 30px 20px;
                border-radius: 20px;
            }
            
            .header h1 {
                font-size: 1.5em;
            }
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="header">
            <h1>🔐 Admin Login</h1>
            <p>{{cafe_name}}</p>
            <div class="admin-badge">ADMINISTRATOR ACCESS</div>
        </div>
        
        <div class="error" id="errorMsg"></div>
        <div class="success" id="successMsg"></div>
        
        <form id="loginForm" method="POST" action="/login">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required autocomplete="username" placeholder="Enter your username">
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required autocomplete="current-password" placeholder="Enter your password">
            </div>
            
            <button type="submit" class="btn">Login</button>
        </form>
    </div>
    
    <script>
        // Handle form submission
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            const errorMsg = document.getElementById('errorMsg');
            const successMsg = document.getElementById('successMsg');
            
            // Hide previous messages
            errorMsg.classList.remove('show');
            successMsg.classList.remove('show');
            
            // Validate inputs
            if (!username || !password) {
                errorMsg.textContent = 'Please enter both username and password';
                errorMsg.classList.add('show');
                return;
            }
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    successMsg.textContent = 'Login successful! Redirecting...';
                    successMsg.classList.add('show');
                    
                    // Redirect after short delay - use redirect URL from response or default to /
                    const redirectUrl = data.redirect || '/';
                    setTimeout(() => {
                        window.location.href = redirectUrl;
                    }, 500);
                } else {
                    errorMsg.textContent = data.message || 'Login failed. Please check your credentials.';
                    errorMsg.classList.add('show');
                }
            } catch (error) {
                errorMsg.textContent = 'Error connecting to server: ' + error.message;
                errorMsg.classList.add('show');
                console.error('Login error:', error);
            }
        });
        
        // Clear error message when user starts typing
        document.getElementById('username').addEventListener('input', function() {
            document.getElementById('errorMsg').classList.remove('show');
        });
        
        document.getElementById('password').addEventListener('input', function() {
            document.getElementById('errorMsg').classList.remove('show');
        });
    </script>
</body>
</html>
"""


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def admin_login():
    """Admin login"""
    # If already logged in and admin, go to admin dashboard
    if current_user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        # Handle both JSON and form data
        if request.is_json:
            data = request.json
        else:
            data = request.form
        
        username = sanitize_input(data.get('username', ''))
        password = data.get('password', '')
        
        if not username or not password:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Username and password required'}), 400
            else:
                # For form submissions, show error on page
                return render_template_string(
                    LOGIN_HTML_TEMPLATE.replace(
                        '<div class="error" id="errorMsg"></div>',
                        '<div class="error show" id="errorMsg">Username and password required</div>'
                    ), 
                    cafe_name=Config.CAFE_NAME
                )
        
        user = authenticate_user(username, password)
        if user:
            if user.role != 'admin':
                error_msg = 'Admin access required'
                if request.is_json:
                    return jsonify({'success': False, 'message': error_msg}), 403
                else:
                    return render_template_string(
                        LOGIN_HTML_TEMPLATE.replace(
                            '<div class="error" id="errorMsg"></div>',
                            f'<div class="error show" id="errorMsg">{error_msg}</div>'
                        ), 
                        cafe_name=Config.CAFE_NAME
                    )
            
            login_user(user)
            
            # Generate JWT token for API access
            token = generate_jwt_token(user)
            
            # Get next URL from Flask-Login or default to /
            next_url = request.args.get('next')
            if not next_url or not next_url.startswith('/'):
                next_url = '/'
            
            # If it's a form submission, redirect
            if not request.is_json:
                return redirect(next_url)
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'token': token,
                'redirect': next_url,
                'user': {
                    'username': user.username,
                    'role': user.role,
                    'full_name': user.full_name
                }
            })
        
        error_msg = 'Invalid username or password'
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg}), 401
        else:
            return render_template_string(
                LOGIN_HTML_TEMPLATE.replace(
                    '<div class="error" id="errorMsg"></div>',
                    f'<div class="error show" id="errorMsg">{error_msg}</div>'
                ), 
                cafe_name=Config.CAFE_NAME
            )
    
    # GET request - show login page
    return render_template_string(LOGIN_HTML_TEMPLATE, cafe_name=Config.CAFE_NAME)


@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    return redirect('/login')


@app.route('/api/token', methods=['POST'])
@limiter.limit("10 per minute")
def get_api_token():
    """Get JWT token for API access"""
    data = request.json if request.is_json else request.form
    username = sanitize_input(data.get('username', ''))
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400
    
    user = authenticate_user(username, password)
    if user:
        token = generate_jwt_token(user)
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'username': user.username,
                'role': user.role
            }
        })
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard"""
    generate_csrf_token()  # Generate CSRF token for forms
    return render_template_string(ADMIN_HTML_TEMPLATE, 
                                cafe_name=Config.CAFE_NAME, 
                                cafe_location=Config.CAFE_LOCATION)

@app.route('/status')
@login_required
@admin_required
@limiter.limit("30 per minute")
def status():
    """Get system status"""
    refresh_data()  # Refresh data from CSV before getting stats
    stats = get_system_stats()
    vouchers = get_all_vouchers()
    
    # Count redeemed vouchers
    redeemed_count = sum(1 for v in vouchers.values() if v['redeemed'])
    stats['redeemed_count'] = redeemed_count
    
    return jsonify(stats)

@app.route('/employees')
@login_required
@admin_required
@limiter.limit("30 per minute")
def employees():
    """Get employee list with birthday info"""
    refresh_data()  # Refresh data from CSV
    employees = load_employees()
    birthdays = get_birthday_today()
    birthday_ids = {emp['employee_id'] for emp in birthdays}
    
    for emp in employees:
        emp['is_birthday'] = emp['employee_id'] in birthday_ids
    
    return jsonify({'employees': employees})

@app.route('/vouchers')
@login_required
@admin_required
@limiter.limit("30 per minute")
def vouchers():
    """Get all vouchers"""
    refresh_data()  # Refresh data from CSV
    vouchers = get_all_vouchers()
    voucher_list = []
    
    for code, voucher in vouchers.items():
        voucher_list.append({
            'code': code,
            'employee_name': voucher['employee_name'],
            'created_at': voucher['created_at'],
            'expires_at': voucher['expires_at'],
            'redeemed': voucher['redeemed']
        })
    
    return jsonify({'vouchers': voucher_list})


@app.route('/history')
@login_required
@admin_required
@limiter.limit("30 per minute")
def history():
    """Get voucher history"""
    refresh_data()  # Refresh data from CSV before getting history
    return jsonify({'history': get_voucher_history()})

@app.route('/clear-history', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 per minute")
def clear_history():
    """Clear voucher history"""
    try:
        with open(Config.VOUCHER_HISTORY_CSV, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['timestamp', 'voucher_code', 'employee_id', 'employee_name', 'status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        
        return jsonify({
            'success': True,
            'message': 'Voucher history cleared successfully!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error clearing history: {str(e)}'
        })

@app.route('/send-birthday', methods=['POST'])
@login_required
@admin_required
@limiter.limit("10 per hour")
def send_birthday():
    """Send birthday wishes to employees with birthdays today"""
    try:
        # Check if force_new parameter is provided (for testing)
        data = request.json if request.is_json else request.form
        force_new = data.get('force_new', 'false').lower() == 'true' if data else False
        
        refresh_data()
        birthdays = get_birthday_today()
        
        if not birthdays:
            return jsonify({
                'success': False,
                'message': 'No birthdays today'
            })
        
        results = []
        for employee in birthdays:
            try:
                # Create voucher (with force_new for testing)
                voucher_code = create_voucher(
                    employee['employee_id'], 
                    employee['employee_name'],
                    force_new=force_new
                )
                
                # Generate QR code
                qr_code = generate_qr_code(voucher_code)
                
                # Send WhatsApp message
                success = send_whatsapp_message(
                    employee['phone_number'],
                    employee['employee_name'],
                    voucher_code
                )
                
                results.append({
                    'employee_name': employee['employee_name'],
                    'voucher_code': voucher_code,
                    'message_sent': success
                })
                
            except Exception as e:
                results.append({
                    'employee_name': employee['employee_name'],
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(birthdays)} birthdays',
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/regenerate-voucher', methods=['POST'])
@login_required
@admin_required
@limiter.limit("10 per hour")
def regenerate_voucher():
    """Regenerate voucher for an employee (for testing)"""
    try:
        data = request.json if request.is_json else request.form
        employee_id = sanitize_input(data.get('employee_id', ''))
        
        if not employee_id:
            return jsonify({'success': False, 'message': 'Employee ID required'}), 400
        
        refresh_data()
        employees = load_employees()
        employee = None
        for emp in employees:
            if emp['employee_id'] == employee_id:
                employee = emp
                break
        
        if not employee:
            return jsonify({'success': False, 'message': 'Employee not found'}), 404
        
        # Force create new voucher
        voucher_code = create_voucher(
            employee['employee_id'],
            employee['employee_name'],
            force_new=True
        )
        
        # Generate QR code
        qr_code = generate_qr_code(voucher_code)
        
        return jsonify({
            'success': True,
            'message': f'New voucher generated for {employee["employee_name"]}',
            'voucher_code': voucher_code,
            'employee_name': employee['employee_name']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============= MAIN =============
if __name__ == '__main__':


    try:
        print("=" * 60)
        print(f"Starting {Config.CAFE_NAME} Admin Interface...")
        print("=" * 60)
        print(f"Admin Interface: http://localhost:{Config.ADMIN_PORT}")
        print(f"Host: {Config.HOST}")
        print(f"Debug Mode: {Config.DEBUG}")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        print()
        
        # Load initial data (quietly)
        print("Loading data...")
        refresh_data()  # Refresh data from CSV
        print("✓ Data loaded")
        print()

        
        
        # Show registered routes
        with app.app_context():
            routes = list(app.url_map.iter_rules())
            print(f"Registered routes: {len(routes)}")
            if '/login' in [r.rule for r in routes]:
                print("✓ Login route is registered")
            else:
                print("✗ WARNING: Login route NOT found!")
        print()
        
        print("Starting Flask server...")
        print("=" * 60)
        print()
        
        # Start the server
        app.run(host=Config.HOST, port=Config.ADMIN_PORT, debug=Config.DEBUG)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("ERROR: Failed to start server!")
        print("=" * 60)
        print(f"Error: {e}")
        print("\nFull error details:")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        input("Press Enter to exit...")
        sys.exit(1)
