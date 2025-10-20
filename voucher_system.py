#!/usr/bin/env python3
"""
Voucher management system for BDVoucher
"""
import csv
import io
import base64
import qrcode
import secrets
import string
from datetime import datetime, timedelta
from config import Config

# Simple in-memory storage for vouchers
vouchers_db = {}

def load_employees():
    """Load employees from CSV"""
    employees = []
    try:
        with open(Config.EMPLOYEES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                employees.append(row)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error loading employees: {e}")
    return employees

def get_birthday_today():
    """Get employees with birthday today"""
    employees = load_employees()
    today = datetime.now()
    birthdays = []
    
    for emp in employees:
        try:
            dob = datetime.strptime(emp['date_of_birth'], '%Y-%m-%d')
            if dob.month == today.month and dob.day == today.day:
                birthdays.append(emp)
        except ValueError:
            continue
    
    return birthdays

def generate_secure_code():
    """Generate a secure random voucher code"""
    # Generate 8 random characters (letters and numbers)
    alphabet = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(8))
    return f"BDV{random_part}"

def create_voucher(employee_id, employee_name):
    """Create a voucher with secure code"""
    # Generate unique secure code
    voucher_code = generate_secure_code()
    
    # Ensure uniqueness
    while voucher_code in vouchers_db:
        voucher_code = generate_secure_code()
    
    created_at = datetime.now()
    expires_at = created_at + timedelta(hours=Config.VOUCHER_VALIDITY_HOURS)
    
    vouchers_db[voucher_code] = {
        'employee_id': employee_id,
        'employee_name': employee_name,
        'created_at': created_at.isoformat(),
        'expires_at': expires_at.isoformat(),
        'redeemed': False,
        'redeemed_at': None
    }
    
    # Save to history
    save_voucher_to_history(voucher_code, employee_id, employee_name, 'created')
    
    return voucher_code

def redeem_voucher(voucher_code):
    """Redeem a voucher"""
    if voucher_code not in vouchers_db:
        return False, 'Voucher not found'
    
    voucher = vouchers_db[voucher_code]
    
    # Check expiration
    expires_at = datetime.fromisoformat(voucher['expires_at'])
    if datetime.now() > expires_at:
        return False, 'Voucher expired'
    
    if voucher['redeemed']:
        return False, 'Voucher already redeemed'
    
    # Mark as redeemed
    voucher['redeemed'] = True
    voucher['redeemed_at'] = datetime.now().isoformat()
    
    # Save to history
    save_voucher_to_history(voucher_code, voucher['employee_id'], voucher['employee_name'], 'redeemed')
    
    return True, voucher

def save_voucher_to_history(voucher_code, employee_id, employee_name, status):
    """Save voucher action to history"""
    import os
    try:
        file_exists = os.path.exists(Config.VOUCHER_HISTORY_CSV)
        
        with open(Config.VOUCHER_HISTORY_CSV, 'a', newline='', encoding='utf-8') as f:
            fieldnames = ['timestamp', 'voucher_code', 'employee_id', 'employee_name', 'status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'voucher_code': voucher_code,
                'employee_id': employee_id,
                'employee_name': employee_name,
                'status': status
            })
    except Exception as e:
        print(f"Error saving to history: {e}")

def generate_qr_code(voucher_code):
    """Generate QR code as base64 image"""
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(voucher_code)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"

def get_all_vouchers():
    """Get all vouchers"""
    return vouchers_db
