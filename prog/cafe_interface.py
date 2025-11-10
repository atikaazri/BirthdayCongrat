#!/usr/bin/env python3
"""
Cafe Interface for BDVoucher - Improved UI with In-Page Camera
Chill birthday design, mobile compatible, auto-scan on upload

Cafe Interface for BDVoucher System
Independent Flask app on its own port (default 5001)
Handles voucher redemption by cafe staff or admins
"""

    
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import current_user
from flask_wtf.csrf import CSRFProtect
from config import Config
from database import redeem_voucher
from auth import (
    login_manager, User, authenticate_user, login_user, 
    logout_user, login_required, cafe_required, generate_jwt_token
)
from security_helpers import (
    csrf_protect, validate_voucher_code, sanitize_input,
    add_security_headers, generate_csrf_token
)
import cv2
import threading
import time
import os
import numpy as np
from pyzbar.pyzbar import decode
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
from qr_system import parse_qr_text


# ======================================================
# Flask App Setup
# ======================================================

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-this-secret-key-in-production-12345')

# Initialize Flask-Login
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = "strong"

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

csrf = CSRFProtect(app)

# Add security headers to all responses
@app.after_request
def set_security_headers(response):
    return add_security_headers(response)



# ======================================================
# Templates
# ======================================================
# Login HTML template for cafe
CAFE_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cafe Login - {{cafe_name}}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 25px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            max-width: 400px;
            width: 100%;
        }
        h1 {
            color: #d63384;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #495057;
            font-weight: 600;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ffc1cc;
            border-radius: 15px;
            font-size: 16px;
            box-sizing: border-box;
        }
        input:focus {
            outline: none;
            border-color: #ff6b9d;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #ff6b9d, #c44569);
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 16px;
            cursor: pointer;
            font-weight: 600;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        .error.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🔐 Cafe Login</h1>
        <div class="error" id="errorMsg"></div>
        <form id="loginForm">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required autocomplete="username">
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required autocomplete="current-password">
            </div>
            <button type="submit">Login</button>
        </form>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorMsg = document.getElementById('errorMsg');
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username, password})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = '/';
                } else {
                    errorMsg.textContent = data.message || 'Login failed';
                    errorMsg.classList.add('show');
                }
            } catch (error) {
                errorMsg.textContent = 'Error: ' + error.message;
                errorMsg.classList.add('show');
            }
        });
    </script>
</body>
</html>
"""

CAFE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token }}">
    <title>{{ cafe_name }} - Birthday Voucher Redemption</title>
    <!-- Add jsQR library for QR code scanning -->
    <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js"></script>
    
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
                    <div class="camera-overlay" id="cameraOverlay" style="display: none;">
                        <!-- Green scanning frame -->
                        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 250px; height: 250px; border: 3px solid #00ff00; border-radius: 10px; pointer-events: none;"></div>
                    </div>
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
                <input type="text" id="voucherCode" placeholder="Enter voucher code or scan QR code" maxlength="200">
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
        const CSRF = document.querySelector('meta[name="csrf-token"]')?.content || '';
        let scanning = false;
        let countdownTimer = null;
        let videoStream = null;
        let scanInterval = null; // Add this new variable

        
        function startCameraScan() {
            if (scanning) return;
            
            scanning = true;
            document.getElementById('cameraBtn').style.display = 'none';
            document.getElementById('stopCameraBtn').style.display = 'inline-block';
            document.getElementById('cameraContainer').style.display = 'block';
            document.getElementById('cameraStatus').style.display = 'block';
            document.getElementById('cameraPreview').style.display = 'block';
            document.getElementById('statusText').textContent = 'Starting camera...';
            
            // Clear any previous results
            document.getElementById('result').style.display = 'none';

            // Start countdown
            startCountdown();
            
            // Start in-page camera with QR scanning
            startInPageCamera();
        }

        function startInPageCamera() {
            // Stop backend camera if it's running (cleanup)
            fetch('/stop-camera-scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': CSRF }
            }).catch(error => console.log('Backend camera cleanup:', error));
            
            // Get user media with better constraints for QR scanning
            navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'environment', // Prefer rear camera
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                } 
            })
            .then(stream => {
                videoStream = stream;
                const video = document.getElementById('video');
                video.srcObject = stream;
                document.getElementById('cameraOverlay').style.display = 'block';
                document.getElementById('statusText').textContent = 'Camera ready - scanning for QR codes...';
                
                // Wait for video to be ready
                video.onloadedmetadata = () => {
                    // Start QR code scanning
                    startQRScanning(video);
                };
            })
            .catch(error => {
                console.error('Error accessing camera:', error);
                document.getElementById('statusText').textContent = 'Camera error: ' + error.message;
                
                if (error.name === 'NotAllowedError') {
                    showResult('Camera permission denied. Please allow camera access in your browser settings.', 'error');
                } else if (error.name === 'NotFoundError') {
                    showResult('No camera found. Please check if your device has a camera.', 'error');
                } else {
                    showResult('Camera access error: ' + error.message, 'error');
                }
                
                stopCameraScan();
            });
        }

        // Add this NEW function for QR scanning
        function startQRScanning(videoElement) {
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            
            // Scan for QR codes every 300ms (faster response)
            scanInterval = setInterval(() => {
                if (!scanning || videoElement.readyState !== videoElement.HAVE_ENOUGH_DATA) {
                    return;
                }
                
                try {
                    // Set canvas dimensions to match video
                    canvas.width = videoElement.videoWidth;
                    canvas.height = videoElement.videoHeight;
                    
                    // Draw video frame to canvas
                    context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
                    
                    // Get image data for QR scanning
                    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
                    
                    // Use jsQR library to detect QR codes
                    const code = jsQR(imageData.data, imageData.width, imageData.height, {
                        inversionAttempts: "dontInvert",
                    });
                    
                    if (code) {
                        console.log('QR code detected:', code.data);
                        document.getElementById('statusText').textContent = '✅ QR code detected! Validating...';
                        
                        // Add visual feedback
                        const overlay = document.getElementById('cameraOverlay');
                        overlay.style.borderColor = '#00ff00';
                        overlay.style.backgroundColor = 'rgba(0, 255, 0, 0.1)';
                        
                        // Validate the scanned code
                        validateVoucher(code.data);
                        stopCameraScan();
                    }
                } catch (error) {
                    console.error('QR scanning error:', error);
                }
            }, 300); // Scan every 300ms for better responsiveness
        }

        
        function stopCameraScan() {
            if (!scanning) return;
            
            scanning = false;
            
            // Stop QR scanning
            if (scanInterval) {
                clearInterval(scanInterval);
                scanInterval = null;
            }
            
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
            
            // Stop backend camera (cleanup)
            fetch('/stop-camera-scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': CSRF }
            }).catch(error => console.log('Backend camera stop:', error));
            
            // Update UI
            document.getElementById('cameraBtn').style.display = 'inline-block';
            document.getElementById('stopCameraBtn').style.display = 'none';
            document.getElementById('cameraContainer').style.display = 'none';
            document.getElementById('cameraStatus').style.display = 'none';
            document.getElementById('cameraPreview').style.display = 'none';
            document.getElementById('cameraOverlay').style.display = 'none';
            
            // Reset overlay styles
            const overlay = document.getElementById('cameraOverlay');
            overlay.style.borderColor = '';
            overlay.style.backgroundColor = '';
        }


        // NEW: Add the startCountdown function
        function startCountdown() {
            let timeLeft = 120; // 2 minutes
            const countdownElement = document.getElementById('countdown');
            countdownElement.style.display = 'block';
            
            countdownTimer = setInterval(() => {
                if (!scanning) {
                    clearInterval(countdownTimer);
                    return;
                }
                
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                countdownElement.textContent = `⏰ ${minutes}:${seconds.toString().padStart(2, '0')} remaining`;
                timeLeft--;
                
                if (timeLeft < 0) {
                    clearInterval(countdownTimer);
                    showResult('Scanning time expired. Please try again.', 'info');
                    stopCameraScan();
                }
            }, 1000);
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
                headers: { 'X-CSRF-Token': CSRF },
                body: formData
            })
            .then(res => {
                if (!res.ok) {
                    return res.json().then(data => {
                        throw new Error(data.message || 'Scan failed');
                    });
                }
                return res.json();
            })
            .then(data => {
                if (data.success && data.code) {
                    // Automatically validate the scanned code
                    validateVoucher(data.code);
                } else {
                    showFullScreenResult('Scan Failed', data.message || 'No valid voucher QR code found in image. Please ensure the QR code is clear and not damaged.', 'error');
                    setTimeout(() => {
                        clearForm();
                    }, 4000);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showFullScreenResult('Scan Error', error.message || 'Error scanning image. Please try again or use manual entry.', 'error');
                setTimeout(() => {
                    clearForm();
                }, 4000);
            });
        }

        function redeemVoucher() {
            const code = document.getElementById('voucherCode').value.trim();
            
            if (!code) {
                showResult('Please enter a voucher code.', 'error');
                return;
            }
            
            // Allow both V2 secure codes (longer format) and V1 codes (12 characters)
            if (code.length < 8) {
                showResult('Voucher code is too short.', 'error');
                return;
            }
            
            validateVoucher(code);
        }

        function validateVoucher(code) {
            // Show loading state
            showResult('Validating voucher code...', 'info');
            
            fetch('/redeem', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': CSRF },
                body: JSON.stringify({ code: code })
            })
            .then(res => {
                if (!res.ok) {
                    return res.json().then(data => {
                        throw new Error(data.message || 'Validation failed');
                    });
                }
                return res.json();
            })
            .then(data => {
                if (data.success) {
                    showFullScreenResult('Success! 🎉', `Voucher redeemed successfully for ${data.employee_name}!`, 'success');
                    setTimeout(() => {
                        clearForm();
                    }, 3000);
                } else {
                    showFullScreenResult('Error', data.message || 'Failed to redeem voucher', 'error');
                    setTimeout(() => {
                        clearForm();
                    }, 4000);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                let errorMsg = 'Network error occurred';
                if (error.message) {
                    errorMsg = error.message;
                }
                showFullScreenResult('Error', errorMsg, 'error');
                setTimeout(() => {
                    clearForm();
                }, 4000);
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



@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """Cafe login"""
    if current_user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        username = sanitize_input(data.get('username', ''))
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400

        user = authenticate_user(username, password)
        if user:
            if user.role not in ['cafe', 'admin']:
                return jsonify({'success': False, 'message': 'Cafe access required'}), 403

            login_user(user)
            token = generate_jwt_token(user)
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'token': token,
                'user': {
                    'username': user.username,
                    'role': user.role
                }
            })

        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

    return render_template_string(CAFE_LOGIN_TEMPLATE, cafe_name=Config.CAFE_NAME)

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    return redirect('/login')  

@app.route('/')
@login_required
@cafe_required
def index():
    """Cafe redemption page"""
    generate_csrf_token()  # Generate CSRF token
    return render_template_string(CAFE_HTML_TEMPLATE, 
                                cafe_name=Config.CAFE_NAME, 
                                cafe_location=Config.CAFE_LOCATION)

# ======================================================
# QR / Camera Endpoints
# ======================================================

# Global variables for camera
camera = None
scanner_active = False
scanner_result = None
scanner_error = None

# Allowed file extensions for image upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/start-camera-scan', methods=['POST'])
@csrf.exempt  # Exempt CSRF for API calls
@limiter.limit("120 per minute")
def start_camera_scan():
    """Start the camera scan"""
    # Check authentication manually to return JSON instead of HTML redirect
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
    
    # Check cafe role
    if not hasattr(current_user, 'role') or current_user.role not in ['cafe', 'admin']:
        return jsonify({'success': False, 'message': 'Cafe access required'}), 403
    
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
@csrf.exempt  # Exempt CSRF for API calls
@limiter.limit("120 per minute")
def stop_camera_scan():
    """Stop the camera scan"""
    # Check authentication manually to return JSON instead of HTML redirect
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
    
    # Check cafe role
    if not hasattr(current_user, 'role') or current_user.role not in ['cafe', 'admin']:
        return jsonify({'success': False, 'message': 'Cafe access required'}), 403
    
    global camera, scanner_active, scanner_result, scanner_error
    
    scanner_active = False
    scanner_result = None
    scanner_error = None
    
    if camera:
        camera.release()
        camera = None
    
    return jsonify({'success': True, 'message': 'Camera scan stopped'})

@app.route('/check-camera-scan')
@csrf.exempt  # Exempt CSRF for API calls
@limiter.limit("120 per minute")
def check_camera_scan():
    """Check camera scan status and return any detected codes"""
    # Check authentication manually to return JSON instead of HTML redirect
    if not current_user.is_authenticated:
        return jsonify({
            'active': False,
            'detected': False,
            'error': 'Authentication required'
        }), 401
    
    # Check cafe role
    if not hasattr(current_user, 'role') or current_user.role not in ['cafe', 'admin']:
        return jsonify({
            'active': False,
            'detected': False,
            'error': 'Cafe access required'
        }), 403
    
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
@csrf.exempt  # Exempt CSRF for file uploads - we'll handle auth separately
@limiter.limit("120 per minute")
def scan_image():
    """Scan QR code from uploaded image"""
    # Check authentication manually to return JSON instead of HTML redirect
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
    
    # Check cafe role
    if not hasattr(current_user, 'role') or current_user.role not in ['cafe', 'admin']:
        return jsonify({'success': False, 'message': 'Cafe access required'}), 403
    
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No image file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Invalid file type. Please upload PNG, JPG, JPEG, GIF, or BMP images.'}), 400
        
        # Read image data
        image_data = file.read()
        if not image_data:
            return jsonify({'success': False, 'message': 'Image file is empty'}), 400
        
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'success': False, 'message': 'Could not decode image. Please ensure the file is a valid image.'}), 400
        
        # Decode QR codes
        try:
            decoded_objects = decode(image)
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error decoding QR code: {str(e)}'}), 500

        if decoded_objects:
            # Try each detected QR code until we find a valid voucher
            qr_data_list = []
            last_error = None
            
            for obj in decoded_objects:
                try:
                    qr_data = obj.data.decode("utf-8").strip()
                    if not qr_data:
                        continue
                    
                    # Store QR data for error reporting
                    qr_data_list.append(qr_data[:100])  # Store first 100 chars for debugging
                    
                    # Parse QR code (handles both V1 and V2)
                    # allow_expired=True so we extract code even if expired (check expiration at redemption)
                    try:
                        code = parse_qr_text(qr_data, allow_expired=True)
                        if code:
                            # Log what we found for debugging
                            print(f"[IMAGE SCAN] Successfully extracted code: {code} from QR data: {qr_data[:50]}...")
                            return jsonify({'success': True, 'code': code})
                    except ValueError as e:
                        # Log the error for debugging
                        error_msg = str(e)
                        last_error = error_msg
                        print(f"[IMAGE SCAN] Parse error for QR data '{qr_data[:50]}...': {error_msg}")
                        
                        # If it's a signature error, this QR is definitely invalid
                        if "signature" in error_msg.lower() or "tampered" in error_msg.lower():
                            continue
                        
                        # For other errors (like expired), we might still want to try to extract
                        # But if parsing fails completely, continue to next QR code
                        continue
                    except Exception as e:
                        # Log unexpected errors
                        last_error = str(e)
                        print(f"[IMAGE SCAN] Unexpected error parsing QR: {e}")
                        # Error parsing, try next QR code
                        continue
                except Exception as e:
                    # Error decoding this QR code, try next
                    last_error = f"Decode error: {str(e)}"
                    continue
            
            # No valid voucher QR codes found - provide helpful error message
            error_message = 'No valid voucher QR code detected in image.'
            if qr_data_list:
                error_message += f' Found {len(qr_data_list)} QR code(s) but could not parse as voucher codes.'
                if last_error:
                    error_message += f' Last error: {last_error}'
            else:
                error_message += ' Please ensure the QR code is clear and visible in the image.'
            
            return jsonify({'success': False, 'message': error_message}), 400
        else:
            return jsonify({
                'success': False, 
                'message': 'No QR code detected in image. Please ensure: 1) The QR code is clear and not blurry, 2) The image is well-lit, 3) The QR code is fully visible, 4) The image format is supported (PNG, JPG, JPEG, GIF, BMP)'
            }), 400

    except Exception as e:
        import traceback
        print(f"Error scanning image: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Error scanning image: {str(e)}'}), 500

def camera_scan_thread():
    """Robust camera scanner: tries multiple camera indices/backends, decodes in grayscale,
    supports secured V2 (parse_qr_text) with legacy 12-char fallback, and returns the first valid code.
    """
    import time
    import cv2
    from pyzbar.pyzbar import decode

    global camera, scanner_active, scanner_result, scanner_error

    try:
        # --- Open camera robustly (try multiple indices, two backends) ---
        indices_to_try = [0, 1, 2, 3]
        camera = None

        for idx in indices_to_try:
            # Windows-friendly first attempt
            cam = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if not cam.isOpened():
                # Fallback backend
                cam.release()
                cam = cv2.VideoCapture(idx)

            if cam.isOpened():
                # Use HD for better QR detection
                cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                camera = cam
                print(f"[CAMERA] Opened camera index {idx}")
                break

        if not camera or not camera.isOpened():
            scanner_error = "Could not access camera (all indices failed)"
            scanner_active = False
            print("[CAMERA] ERROR - no camera available")
            return

        detected_codes = set()
        start_time = time.time()
        timeout_secs = 120.0  # adjust if you want shorter/longer window

        while scanner_active:
            # Timeout guard
            if (time.time() - start_time) >= timeout_secs:
                scanner_error = f"Camera scan timed out after {int(timeout_secs)} seconds"
                scanner_active = False
                print("[CAMERA] Timeout")
                break

            ok, frame = camera.read()
            if not ok:
                # Keep trying a few frames rather than quitting immediately
                continue

            # Grayscale improves QR decode reliability in many cases
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            except Exception:
                gray = frame

            try:
                decoded_objects = decode(gray)
            except Exception as e:
                # If pyzbar hiccups, skip this frame
                decoded_objects = []
                # Optional: print(f"[CAMERA] Decode error: {e}")

            for obj in decoded_objects:
                # Best-effort decode of the QR text
                try:
                    raw = obj.data.decode("utf-8", errors="ignore").strip()
                except Exception:
                    raw = None

                if not raw:
                    continue

                # Try secured V2 first (parse_qr_text). If it fails, fallback to legacy 12-char alnum.
                code = None
                try:
                    from qr_system import parse_qr_text
                    # allow_expired=True lets us extract the code; you still enforce expiry at redemption
                    code = parse_qr_text(raw, allow_expired=True)
                except Exception:
                    if len(raw) == 12 and raw.isalnum():
                        code = raw

                if code and code not in detected_codes:
                    detected_codes.add(code)
                    scanner_result = code
                    scanner_active = False
                    print(f"[CAMERA] Detected voucher code: {code}")
                    break  # stop inner loop

            if scanner_result:
                break  # stop outer while

    except Exception as e:
        scanner_error = str(e)
        scanner_active = False
        print(f"[CAMERA] Unexpected error: {e}")

    finally:
        # Always release resources
        try:
            if camera:
                camera.release()
        except Exception:
            pass
        camera = None

        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

@app.route('/redeem', methods=['POST'])
@csrf.exempt  # Exempt CSRF - we handle auth separately and validate input
@limiter.limit("20 per minute")
def redeem():
    """Redeem a voucher (accept JSON or form)"""
    # Check authentication manually to return JSON instead of HTML redirect
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
    
    # Check cafe role
    if not hasattr(current_user, 'role') or current_user.role not in ['cafe', 'admin']:
        return jsonify({'success': False, 'message': 'Cafe access required'}), 403
    
    if request.is_json:
        raw = (request.json or {}).get('code', '')
    else:
        raw = request.form.get('code', '') or request.values.get('code', '')
    raw = (raw or '').strip()  # ✅ ONLY trim whitespace here

    if not raw:
        return jsonify({'success': False, 'message': 'Voucher code is required'}), 400

    # Normalize (handles V2 "V2|...|sig" and legacy codes)
    from qr_system import parse_qr_text
    
    try:
        code = parse_qr_text(raw)       # ✅ returns the plain voucher code
    except Exception as e:
        return jsonify({'success': False, 'message': f'Invalid QR code: {str(e)}'}), 400

    # Now it's safe to sanitize the plain code if you want
    code = sanitize_input(code)

    # Validate & redeem
    is_valid, msg = validate_voucher_code(code)
    if not is_valid:
        return jsonify({'success': False, 'message': msg}), 400

    ok, res = redeem_voucher(code)
    if ok:
        return jsonify({
            'success': True,
            'employee_name': res['employee_name'],
            'message': 'Voucher redeemed successfully!'
        })
    return jsonify({'success': False, 'message': res}), 400

    '''
    """Redeem a voucher"""
    # Validate JSON request
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Content-Type must be application/json'}), 400
    
    data = request.json
    raw_code = sanitize_input(data.get('code', ''))

    try:
        # Parse secured QR or legacy code into normalized voucher code
        code = parse_qr_text(raw_code)
    except Exception as e:
        return jsonify({'success': False, 'message': f"Invalid QR code: {e}"}), 400

    # Validate voucher code format (still applies to legacy and V2 decoded form)
    is_valid, message = validate_voucher_code(code)
    if not is_valid:
        return jsonify({'success': False, 'message': message}), 400
    
    # Redeem voucher
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
    '''

if __name__ == '__main__':
    print(f"Starting {Config.CAFE_NAME} Cafe Interface (Improved UI & In-Page Camera)...")
    print(f"Cafe Interface: http://localhost:{Config.CAFE_PORT}")
    print("Press Ctrl+C to stop")
    print("=" * 30)
    
    # Start the server
    app.run(host=Config.HOST, port=Config.CAFE_PORT, debug=Config.DEBUG)
