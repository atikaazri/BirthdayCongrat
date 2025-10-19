"""
Cafe web UI for scanning vouchers (Flask)
Usage: python cafe_ui.py
"""
from flask import Flask, render_template_string, request, jsonify
from config import Config
from vouchers import redeem_voucher, get_all_vouchers

app = Flask(__name__)

SCANNER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{CAFE_NAME}} - Voucher Scanner</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jsQR/1.4.0/jsQR.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f0f0f0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 20px; }
        h1 { color: {{PRIMARY_COLOR}}; margin-bottom: 5px; }
        .location { color: #666; font-size: 14px; }
        .scanner-section { margin-bottom: 20px; }
        video, canvas { width: 100%; border: 2px solid #ddd; border-radius: 4px; }
        input { width: 100%; padding: 12px; font-size: 16px; border: 2px solid #ddd; border-radius: 4px; margin: 10px 0; }
        button { width: 100%; padding: 12px; background: {{PRIMARY_COLOR}}; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin-bottom: 10px; }
        button:hover { background: {{SECONDARY_COLOR}}; }
        .result { margin-top: 20px; padding: 15px; border-radius: 4px; display: none; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .result h3 { margin-bottom: 10px; }
        .result p { margin: 5px 0; font-size: 14px; }
        .info-badge { background: #e7f3ff; color: #0066cc; padding: 10px; border-radius: 4px; font-size: 13px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 {{CAFE_NAME}} - Voucher Scanner</h1>
            <p class="location">📍 {{CAFE_LOCATION}}</p>
        </div>
        
        <div class="scanner-section">
            <h3>Scan QR Code:</h3>
            <video id="video" width="100%" height="400"></video>
            <canvas id="canvas" style="display:none;"></canvas>
            <br><br>
            <button onclick="startScanning()">Start Camera</button>
            <button onclick="stopScanning()">Stop</button>
        </div>
        
        <div class="scanner-section">
            <h3>Or Enter Code Manually:</h3>
            <input type="text" id="manualCode" placeholder="Enter voucher code..." onkeypress="if(event.key==='Enter') redeemVoucher()">
            <button onclick="redeemVoucher()">Verify & Redeem</button>
        </div>
        
        <div id="result" class="result">
            <h3 id="resultTitle"></h3>
            <p id="resultMessage"></p>
            <div class="info-badge" id="resultDetails" style="display:none;"></div>
        </div>
    </div>

    <script>
        let scanning = false;
        let video = document.getElementById('video');
        let canvas = document.getElementById('canvas');
        let ctx = canvas.getContext('2d');

        function startScanning() {
            navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
                .then(stream => {
                    video.srcObject = stream;
                    scanning = true;
                    scanFrame();
                })
                .catch(err => showResult('Error', 'Cannot access camera: ' + err.message, false));
        }

        function stopScanning() {
            scanning = false;
            if (video.srcObject) {
                video.srcObject.getTracks().forEach(track => track.stop());
            }
        }

        function scanFrame() {
            if (!scanning) return;
            
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0);
            
            let imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            let code = jsQR(imageData.data, imageData.width, imageData.height);
            
            if (code) {
                document.getElementById('manualCode').value = code.data;
                redeemVoucher();
                stopScanning();
                return;
            }
            
            requestAnimationFrame(scanFrame);
        }

        function redeemVoucher() {
            let code = document.getElementById('manualCode').value.trim();
            if (!code) {
                showResult('Error', 'Please enter a voucher code', false);
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
                    let details = `Expires: ${data.expires_at || 'N/A'}`;
                    showResult('✓ Valid Voucher', `Employee: ${data.employee_name}\\n(ID: ${data.employee_id})\\n\\nVoucher redeemed successfully!`, true, details);
                    document.getElementById('manualCode').value = '';
                } else {
                    showResult('✗ Invalid Voucher', data.message, false);
                }
            });
        }

        function showResult(title, message, success, details) {
            let resultDiv = document.getElementById('result');
            document.getElementById('resultTitle').innerText = title;
            document.getElementById('resultMessage').innerText = message;
            resultDiv.className = 'result ' + (success ? 'success' : 'error');
            resultDiv.style.display = 'block';
            
            if (details) {
                document.getElementById('resultDetails').innerText = details;
                document.getElementById('resultDetails').style.display = 'block';
            } else {
                document.getElementById('resultDetails').style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    from config import Config
    
    html = SCANNER_HTML.replace('{{CAFE_NAME}}', Config.CAFE_NAME)
    html = html.replace('{{CAFE_LOCATION}}', Config.CAFE_LOCATION)
    html = html.replace('{{PRIMARY_COLOR}}', Config.BRAND_COLOR_PRIMARY)
    html = html.replace('{{SECONDARY_COLOR}}', Config.BRAND_COLOR_SECONDARY)
    html = html.replace('{{VALIDITY}}', str(Config.VOUCHER_VALIDITY_HOURS))
    
    return render_template_string(html)


@app.route('/redeem', methods=['POST'])
def redeem():
    data = request.json
    code = data.get('code', '')
    
    success, result = redeem_voucher(code)
    
    if not success:
        return jsonify({'success': False, 'message': result})
    
    return jsonify({
        'success': True,
        'employee_id': result['employee_id'],
        'employee_name': result['employee_name'],
        'redeemed_at': result['redeemed_at'],
        'expires_at': result['expires_at']
    })


@app.route('/admin/vouchers')
def admin_vouchers():
    return jsonify(get_all_vouchers())


if __name__ == '__main__':
    print(f"Starting Flask scanner at http://localhost:{Config.FLASK_PORT}")
    app.run(debug=Config.DEBUG_MODE, port=Config.FLASK_PORT)