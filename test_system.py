#!/usr/bin/env python3
"""
Test script for the birthday voucher system
This script tests the system without sending actual WhatsApp messages
"""
import os
import sys
from datetime import datetime
from config import Config
from vouchers import create_voucher, redeem_voucher, get_all_vouchers
from send_birthday import load_employees, get_birthday_today, generate_qr_code

def test_config():
    """Test configuration loading"""
    print("Testing Configuration...")
    print(f"  Messaging Service: {Config.MESSAGING_SERVICE}")
    print(f"  Cafe Name: {Config.CAFE_NAME}")
    print(f"  Voucher Reward: {Config.VOUCHER_REWARD}")
    print(f"  Validity Hours: {Config.VOUCHER_VALIDITY_HOURS}")
    print(f"  Brand Emoji: {Config.BRAND_EMOJI}")
    print()

def test_employee_loading():
    """Test employee CSV loading"""
    print("Testing Employee Loading...")
    try:
        employees = load_employees()  # Use default configurable file
        print(f"  Loaded {len(employees)} employees")
        
        for emp in employees:
            print(f"    - {emp[Config.CSV_COLUMNS['employee_name']]} ({emp[Config.CSV_COLUMNS['phone_number']]}) - DOB: {emp[Config.CSV_COLUMNS['date_of_birth']]}")
        
        return employees
    except Exception as e:
        print(f"  Error loading employees: {e}")
        return []
    print()

def test_birthday_detection(employees):
    """Test birthday detection"""
    print("Testing Birthday Detection...")
    try:
        birthdays = get_birthday_today(employees)
        print(f"  Found {len(birthdays)} birthdays today")
        
        if birthdays:
            for emp in birthdays:
                print(f"    - {emp[Config.CSV_COLUMNS['employee_name']]} ({emp[Config.CSV_COLUMNS['phone_number']]})")
        else:
            print("    - No birthdays today")
        
        return birthdays
    except Exception as e:
        print(f"  Error detecting birthdays: {e}")
        return []
    print()

def test_voucher_system():
    """Test voucher creation and redemption"""
    print("Testing Voucher System...")
    try:
        # Create a test voucher
        test_code = create_voucher("TEST001", "Test Employee")
        print(f"  Created voucher: {test_code}")
        
        # Test voucher retrieval
        voucher = get_all_vouchers()
        print(f"  Voucher stored in database")
        
        # Test redemption
        success, result = redeem_voucher(test_code)
        if success:
            print(f"  Voucher redeemed successfully for: {result['employee_name']}")
        else:
            print(f"  Voucher redemption failed: {result}")
        
        # Test QR code generation
        qr_code = generate_qr_code(test_code)
        print(f"  QR code generated (length: {len(qr_code)} chars)")
        
    except Exception as e:
        print(f"  Error testing vouchers: {e}")
    print()

def test_message_generation():
    """Test message template generation"""
    print("Testing Message Generation...")
    try:
        message = Config.get_birthday_message("Test Employee", "+96812345678")
        print("  Birthday message generated:")
        print(f"    {message}")
        
        notification = Config.get_notification_message("Test Employee", "+96812345678")
        print("  Notification message generated:")
        print(f"    {notification}")
        
    except Exception as e:
        print(f"  Error generating messages: {e}")
    print()

def test_messaging_config():
    """Test messaging configuration"""
    print("Testing Messaging Configuration...")
    try:
        if Config.MESSAGING_SERVICE == 'ultramsg':
            if Config.ULTRAMSG_INSTANCE_ID and Config.ULTRAMSG_TOKEN:
                print("  UltraMsg credentials configured")
                print(f"    Instance ID: {Config.ULTRAMSG_INSTANCE_ID}")
                print(f"    Token: {Config.ULTRAMSG_TOKEN[:10]}...")
            else:
                print("  UltraMsg credentials not configured")
                print("    Please set ULTRAMSG_INSTANCE_ID and ULTRAMSG_TOKEN in .env")
        elif Config.MESSAGING_SERVICE == 'twilio':
            if Config.TWILIO_SID and Config.TWILIO_AUTH and Config.TWILIO_PHONE:
                print("  Twilio credentials configured")
                print(f"    SID: {Config.TWILIO_SID}")
                print(f"    Phone: {Config.TWILIO_PHONE}")
            else:
                print("  Twilio credentials not configured")
                print("    Please set TWILIO_SID, TWILIO_AUTH, and TWILIO_PHONE in .env")
        else:
            print(f"  Using {Config.MESSAGING_SERVICE} messaging service")
    except Exception as e:
        print(f"  Error checking messaging config: {e}")
    print()

def main():
    """Run all tests"""
    print("BIRTHDAY VOUCHER SYSTEM - TEST SUITE")
    print("=" * 50)
    print()
    
    # Run tests
    test_config()
    employees = test_employee_loading()
    birthdays = test_birthday_detection(employees)
    test_voucher_system()
    test_message_generation()
    test_messaging_config()
    
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"  Total employees: {len(employees)}")
    print(f"  Birthdays today: {len(birthdays)}")
    print(f"  Messaging service: {Config.MESSAGING_SERVICE}")
    print(f"  Cafe: {Config.CAFE_NAME}")
    print()
    
    if birthdays:
        print("READY TO SEND BIRTHDAY WISHES!")
        print("Run: python send_birthday.py employees.csv")
    else:
        print("No birthdays today. System is ready for testing.")
        print("You can still test the web UI and API endpoints.")
    
    print()
    print("NEXT STEPS:")
    print("  1. Configure messaging credentials in .env file")
    print("  2. Test web scanner: python cafe_ui.py")
    print("  3. Test API: uvicorn api:app --reload --port 8000")
    print("  4. Send birthday wishes: python send_birthday.py")

if __name__ == "__main__":
    main()
