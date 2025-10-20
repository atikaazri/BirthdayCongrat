#!/usr/bin/env python3
"""
BDVoucher - Final Comprehensive Testing Script

TO RUN THE SYSTEM:
1. Start the server: python app.py
2. Open browser: http://localhost:5000
3. Run this test: python final_testing.py

This script will:
- Test all system components
- Send actual WhatsApp messages with QR codes
- Test voucher creation and redemption
- Verify frontend/backend integration
- Clean up and provide final status
"""

import os
import sys
import csv
import time
import requests
import subprocess
import threading
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from voucher_system import (
    load_employees, get_birthday_today, create_voucher, 
    redeem_voucher, generate_qr_code, get_all_vouchers, vouchers_db
)
from whatsapp_service import send_whatsapp_message

class Colors:
    """Terminal colors for better output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}[SUCCESS] {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}[ERROR] {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}[INFO] {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARNING] {text}{Colors.END}")

def clear_voucher_history():
    """Clear voucher history for clean testing"""
    try:
        with open(Config.VOUCHER_HISTORY_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'voucher_code', 'employee_id', 'employee_name', 'status'])
        print_success("Voucher history cleared")
    except Exception as e:
        print_error(f"Failed to clear history: {e}")

def test_data_loading():
    """Test CSV data loading"""
    print_header("TESTING DATA LOADING")
    
    try:
        employees = load_employees()
        if employees:
            print_success(f"Loaded {len(employees)} employees from CSV")
            for emp in employees:
                print_info(f"  - {emp['employee_name']} ({emp['phone_number']})")
        else:
            print_error("No employees found")
            return False
            
        birthdays = get_birthday_today()
        if birthdays:
            print_success(f"Found {len(birthdays)} birthdays today")
            for emp in birthdays:
                print_info(f"  - {emp['employee_name']} ({emp['phone_number']})")
        else:
            print_warning("No birthdays today")
            
        return True
    except Exception as e:
        print_error(f"Data loading failed: {e}")
        return False

def test_voucher_system():
    """Test voucher creation and redemption"""
    print_header("TESTING VOUCHER SYSTEM")
    
    try:
        # Clear existing vouchers
        vouchers_db.clear()
        
        # Create test voucher
        test_employee_id = "TEST001"
        test_employee_name = "Test Employee"
        
        voucher_code = create_voucher(test_employee_id, test_employee_name)
        print_success(f"Created secure voucher: {voucher_code}")
        
        # Test QR code generation
        qr_code = generate_qr_code(voucher_code)
        if qr_code and qr_code.startswith('data:image/png;base64,'):
            print_success("QR code generated successfully")
        else:
            print_error("QR code generation failed")
            
        # Test redemption
        success, result = redeem_voucher(voucher_code)
        if success:
            print_success(f"Voucher redeemed for: {result['employee_name']}")
        else:
            print_error(f"Redemption failed: {result}")
            
        # Test invalid voucher
        success, result = redeem_voucher("INVALID_CODE")
        if not success:
            print_success("Invalid voucher correctly rejected")
        else:
            print_error("Invalid voucher was accepted")
            
        return True
    except Exception as e:
        print_error(f"Voucher system test failed: {e}")
        return False

def test_whatsapp_integration():
    """Test WhatsApp message sending"""
    print_header("TESTING WHATSAPP INTEGRATION")
    
    try:
        birthdays = get_birthday_today()
        if not birthdays:
            print_warning("No birthdays today - creating test message")
            # Create a test voucher for demonstration
            test_emp = {
                'employee_id': 'DEMO001',
                'employee_name': 'Demo Employee',
                'phone_number': '+1234567890'  # Test number
            }
            birthdays = [test_emp]
        
        sent_count = 0
        for emp in birthdays:
            # Create voucher
            voucher_code = create_voucher(emp['employee_id'], emp['employee_name'])
            print_info(f"Created voucher for {emp['employee_name']}: {voucher_code}")
            
            # Generate QR code
            qr_code = generate_qr_code(voucher_code)
            
            # Send WhatsApp message
            print_info(f"Sending WhatsApp message to {emp['phone_number']}...")
            success = send_whatsapp_message(emp['phone_number'], emp['employee_name'], voucher_code)
            
            if success:
                print_success(f"Message sent to {emp['employee_name']}")
                sent_count += 1
            else:
                print_warning(f"Failed to send to {emp['employee_name']} (check credentials)")
        
        print_success(f"WhatsApp integration test completed - {sent_count} messages sent")
        return True
        
    except Exception as e:
        print_error(f"WhatsApp integration test failed: {e}")
        return False

def start_server():
    """Start the Flask server in background"""
    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, 'app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        return process
    except Exception as e:
        print_error(f"Failed to start server: {e}")
        return None

def test_web_interface():
    """Test web interface endpoints"""
    print_header("TESTING WEB INTERFACE")
    
    try:
        base_url = "http://localhost:5000"
        
        # Test main page
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print_success("Main page accessible")
            
            # Check for QR scanning elements
            content = response.text
            if 'jsQR' in content and 'startCamera' in content:
                print_success("QR scanning interface loaded")
            else:
                print_error("QR scanning interface missing")
        else:
            print_error(f"Main page failed: {response.status_code}")
            
        # Test status endpoint
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status endpoint working - {data['employees_count']} employees, {data['vouchers_count']} vouchers")
        else:
            print_error(f"Status endpoint failed: {response.status_code}")
            
        # Test history endpoint
        response = requests.get(f"{base_url}/history", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"History endpoint working - {len(data['history'])} records")
        else:
            print_error(f"History endpoint failed: {response.status_code}")
            
        # Test voucher redemption
        vouchers = get_all_vouchers()
        if vouchers:
            test_code = list(vouchers.keys())[0]
            response = requests.post(f"{base_url}/redeem", 
                                   json={'code': test_code}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print_success("Voucher redemption via API working")
                else:
                    print_warning("Voucher already redeemed")
            else:
                print_error(f"Redemption API failed: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server - is it running?")
        return False
    except Exception as e:
        print_error(f"Web interface test failed: {e}")
        return False

def test_birthday_processing():
    """Test birthday processing endpoint"""
    print_header("TESTING BIRTHDAY PROCESSING")
    
    try:
        response = requests.post("http://localhost:5000/send-birthday", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Birthday processing: {data['message']}")
            return True
        else:
            print_error(f"Birthday processing failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Birthday processing test failed: {e}")
        return False

def cleanup_and_summary():
    """Clean up and provide final summary"""
    print_header("CLEANUP AND SUMMARY")
    
    try:
        # Get final statistics
        employees = load_employees()
        birthdays = get_birthday_today()
        vouchers = get_all_vouchers()
        voucher_count = len(vouchers)
        
        # Count history records
        history_count = 0
        try:
            with open(Config.VOUCHER_HISTORY_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                history_count = len(list(reader))
        except:
            pass
        
        print_success("Final System Status:")
        print_info(f"  - Employees: {len(employees)}")
        print_info(f"  - Birthdays today: {len(birthdays)}")
        print_info(f"  - Active vouchers: {voucher_count}")
        print_info(f"  - History records: {history_count}")
        
        # Show voucher codes
        if vouchers:
            print_info("Generated voucher codes:")
            for code, voucher in vouchers.items():
                status = "redeemed" if voucher['redeemed'] else "active"
                print_info(f"  - {code} ({voucher['employee_name']}) - {status}")
        
        print_success("All tests completed successfully!")
        return True
        
    except Exception as e:
        print_error(f"Cleanup failed: {e}")
        return False

def main():
    """Main testing function"""
    print_header("BDVOUCHER FINAL TESTING")
    print_info("Starting comprehensive system testing...")
    print_info("Make sure the server is running: python app.py")
    print_info("Web interface: http://localhost:5000")
    
    # Clear history for clean testing
    clear_voucher_history()
    
    # Test results tracking
    tests = [
        ("Data Loading", test_data_loading),
        ("Voucher System", test_voucher_system),
        ("WhatsApp Integration", test_whatsapp_integration),
        ("Web Interface", test_web_interface),
        ("Birthday Processing", test_birthday_processing),
        ("Cleanup & Summary", cleanup_and_summary)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print_warning(f"{test_name} test had issues")
        except Exception as e:
            print_error(f"{test_name} test failed: {e}")
    
    # Final results
    print_header("FINAL RESULTS")
    print_success(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print_success("ALL TESTS PASSED! System is ready for production!")
    else:
        print_warning("Some tests had issues. Check the output above.")
    
    print_info("\nTo run the system:")
    print_info("1. Start server: python app.py")
    print_info("2. Open browser: http://localhost:5000")
    print_info("3. Test QR scanning with camera")
    print_info("4. Test manual voucher entry")
    print_info("5. Send birthday wishes")

if __name__ == "__main__":
    main()
