#!/usr/bin/env python3
"""
Cafe Interface for BDVoucher - Fixed Camera & Auto-Redemption
Camera opens properly, automatic validation, full-screen results
"""
from flask import Flask, render_template_string, request, jsonify
from config import Config
from database import redeem_voucher
import cv2
import threading
import time
import os
import numpy as np
from pyzbar.pyzbar import decode
from werkzeug.utils import secure_filename
import base64
from io import BytesIO

app = Flask(__name__)

# Global variables for camera
camera = None
scanner_active = False
scanner_result = None
scanner_error = None

# Allowed file extensions for image upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

CAFE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{cafe_name}} - Voucher Redemption</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 600px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #2c3e50;
            margin: 0;
            font-size: 2.5em;
        }
        .location {
            color: #7f8c8d;
            margin: 5px 0;
        }
        .section {
            margin: 25px 0;
            padding: 20px;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            background: #f8f9fa;
        }
        .section h3 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #2980b9;
        }
        .btn-danger {
            background: #e74c3c;
        }
        .btn-danger:hover {
            background: #c0392b;
        }
        .btn-success {
            background: #27ae60;
        }
        .btn-success:hover {
            background: #229954;
        }
        .btn-warning {
            background: #f39c12;
        }
        .btn-warning:hover {
            background: #e67e22;
        }
        .input-group {
            display: flex;
            gap: 10px;
            margin: 15px 0;
        }
        .input-group input {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 16px;
        }
        .file-input {
            margin: 15px 0;
        }
        .file-input input[type="file"] {
            width: 100%;
            padding: 10px;
            border: 2px dashed #ddd;
            border-radius: 6px;
            background: #f8f9fa;
        }
        .result {
            margin: 15px 0;
            padding: 15px;
            border-radius: 6px;
            font-weight: bold;
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
        .info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        .scanner-status {
            text-align: center;
            color: #007bff;
            font-weight: bold;
            margin: 10px 0;
            padding: 10px;
            background: #e3f2fd;
            border-radius: 5px;
        }
        .camera-window {
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border: 2px solid #e9ecef;
        }
        .camera-window h4 {
            margin: 0 0 10px 0;
            color: #2c3e50;
        }
        .upload-area {
            border: 2px dashed #ddd;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            background: #f8f9fa;
            margin: 15px 0;
        }
        .upload-area.dragover {
            border-color: #3498db;
            background: #e3f2fd;
        }
        .countdown {
            font-size: 18px;
            font-weight: bold;
            color: #e74c3c;
        }
        
        /* Full-screen result overlay */
        .result-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .result-modal {
            background: white;
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            max-width: 500px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        .result-modal h2 {
            margin: 0 0 20px 0;
            font-size: 2em;
        }
        .result-modal .message {
            font-size: 1.2em;
            margin: 20px 0;
            padding: 20px;
            border-radius: 10px;
        }
        .result-modal .btn {
            margin: 10px;
            padding: 15px 30px;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{cafe_name}}</h1>
            <p class="location">📍 {{cafe_location}}</p>
            <h2>🎫 Voucher Redemption</h2>
        </div>
        
        <div class="section">
            <h3>📷 Camera Scanning</h3>
            <div style="text-align: center;">
                <button class="btn btn-success" onclick="startCameraScan()" id="cameraBtn">📷 Start Camera Scan</button>
                <button class="btn btn-danger" onclick="stopCameraScan()" id="stopCameraBtn" style="display: none; margin-left: 10px;">🛑 Stop Camera</button>
            </div>
            <div class="camera-window" id="cameraWindow" style="display: none;">
                <h4>📷 Camera Window</h4>
                <div class="countdown" id="countdown" style="display: none;"></div>
            </div>
            <div class="scanner-status" id="cameraStatus" style="display: none;">
                🔍 Camera scanning... Check camera window for live feed
            </div>
        </div>
        
        <div class="section">
            <h3>📁 Image Upload</h3>
            <div class="upload-area" id="uploadArea">
                <p>📁 Drag and drop QR code image here or click to select</p>
                <input type="file" id="imageInput" accept="image/*" style="display: none;" onchange="handleImageUpload(this)">
                <button class="btn btn-warning" onclick="document.getElementById('imageInput').click()">📁 Select Image</button>
            </div>
            <div id="imagePreview" style="display: none; text-align: center; margin: 15px 0;">
                <img id="previewImg" style="max-width: 200px; max-height: 200px; border: 2px solid #ddd; border-radius: 5px;">
                <br>
                <button class="btn" onclick="scanUploadedImage()" style="margin-top: 10px;">🔍 Scan This Image</button>
            </div>
        </div>
        
        <div class="section">
            <h3>⌨️ Manual Entry</h3>
            <div class="input-group">
                <input type="text" id="voucherCode" placeholder="Enter voucher code manually..." autocomplete="off">
                <button class="btn" onclick="redeemVoucher()">Redeem Voucher</button>
            </div>
        </div>
        
        <div id="result" class="result" style="display: none;"></div>
    </div>

    <!-- Full-screen result overlay -->
    <div class="result-overlay" id="resultOverlay">
        <div class="result-modal">
            <h2 id="resultTitle">Processing...</h2>
            <div class="message" id="resultMessage">Please wait...</div>
            <button class="btn btn-success" onclick="hideResult()" id="backBtn" style="display: none;">Go Back</button>
        </div>
    </div>

    <script>
        let scanning = false;
        let uploadedImage = null;
        let countdownTimer = null;

        // Drag and drop functionality
        const uploadArea = document.getElementById('uploadArea');
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleImageUpload({ files: files });
            }
        });

        function handleImageUpload(input) {
            const file = input.files[0];
            if (file && file.type.startsWith('image/')) {
                uploadedImage = file;
                
                // Show preview
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('previewImg').src = e.target.result;
                    document.getElementById('imagePreview').style.display = 'block';
                };
                reader.readAsDataURL(file);
                
                showResult('Image uploaded successfully! Click "Scan This Image" to process.', 'info');
            } else {
                showResult('Please select a valid image file.', 'error');
            }
        }

        function scanUploadedImage() {
            if (!uploadedImage) {
                showResult('Please upload an image first.', 'error');
                return;
            }
            
            showFullScreenResult('Processing...', 'Scanning uploaded image...', 'info');
            
            const formData = new FormData();
            formData.append('image', uploadedImage);
            
            fetch('/scan-image', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // Automatically validate the voucher
                    validateVoucher(data.code);
                } else {
                    showFullScreenResult('Error', 'No QR code found in image: ' + data.message, 'error');
                    // Auto-clear form after image scan error
                    setTimeout(() => {
                        clearForm();
                    }, 3000);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showFullScreenResult('Error', 'Error scanning image. Please try again.', 'error');
                // Auto-clear form after network error
                setTimeout(() => {
                    clearForm();
                }, 3000);
            });
        }

        function startCameraScan() {
            if (scanning) return;
            
            showFullScreenResult('Starting Camera...', 'Opening camera window...', 'info');
            
            fetch('/start-camera-scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    scanning = true;
                    document.getElementById('cameraBtn').style.display = 'none';
                    document.getElementById('stopCameraBtn').style.display = 'inline-block';
                    document.getElementById('cameraWindow').style.display = 'block';
                    document.getElementById('cameraStatus').style.display = 'block';
                    document.getElementById('countdown').style.display = 'block';
                    hideResult();
                    showResult('Camera scan started! OpenCV window opened. Point camera at QR code.', 'info');
                    
                    // Start countdown
                    startCountdown(30);
                    
                    // Start polling for results
                    pollCameraScan();
                } else {
                    showFullScreenResult('Error', 'Failed to start camera scan: ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showFullScreenResult('Error', 'Error starting camera scan. Please try again.', 'error');
            });
        }

        function startCountdown(seconds) {
            let timeLeft = seconds;
            const countdownElement = document.getElementById('countdown');
            
            countdownTimer = setInterval(() => {
                // Check if scanning is still active
                if (!scanning) {
                    clearInterval(countdownTimer);
                    countdownTimer = null;
                    return;
                }
                
                countdownElement.textContent = `Auto-close in: ${timeLeft} seconds`;
                timeLeft--;
                
                if (timeLeft < 0) {
                    clearInterval(countdownTimer);
                    countdownTimer = null;
                    stopCameraScan();
                }
            }, 1000);
        }


        function stopCameraScan() {
            if (!scanning) return;
            
            // Clear countdown timer immediately
            if (countdownTimer) {
                clearInterval(countdownTimer);
                countdownTimer = null;
            }
            
            // Stop scanning immediately
            scanning = false;
            
            fetch('/stop-camera-scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('cameraBtn').style.display = 'inline-block';
                document.getElementById('stopCameraBtn').style.display = 'none';
                document.getElementById('cameraWindow').style.display = 'none';
                document.getElementById('cameraStatus').style.display = 'none';
                document.getElementById('countdown').style.display = 'none';
                showResult('Camera scan stopped.', 'info');
                // Clear form when camera scan stops
                setTimeout(() => {
                    clearForm();
                }, 1000);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }

        function pollCameraScan() {
            if (!scanning) {
                console.log('Polling stopped - scanning is false');
                return;
            }
            
            fetch('/check-camera-scan')
            .then(res => res.json())
            .then(data => {
                console.log('Camera scan check result:', data);
                
                if (data.detected) {
                    // QR code detected - automatically validate
                    console.log('QR code detected:', data.result);
                    stopCameraScan();
                    validateVoucher(data.result);
                } else if (data.error) {
                    console.log('Camera scan error:', data.error);
                    showFullScreenResult('Error', 'Camera scan error: ' + data.error, 'error');
                    stopCameraScan();
                } else if (data.active) {
                    // Continue polling
                    setTimeout(pollCameraScan, 1000);
                } else {
                    // Scanner is not active, stop polling and revert interface
                    console.log('Scanner not active, stopping polling');
                    scanning = false;
                    // Revert interface to original state
                    document.getElementById('cameraBtn').style.display = 'inline-block';
                    document.getElementById('stopCameraBtn').style.display = 'none';
                    document.getElementById('cameraWindow').style.display = 'none';
                    document.getElementById('cameraStatus').style.display = 'none';
                    document.getElementById('countdown').style.display = 'none';
                    showResult('Camera scan completed.', 'info');
                    // Clear form after timeout
                    setTimeout(() => {
                        clearForm();
                    }, 2000);
                }
            })
            .catch(error => {
                console.error('Polling error:', error);
                if (scanning) {
                    setTimeout(pollCameraScan, 1000);
                }
            });
        }

        function validateVoucher(code) {
            showFullScreenResult('Validating...', 'Processing voucher...', 'info');
            
            fetch('/redeem', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showFullScreenResult('Success!', `Voucher redeemed successfully for: ${data.employee_name}`, 'success');
                } else {
                    showFullScreenResult('Error', data.message, 'error');
                    // Auto-clear form after error too (for expired/already redeemed cases)
                    setTimeout(() => {
                        clearForm();
                    }, 3000); // Clear after 3 seconds for errors
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showFullScreenResult('Error', 'Error validating voucher. Please try again.', 'error');
                // Auto-clear form after network errors
                setTimeout(() => {
                    clearForm();
                }, 3000);
            });
        }

        function redeemVoucher() {
            const code = document.getElementById('voucherCode').value.trim();
            if (!code) {
                showResult('Please enter a voucher code', 'error');
                return;
            }
            
            validateVoucher(code);
        }

        function clearForm() {
            // Clear manual entry field
            document.getElementById('voucherCode').value = '';
            
            // Clear uploaded image
            uploadedImage = null;
            document.getElementById('imageInput').value = '';
            document.getElementById('imagePreview').style.display = 'none';
            document.getElementById('previewImg').src = '';
            
            // Clear any result messages
            document.getElementById('result').style.display = 'none';
        }

        function showFullScreenResult(title, message, type) {
            document.getElementById('resultTitle').textContent = title;
            document.getElementById('resultMessage').textContent = message;
            document.getElementById('resultMessage').className = 'message ' + type;
            document.getElementById('resultOverlay').style.display = 'flex';
            document.getElementById('backBtn').style.display = 'inline-block';
            
            // Auto-clear form after showing result (except for errors that might need retry)
            if (type === 'success') {
                setTimeout(() => {
                    clearForm();
                }, 2000); // Clear after 2 seconds for success
            }
        }

        function hideResult() {
            document.getElementById('resultOverlay').style.display = 'none';
            // Clear form when hiding result
            clearForm();
        }

        function showResult(message, type) {
            const element = document.getElementById('result');
            element.textContent = message;
            element.className = 'result ' + type;
            element.style.display = 'block';
        }

        // Allow Enter key to redeem voucher
        document.getElementById('voucherCode').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                redeemVoucher();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Cafe redemption page"""
    return render_template_string(CAFE_HTML_TEMPLATE, 
                                cafe_name=Config.CAFE_NAME, 
                                cafe_location=Config.CAFE_LOCATION)


@app.route('/start-camera-scan', methods=['POST'])
def start_camera_scan():
    """Start the camera scan"""
    global camera, scanner_active, scanner_result, scanner_error
    
    if scanner_active:
        return jsonify({'success': False, 'message': 'Camera scan already running'})
    
    try:
        scanner_active = True
        scanner_result = None
        scanner_error = None
        
        # Start camera scan in a separate thread
        scanner_thread = threading.Thread(target=camera_scan_thread, name="CameraScanThread")
        scanner_thread.daemon = False
        scanner_thread.start()
        
        return jsonify({'success': True, 'message': 'Camera scan started'})
    except Exception as e:
        scanner_active = False
        return jsonify({'success': False, 'message': str(e)})

@app.route('/stop-camera-scan', methods=['POST'])
def stop_camera_scan():
    """Stop the camera scan"""
    global camera, scanner_active, scanner_result, scanner_error
    
    print("[DEBUG] Stopping camera scan...")
    scanner_active = False
    scanner_result = None
    scanner_error = None
    
    if camera:
        camera.release()
        camera = None
    
    return jsonify({'success': True, 'message': 'Camera scan stopped'})

@app.route('/check-camera-scan')
def check_camera_scan():
    """Check camera scan status and return any detected codes"""
    global scanner_active, scanner_result, scanner_error
    
    if scanner_error:
        return jsonify({
            'active': False,
            'detected': False,
            'error': scanner_error
        })
    
    if scanner_result:
        result = scanner_result
        scanner_result = None  # Clear the result
        return jsonify({
            'active': False,
            'detected': True,
            'result': result
        })
    
    return jsonify({
        'active': scanner_active,
        'detected': False
    })

@app.route('/scan-image', methods=['POST'])
def scan_image():
    """Scan QR code from uploaded image"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image file provided'})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No image file selected'})
        
        if file and allowed_file(file.filename):
            # Read the image
            image_data = file.read()
            
            # Convert to OpenCV format
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return jsonify({'success': False, 'message': 'Could not read image'})
            
            # Scan for QR codes
            decoded_objects = decode(image)
            if decoded_objects:
                for obj in decoded_objects:
                    qr_data = obj.data.decode("utf-8")
                    # Check if it's a valid voucher code
                    if qr_data.startswith('BDV') or (len(qr_data) >= 8 and qr_data.isalnum()):
                        return jsonify({'success': True, 'code': qr_data})
                
                # If we found QR codes but none were valid vouchers
                return jsonify({'success': False, 'message': 'QR code found but not a valid voucher'})
            else:
                return jsonify({'success': False, 'message': 'No QR code found in image'})
        else:
            return jsonify({'success': False, 'message': 'Invalid file type'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error scanning image: {str(e)}'})

def camera_scan_thread():
    """Camera scan thread - simplified and clean"""
    global camera, scanner_active, scanner_result, scanner_error
    
    try:
        # Open camera
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not camera.isOpened():
            camera = cv2.VideoCapture(0)
        
        if not camera.isOpened():
            scanner_error = "Could not access camera"
            scanner_active = False
            return

        detected = set()
        start_time = time.time()
        timeout = 30.0  # Auto-close after 30 seconds
        
        while scanner_active:
            current_time = time.time()
            
            # Check timeout
            if current_time - start_time >= timeout:
                break
            
            ret, frame = camera.read()
            if not ret:
                break

            # Detect and decode QR codes
            decoded_objects = decode(frame)
            
            for obj in decoded_objects:
                qr_data = obj.data.decode("utf-8")
                points = obj.polygon

                # Draw bounding box
                if len(points) > 4:
                    hull = cv2.convexHull(points)
                    points = hull

                n = len(points)
                for j in range(n):
                    pt1 = (points[j].x, points[j].y)
                    pt2 = (points[(j + 1) % n].x, points[(j + 1) % n].y)
                    cv2.line(frame, pt1, pt2, (0, 255, 0), 3)

                # Display text
                cv2.putText(frame, qr_data, (points[0].x, points[0].y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                
                if qr_data not in detected:
                    detected.add(qr_data)
                    
                    # Check if it's a valid voucher code (12 characters, alphanumeric)
                    if len(qr_data) == 12 and qr_data.isalnum():
                        scanner_result = qr_data
                        scanner_active = False
                        break

            cv2.imshow("QR Code Scanner", frame)

            # Check for 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        scanner_error = str(e)
    finally:
        scanner_active = False
        if camera:
            camera.release()
            camera = None
        cv2.destroyAllWindows()

@app.route('/redeem', methods=['POST'])
def redeem():
    """Redeem a voucher - FIXED to work properly"""
    data = request.json
    code = data.get('code', '')
    
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
        })

if __name__ == '__main__':
    print(f"Starting {Config.CAFE_NAME} Cafe Interface (Fixed Camera & Auto-Redemption)...")
    print(f"Cafe Interface: http://localhost:{Config.CAFE_PORT}")
    print("Press Ctrl+C to stop")
    print("=" * 30)
    
    # Start the server
    app.run(host=Config.HOST, port=Config.CAFE_PORT, debug=Config.DEBUG)