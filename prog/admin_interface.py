#!/usr/bin/env python3
"""
Admin Interface - Full System Management
Complete interface for administrators to manage the voucher system
"""
from flask import Flask, render_template_string, request, jsonify
from config import Config
from database import (
    load_employees, get_birthday_today, create_voucher, 
    redeem_voucher, generate_qr_code, get_all_vouchers,
    get_voucher_history, get_system_stats, refresh_data
)
from whatsapp_service import send_whatsapp_message
import csv

# ============= ADMIN FLASK APPLICATION =============
app = Flask(__name__)

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

@app.route('/')
def index():
    """Admin dashboard"""
    return render_template_string(ADMIN_HTML_TEMPLATE, 
                                cafe_name=Config.CAFE_NAME, 
                                cafe_location=Config.CAFE_LOCATION)

@app.route('/status')
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
def history():
    """Get voucher history"""
    refresh_data()  # Refresh data from CSV before getting history
    return jsonify({'history': get_voucher_history()})

@app.route('/clear-history', methods=['POST'])
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

# ============= MAIN =============
if __name__ == '__main__':
    print(f"Starting {Config.CAFE_NAME} Admin Interface...")
    print(f"Admin Interface: http://localhost:{Config.ADMIN_PORT}")
    print("Press Ctrl+C to stop")
    print("=" * 30)
    
    # Load initial data (quietly)
    refresh_data()  # Refresh data from CSV
    
    # Start the server
    app.run(host=Config.HOST, port=Config.ADMIN_PORT, debug=Config.DEBUG)
