#!/usr/bin/env python3
"""
Final Testing Script - Full Program Execution
This script runs the complete birthday voucher system with WhatsApp messaging
"""

import os
import sys
import time
import threading
import subprocess
from datetime import datetime

# Add the prog directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import get_birthday_today, create_voucher, generate_qr_code
from whatsapp_service import send_whatsapp_message

def print_header():
    """Print the program header"""
    print("=" * 60)
    print(f"🎂 {Config.CAFE_NAME} Birthday Voucher System")
    print("=" * 60)
    print(f"📍 Location: {Config.CAFE_LOCATION}")
    print(f"🎁 Reward: {Config.VOUCHER_REWARD} (Value: {Config.VOUCHER_VALUE})")
    print(f"⏰ Validity: {Config.get_validity_period_text()}")
    print(f"📱 Messaging: {Config.MESSAGING_SERVICE}")
    print(f"🕐 Auto-messaging: {'Enabled' if Config.AUTO_MESSAGING_ENABLED else 'Disabled'}")
    if Config.AUTO_MESSAGING_ENABLED:
        print(f"⏰ Auto-messaging time: {Config.AUTO_MESSAGING_TIME} {Config.AUTO_MESSAGING_TIMEZONE}")
    print("=" * 60)

def print_info(message):
    """Print info message"""
    print(f"[INFO] {message}")

def print_success(message):
    """Print success message"""
    print(f"[SUCCESS] {message}")

def print_error(message):
    """Print error message"""
    print(f"[ERROR] {message}")

def print_warning(message):
    """Print warning message"""
    print(f"[WARNING] {message}")

def start_servers():
    """Start all required servers"""
    print_info("Starting all servers...")
    
    # Start main server
    print_info("Starting main server (port 5000)...")
    main_server = subprocess.Popen([
        sys.executable, "app.py"
    ], cwd=os.path.dirname(os.path.abspath(__file__)))
    
    time.sleep(2)  # Give server time to start
    
    # Start cafe interface
    print_info("Starting cafe interface (port 5001)...")
    cafe_server = subprocess.Popen([
        sys.executable, "cafe_interface.py"
    ], cwd=os.path.dirname(os.path.abspath(__file__)))
    
    time.sleep(2)  # Give server time to start
    
    # Start admin interface
    print_info("Starting admin interface (port 5002)...")
    admin_server = subprocess.Popen([
        sys.executable, "admin_interface.py"
    ], cwd=os.path.dirname(os.path.abspath(__file__)))
    
    time.sleep(2)  # Give server time to start
    
    print_success("All servers started successfully!")
    print_info("Web interfaces available at:")
    print_info("  - Main Server: http://localhost:5000")
    print_info("  - Cafe Interface: http://localhost:5001")
    print_info("  - Admin Interface: http://localhost:5002")
    
    return main_server, cafe_server, admin_server

def send_birthday_messages():
    """Send birthday messages to employees with birthdays today"""
    print_info("Checking for employees with birthdays today...")
    
    # Force refresh data to ensure we have latest employee data
    from database import refresh_data
    refresh_data()
    
    birthdays = get_birthday_today()
    
    if not birthdays:
        print_warning("No employees have birthdays today.")
        return []
    
    print_success(f"Found {len(birthdays)} employees with birthdays today!")
    print()
    
    results = []
    for employee in birthdays:
        try:
            print_info(f"Processing birthday for {employee['employee_name']} ({employee['employee_id']})")
            
            # Create voucher
            voucher_code = create_voucher(employee['employee_id'], employee['employee_name'])
            print_success(f"Created voucher: {voucher_code}")
            
            # Generate QR code
            qr_code = generate_qr_code(voucher_code)
            print_success(f"Generated QR code: {voucher_code}.png")
            
            # Send WhatsApp message
            print_info(f"Sending WhatsApp message to {employee['phone_number']}...")
            success = send_whatsapp_message(
                employee['phone_number'],
                employee['employee_name'],
                voucher_code
            )
            
            if success:
                print_success(f"WhatsApp message sent to {employee['employee_name']}")
                results.append({
                    'employee_name': employee['employee_name'],
                    'voucher_code': voucher_code,
                    'message_sent': True
                })
            else:
                print_error(f"Failed to send WhatsApp message to {employee['employee_name']}")
                results.append({
                    'employee_name': employee['employee_name'],
                    'voucher_code': voucher_code,
                    'message_sent': False
                })
            
            print()
            
        except Exception as e:
            print_error(f"Error processing {employee['employee_name']}: {e}")
            results.append({
                'employee_name': employee['employee_name'],
                'error': str(e)
            })
    
    return results

def print_results_summary(results):
    """Print summary of results"""
    print("=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    if not results:
        print_warning("No birthday messages were sent.")
        return
    
    successful = sum(1 for r in results if r.get('message_sent', False))
    failed = len(results) - successful
    
    print_success(f"Successfully sent: {successful} messages")
    if failed > 0:
        print_error(f"Failed to send: {failed} messages")
    
    print()
    print("📋 Detailed Results:")
    for result in results:
        if result.get('message_sent', False):
            print_success(f"✅ {result['employee_name']} - Voucher: {result['voucher_code']}")
        elif 'error' in result:
            print_error(f"❌ {result['employee_name']} - Error: {result['error']}")
        else:
            print_warning(f"⚠️ {result['employee_name']} - Message not sent")
    
    print("=" * 60)

def main():
    """Main function"""
    try:
        # Print header
        print_header()
        
        # Send birthday messages
        print_info("Starting birthday message processing...")
        results = send_birthday_messages()
        
        # Print results summary
        print_results_summary(results)
        
        # Start servers
        main_server, cafe_server, admin_server = start_servers()
        
        print()
        print_info("🎉 Full system is now running!")
        print_info("You can now visit the web interfaces to test the system.")
        print_info("Press Ctrl+C to stop all servers.")
        print()
        
        # Keep the program running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print()
            print_info("Shutting down servers...")
            
            # Terminate servers
            main_server.terminate()
            cafe_server.terminate()
            admin_server.terminate()
            
            # Wait for servers to close
            main_server.wait()
            cafe_server.wait()
            admin_server.wait()
            
            print_success("All servers stopped. Goodbye!")
            
    except Exception as e:
        print_error(f"Error running final testing: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())