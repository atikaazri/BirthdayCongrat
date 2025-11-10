#!/usr/bin/env python3
"""
BDVoucher - Birthday Voucher System
Main Flask application

BDVoucher - Landing Page
Simple homepage linking to the Cafe and Admin interfaces.
"""
from flask import Flask, render_template_string, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from database import (
    load_employees, get_birthday_today, create_voucher, 
    redeem_voucher, generate_qr_code, get_all_vouchers,
    get_voucher_history, get_system_stats, refresh_data
)
from whatsapp_service import send_whatsapp_message
from auto_messaging import start_auto_messaging, stop_auto_messaging, test_auto_messaging
from security_helpers import (
    validate_voucher_code, sanitize_input,
    add_security_headers
)
import os



# ============= FLASK APPLICATION =============
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-this-secret-key-in-production-12345')


# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Add security headers to all responses
@app.after_request
def set_security_headers(response):
    return add_security_headers(response)

# Simple HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{cafe_name}} - Voucher System</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        h1 { color: #4CAF50; margin-bottom: 5px; }
        .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        input, button { padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #4CAF50; color: white; cursor: pointer; }
        button:hover { background: #45a049; }
        .result { margin-top: 15px; padding: 10px; border-radius: 4px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .voucher { background: #e7f3ff; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .qr-code { text-align: center; margin: 10px 0; }
        .qr-code img { max-width: 200px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f2f2f2; }
        .nav-links { margin-top: 15px; }
        .nav-link { 
            display: inline-block; 
            margin: 0 10px; 
            padding: 8px 16px; 
            background: #007bff; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px; 
            font-size: 14px;
        }
        .nav-link:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 {{cafe_name}} - Voucher System</h1>
            <p>📍 {{cafe_location}}</p>
            
            <div class="nav-links">
                <a href="http://localhost:5001/login" target="_blank" class="nav-link">🏪 Cafe Login</a>
                <a href="http://localhost:5002/login" target="_blank" class="nav-link">⚙️ Admin Login</a>
            </div>

        </div>
        
        <div class="section">
            <h3>📱 Voucher Scanner</h3>
            <div style="margin-bottom: 15px;">
                <button onclick="startCamera()" id="cameraBtn">📷 Start Camera</button>
                <button onclick="stopCamera()" id="stopBtn" style="display: none;">⏹️ Stop Camera</button>
            </div>
            <video id="video" width="100%" height="300" style="display: none; border: 2px solid #ddd; border-radius: 5px;"></video>
            <canvas id="canvas" style="display: none;"></canvas>
            <div style="margin: 15px 0;">
                <input type="text" id="voucherCode" placeholder="Or enter voucher code manually..." style="width: 300px;">
                <button onclick="redeemVoucher()">Redeem Voucher</button>
            </div>
            <div id="redeemResult" class="result" style="display: none;"></div>
        </div>
        
        
        <div class="section">
            <h3>📊 System Status</h3>
            <button onclick="loadStatus()">Refresh Status</button>
            <div id="statusResult"></div>
        </div>
        
        <div class="section">
            <h3>📋 Voucher History</h3>
            <button onclick="loadHistory()">Load History</button>
            <div id="historyResult"></div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/jsQR/1.4.0/jsQR.min.js"></script>
    <script>
        let video = document.getElementById('video');
        let canvas = document.getElementById('canvas');
        let ctx = canvas.getContext('2d');
        let scanning = false;
        let stream = null;

        function startCamera() {
            navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'environment',
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                } 
            })
            .then(function(mediaStream) {
                stream = mediaStream;
                video.srcObject = stream;
                video.style.display = 'block';
                document.getElementById('cameraBtn').style.display = 'none';
                document.getElementById('stopBtn').style.display = 'inline-block';
                scanning = true;
                scanQRCode();
            })
            .catch(function(err) {
                console.error('Camera access error:', err);
                showResult('redeemResult', 'Camera access denied or not available', false);
            });
        }

        function stopCamera() {
            scanning = false;
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                stream = null;
            }
            video.style.display = 'none';
            document.getElementById('cameraBtn').style.display = 'inline-block';
            document.getElementById('stopBtn').style.display = 'none';
        }

        function scanQRCode() {
            if (!scanning) return;
            
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const code = jsQR(imageData.data, imageData.width, imageData.height);
                
                if (code) {
                    console.log('QR Code detected:', code.data);
                    document.getElementById('voucherCode').value = code.data;
                    stopCamera();
                    redeemVoucher();
                    return;
                }
            }
            
            requestAnimationFrame(scanQRCode);
        }

        function redeemVoucher() {
            const code = document.getElementById('voucherCode').value.trim();
            if (!code) {
                showResult('redeemResult', 'Please enter a voucher code', false);
                return;
            }
            
            fetch('/redeem', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showResult('redeemResult', `Voucher redeemed for: ${data.employee_name}`, true);
                    document.getElementById('voucherCode').value = '';
                } else {
                    showResult('redeemResult', data.message, false);
                }
            })
            .catch(error => {
                showResult('redeemResult', 'Error: ' + error.message, false);
            });
        }
        
        
        function loadStatus() {
            fetch('/status')
            .then(res => res.json())
            .then(data => {
                document.getElementById('statusResult').innerHTML = `
                    <p><strong>Employees:</strong> ${data.employees_count}</p>
                    <p><strong>Birthdays Today:</strong> ${data.birthdays_count}</p>
                    <p><strong>Active Vouchers:</strong> ${data.vouchers_count}</p>
                    <p><strong>Messaging Service:</strong> ${data.messaging_service}</p>
                `;
            });
        }
        
        function loadHistory() {
            fetch('/history')
            .then(res => res.json())
            .then(data => {
                let html = '<table><tr><th>Time</th><th>Code</th><th>Employee</th><th>Status</th></tr>';
                data.history.forEach(record => {
                    html += `<tr>
                        <td>${new Date(record.timestamp).toLocaleString()}</td>
                        <td>${record.voucher_code}</td>
                        <td>${record.employee_name}</td>
                        <td>${record.status}</td>
                    </tr>`;
                });
                html += '</table>';
                document.getElementById('historyResult').innerHTML = html;
            });
        }
        
        function showResult(elementId, message, success) {
            const element = document.getElementById(elementId);
            element.textContent = message;
            element.className = 'result ' + (success ? 'success' : 'error');
            element.style.display = 'block';
        }
        
        // Load initial data
        loadStatus();
    </script>
</body>
</html>
"""

# ============= ROUTE =============

@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE, 
                                cafe_name=Config.CAFE_NAME, 
                                cafe_location=Config.CAFE_LOCATION)

@app.route('/redeem', methods=['POST'])
@limiter.limit("20 per minute")
def redeem():
    """Redeem a voucher"""
    # Validate JSON request
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Content-Type must be application/json'}), 400
    
    data = request.json
    code = sanitize_input(data.get('code', ''))
    
    # Validate voucher code format
    is_valid, message = validate_voucher_code(code)
    if not is_valid:
        return jsonify({'success': False, 'message': message}), 400
    
    success, result = redeem_voucher(code)
    
    if success:
        return jsonify({
            'success': True,
            'employee_name': result['employee_name'],
            'message': 'Voucher redeemed successfully!'
        })
    else:
        return jsonify({
            'success': False,
            'message': result
        }), 400


@app.route('/status')
@limiter.limit("30 per minute")
def status():
    """Get system status"""
    refresh_data()  # Refresh data from CSV before getting stats
    return jsonify(get_system_stats())

@app.route('/history')
@limiter.limit("30 per minute")
def history():
    """Get voucher history"""
    refresh_data()  # Refresh data from CSV before getting history
    return jsonify({'history': get_voucher_history()})

@app.route('/send-birthday', methods=['POST'])
@limiter.limit("10 per hour")
def send_birthday():
    """Send birthday wishes to employees with birthdays today"""
    try:
        birthdays = get_birthday_today()
        
        if not birthdays:
            return jsonify({
                'success': False,
                'message': 'No birthdays today'
            })
        
        results = []
        for employee in birthdays:
            try:
                # Create voucher
                voucher_code = create_voucher(employee['employee_id'], employee['employee_name'])
                
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

@app.route('/test-auto-messaging', methods=['POST'])
@limiter.limit("5 per hour")
def test_auto_messaging_endpoint():
    """Test automatic messaging system"""
    try:
        test_auto_messaging()
        return jsonify({
            'success': True,
            'message': 'Automatic messaging test completed'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Test failed: {str(e)}'
        })

# ============= MAIN =============
if __name__ == '__main__':
    print(f"Starting {Config.CAFE_NAME} Voucher System...")
    print(f"Web Interface: http://localhost:{Config.PORT}")
    print("Press Ctrl+C to stop")
    print("=" * 30)
    
    # Load initial data (quietly)
    refresh_data()  # Refresh data from CSV
    
    # Start automatic messaging scheduler
    if Config.AUTO_MESSAGING_ENABLED:
        print(f"Starting automatic messaging at {Config.AUTO_MESSAGING_TIME} {Config.AUTO_MESSAGING_TIMEZONE}")
        start_auto_messaging()
    else:
        print("Automatic messaging is disabled")
    
    try:
        # Start the server
        app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_auto_messaging()
        print("System stopped.")