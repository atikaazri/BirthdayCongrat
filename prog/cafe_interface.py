#!/usr/bin/env python3
"""
Cafe Interface for BDVoucher - Improved UI with In-Page Camera
Chill birthday design, mobile compatible, auto-scan on upload
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
    <title>{{ cafe_name }} - Birthday Voucher Redemption</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
            min-height: 100vh;
            padding: 10px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 25px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            overflow: hidden;
            backdrop-filter: blur(10px);
        }
        
        .header {
            background: linear-gradient(135deg, #ff6b9d, #c44569, #f8b500);
            color: white;
            padding: 25px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '🎂';
            position: absolute;
            top: -10px;
            left: 20px;
            font-size: 3em;
            opacity: 0.3;
            animation: float 3s ease-in-out infinite;
        }
        
        .header::after {
            content: '🎈';
            position: absolute;
            top: -5px;
            right: 20px;
            font-size: 2.5em;
            opacity: 0.3;
            animation: float 3s ease-in-out infinite reverse;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        .header h1 {
            font-size: 2.2em;
            margin-bottom: 8px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            font-weight: 700;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.95;
            font-weight: 500;
        }
        
        .section {
            padding: 25px;
            border-bottom: 1px solid rgba(255, 182, 193, 0.3);
        }
        
        .section:last-child {
            border-bottom: none;
        }
        
        .section h2 {
            color: #d63384;
            margin-bottom: 20px;
            font-size: 1.6em;
            font-weight: 600;
        }
        
        .section h3 {
            color: #e91e63;
            margin-bottom: 15px;
            font-size: 1.3em;
            font-weight: 600;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #495057;
        }
        
        input[type="text"], input[type="file"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #ffc1cc;
            border-radius: 15px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.8);
        }
        
        input[type="text"]:focus, input[type="file"]:focus {
            outline: none;
            border-color: #ff6b9d;
            box-shadow: 0 0 0 3px rgba(255, 107, 157, 0.1);
            background: white;
        }
        
        .btn {
            background: linear-gradient(135deg, #ff6b9d, #c44569);
            color: white;
            border: none;
            padding: 15px 25px;
            border-radius: 15px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 5px;
            box-shadow: 0 4px 15px rgba(255, 107, 157, 0.3);
        }
        
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(255, 107, 157, 0.4);
        }
        
        .btn:active {
            transform: translateY(-1px);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ff4757, #ff3838);
            box-shadow: 0 4px 15px rgba(255, 71, 87, 0.3);
        }
        
        .btn-success {
            background: linear-gradient(135deg, #2ed573, #1e90ff);
            box-shadow: 0 4px 15px rgba(46, 213, 115, 0.3);
        }
        
        .btn-info {
            background: linear-gradient(135deg, #3742fa, #2f3542);
            box-shadow: 0 4px 15px rgba(55, 66, 250, 0.3);
        }
        
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 15px;
            font-weight: 600;
            text-align: center;
        }
        
        .result.success {
            background: linear-gradient(135deg, #d4edda, #c3e6cb);
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .result.error {
            background: linear-gradient(135deg, #f8d7da, #f5c6cb);
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .result.info {
            background: linear-gradient(135deg, #d1ecf1, #bee5eb);
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .camera-container {
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border: 2px dashed #ffc1cc;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            margin-top: 15px;
            position: relative;
        }
        
        .camera-preview {
            width: 100%;
            max-width: 400px;
            height: 300px;
            background: #000;
            border-radius: 10px;
            margin: 15px auto;
            display: none;
            position: relative;
            overflow: hidden;
        }
        
        .camera-preview video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .camera-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            border: 3px solid #ff6b9d;
            border-radius: 10px;
            pointer-events: none;
        }
        
        .countdown {
            font-size: 1.5em;
            font-weight: bold;
            color: #ff6b9d;
            margin: 10px 0;
        }
        
        .scanner-status {
            background: rgba(255, 193, 204, 0.3);
            padding: 10px;
            border-radius: 10px;
            margin-top: 10px;
            font-family: monospace;
            color: #495057;
        }
        
        .fullscreen-result {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            backdrop-filter: blur(5px);
        }
        
        .result-card {
            background: white;
            padding: 40px;
            border-radius: 25px;
            text-align: center;
            max-width: 500px;
            margin: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.3);
        }
        
        .result-card h2 {
            margin-bottom: 20px;
            font-size: 2em;
        }
        
        .result-card.success h2 {
            color: #2ed573;
        }
        
        .result-card.error h2 {
            color: #ff4757;
        }
        
        .result-card.info h2 {
            color: #3742fa;
        }
        
        .result-card p {
            font-size: 1.2em;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        
        .back-btn {
            background: linear-gradient(135deg, #ff6b9d, #c44569);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 15px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255, 107, 157, 0.3);
        }
        
        .back-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(255, 107, 157, 0.4);
        }
        
        .upload-area {
            border: 2px dashed #ffc1cc;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            background: rgba(255, 193, 204, 0.1);
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .upload-area:hover {
            border-color: #ff6b9d;
            background: rgba(255, 107, 157, 0.1);
        }
        
        .upload-area.dragover {
            border-color: #ff6b9d;
            background: rgba(255, 107, 157, 0.2);
        }
        
        @media (max-width: 768px) {
            body {
                padding: 5px;
            }
            
            .container {
                margin: 5px;
                border-radius: 20px;
            }
            
            .header {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
            
            .section {
                padding: 20px;
            }
            
            .btn {
                width: 100%;
                margin: 5px 0;
                padding: 18px 25px;
            }
            
            .camera-preview {
                height: 250px;
            }
            
            .result-card {
                margin: 10px;
                padding: 30px;
            }
        }
        
        @media (max-width: 480px) {
            .header h1 {
                font-size: 1.5em;
            }
            
            .section h2 {
                font-size: 1.4em;
            }
            
            .section h3 {
                font-size: 1.2em;
            }
            
            .camera-preview {
                height: 200px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎂 {{ cafe_name }}</h1>
            <p>📍 {{ cafe_location }}</p>
        </div>
        
        <div class="section">
            <h2>🎫 Birthday Voucher Redemption</h2>
        </div>
        
        <div class="section">
            <h3>📷 Camera Scanning</h3>
            <div style="text-align: center;">
                <button class="btn btn-success" onclick="startCameraScan()" id="cameraBtn">📷 Start Camera Scan</button>
                <button class="btn btn-danger" onclick="stopCameraScan()" id="stopCameraBtn" style="display: none;">🛑 Stop Camera</button>
            </div>
            <div class="camera-container" id="cameraContainer" style="display: none;">
                <h4>📷 Camera Preview</h4>
                <div class="camera-preview" id="cameraPreview">
                    <video id="video" autoplay muted playsinline></video>
                    <div class="camera-overlay" id="cameraOverlay" style="display: none;"></div>
                </div>
                <div class="countdown" id="countdown" style="display: none;"></div>
            </div>
            <div class="scanner-status" id="cameraStatus" style="display: none;">
                <div>Status: <span id="statusText">Starting...</span></div>
            </div>
        </div>
        
        <div class="section">
            <h3>📁 Image Upload</h3>
            <div class="upload-area" onclick="document.getElementById('imageUpload').click()">
                <div style="font-size: 3em; margin-bottom: 15px;">📸</div>
                <div style="font-size: 1.2em; margin-bottom: 10px; color: #495057;">Click to upload QR code image</div>
                <div style="color: #6c757d; font-size: 0.9em;">or drag and drop your image here</div>
            </div>
            <input type="file" id="imageUpload" accept="image/*" style="display: none;" onchange="handleImageUpload()">
        </div>
        
        <div class="section">
            <h3>⌨️ Manual Entry</h3>
            <div class="form-group">
                <label for="voucherCode">Voucher Code:</label>
                <input type="text" id="voucherCode" placeholder="Enter 12-character voucher code" maxlength="12">
            </div>
            <div style="text-align: center;">
                <button class="btn btn-success" onclick="redeemVoucher()">🎫 Redeem Voucher</button>
            </div>
        </div>
        
        <div id="result" class="result" style="display: none;"></div>
    </div>
    
    <div id="fullscreenResult" class="fullscreen-result" style="display: none;">
        <div class="result-card" id="resultCard">
            <h2 id="resultTitle"></h2>
            <p id="resultMessage"></p>
            <button class="back-btn" onclick="hideFullScreenResult()">Back to Scanner</button>
        </div>
    </div>

    <script>
        let scanning = false;
        let countdownTimer = null;
        let videoStream = null;

        function startCameraScan() {
            if (scanning) return;
            
            scanning = true;
            document.getElementById('cameraBtn').style.display = 'none';
            document.getElementById('stopCameraBtn').style.display = 'inline-block';
            document.getElementById('cameraContainer').style.display = 'block';
            document.getElementById('cameraStatus').style.display = 'block';
            document.getElementById('cameraPreview').style.display = 'block';
            
            // Start in-page camera
            startInPageCamera();
            
            // Start backend camera scan
            fetch('/start-camera-scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    startCountdown();
                    pollCameraScan();
                } else {
                    showResult('Failed to start camera scan: ' + data.message, 'error');
                    stopCameraScan();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showResult('Error starting camera scan: ' + error, 'error');
                stopCameraScan();
            });
        }

        function startInPageCamera() {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(stream => {
                    videoStream = stream;
                    const video = document.getElementById('video');
                    video.srcObject = stream;
                    document.getElementById('cameraOverlay').style.display = 'block';
                })
                .catch(error => {
                    console.error('Error accessing camera:', error);
                    showResult('Camera access denied. Please allow camera permission.', 'error');
                });
        }

        function stopCameraScan() {
            if (!scanning) return;
            
            scanning = false;
            
            // Stop in-page camera
            if (videoStream) {
                videoStream.getTracks().forEach(track => track.stop());
                videoStream = null;
            }
            
            // Clear countdown timer
            if (countdownTimer) {
                clearInterval(countdownTimer);
                countdownTimer = null;
            }
            
            // Stop backend camera
            fetch('/stop-camera-scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('cameraBtn').style.display = 'inline-block';
                document.getElementById('stopCameraBtn').style.display = 'none';
                document.getElementById('cameraContainer').style.display = 'none';
                document.getElementById('cameraStatus').style.display = 'none';
                document.getElementById('cameraPreview').style.display = 'none';
                document.getElementById('cameraOverlay').style.display = 'none';
                showResult('Camera scan stopped.', 'info');
                setTimeout(() => {
                    clearForm();
                }, 1000);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }

        function startCountdown() {
            let timeLeft = 30;
            const countdownElement = document.getElementById('countdown');
            countdownElement.style.display = 'block';
            
            countdownTimer = setInterval(() => {
                if (!scanning) {
                    clearInterval(countdownTimer);
                    return;
                }
                
                countdownElement.textContent = `Auto-close in ${timeLeft} seconds`;
                timeLeft--;
                
                if (timeLeft < 0) {
                    clearInterval(countdownTimer);
                    stopCameraScan();
                }
            }, 1000);
        }

        function pollCameraScan() {
            if (!scanning) return;
            
            fetch('/check-camera-scan')
            .then(res => res.json())
            .then(data => {
                if (data.detected) {
                    console.log('QR code detected:', data.result);
                    stopCameraScan();
                    validateVoucher(data.result);
                } else if (data.error) {
                    console.log('Camera scan error:', data.error);
                    showFullScreenResult('Error', 'Camera scan error: ' + data.error, 'error');
                    stopCameraScan();
                } else if (data.active) {
                    setTimeout(pollCameraScan, 1000);
                } else {
                    console.log('Scanner not active, stopping polling');
                    scanning = false;
                    document.getElementById('cameraBtn').style.display = 'inline-block';
                    document.getElementById('stopCameraBtn').style.display = 'none';
                    document.getElementById('cameraContainer').style.display = 'none';
                    document.getElementById('cameraStatus').style.display = 'none';
                    document.getElementById('cameraPreview').style.display = 'none';
                    showResult('Camera scan completed.', 'info');
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

        function handleImageUpload() {
            const fileInput = document.getElementById('imageUpload');
            const file = fileInput.files[0];
            
            if (!file) return;
            
            if (!file.type.startsWith('image/')) {
                showResult('Please select a valid image file.', 'error');
                return;
            }
            
            // Auto-scan the uploaded image
            scanUploadedImage();
        }

        function scanUploadedImage() {
            const fileInput = document.getElementById('imageUpload');
            const file = fileInput.files[0];
            
            if (!file) return;
            
            const formData = new FormData();
            formData.append('image', file);
            
            fetch('/scan-image', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success && data.code) {
                    validateVoucher(data.code);
                } else {
                    showResult('No QR code found in image.', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showResult('Error scanning image: ' + error, 'error');
            });
        }

        function redeemVoucher() {
            const code = document.getElementById('voucherCode').value.trim();
            
            if (!code) {
                showResult('Please enter a voucher code.', 'error');
                return;
            }
            
            if (code.length !== 12) {
                showResult('Voucher code must be 12 characters long.', 'error');
                return;
            }
            
            validateVoucher(code);
        }

        function validateVoucher(code) {
            fetch('/redeem', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showFullScreenResult('Success!', `Voucher redeemed successfully for ${data.employee_name}!`, 'success');
                    setTimeout(() => {
                        clearForm();
                    }, 2000);
                } else {
                    showFullScreenResult('Error', data.message, 'error');
                    setTimeout(() => {
                        clearForm();
                    }, 3000);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showFullScreenResult('Error', 'Network error: ' + error, 'error');
                setTimeout(() => {
                    clearForm();
                }, 3000);
            });
        }

        function showResult(message, type) {
            const resultDiv = document.getElementById('result');
            resultDiv.textContent = message;
            resultDiv.className = 'result ' + type;
            resultDiv.style.display = 'block';
            
            setTimeout(() => {
                resultDiv.style.display = 'none';
            }, 5000);
        }

        function showFullScreenResult(title, message, type) {
            document.getElementById('resultTitle').textContent = title;
            document.getElementById('resultMessage').textContent = message;
            document.getElementById('resultCard').className = 'result-card ' + type;
            document.getElementById('fullscreenResult').style.display = 'flex';
        }

        function hideFullScreenResult() {
            document.getElementById('fullscreenResult').style.display = 'none';
        }

        function clearForm() {
            document.getElementById('voucherCode').value = '';
            document.getElementById('imageUpload').value = '';
            document.getElementById('result').style.display = 'none';
            document.getElementById('fullscreenResult').style.display = 'none';
        }

        // Drag and drop functionality
        const uploadArea = document.querySelector('.upload-area');
        
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
                document.getElementById('imageUpload').files = files;
                handleImageUpload();
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
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Invalid file type'})
        
        # Read image data
        image_data = file.read()
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'success': False, 'message': 'Could not decode image'})
        
        # Decode QR codes
        decoded_objects = decode(image)
        
        if decoded_objects:
            qr_data = decoded_objects[0].data.decode("utf-8")
            
            # Check if it's a valid voucher code (12 characters, alphanumeric)
            if len(qr_data) == 12 and qr_data.isalnum():
                return jsonify({'success': True, 'code': qr_data})
            else:
                return jsonify({'success': False, 'message': 'Invalid voucher code format'})
        else:
            return jsonify({'success': False, 'message': 'No QR code found'})
    
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
    """Redeem a voucher"""
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
    print(f"Starting {Config.CAFE_NAME} Cafe Interface (Improved UI & In-Page Camera)...")
    print(f"Cafe Interface: http://localhost:{Config.CAFE_PORT}")
    print("Press Ctrl+C to stop")
    print("=" * 30)
    
    # Start the server
    app.run(host=Config.HOST, port=Config.CAFE_PORT, debug=Config.DEBUG)
