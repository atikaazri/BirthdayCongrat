"""
Voucher management system with expiration
"""
from datetime import datetime, timedelta
import csv
import os
from config import Config

# In-memory storage (use database for production)
vouchers_db = {}

# CSV history file (configurable)
HISTORY_CSV = Config.VOUCHER_HISTORY_CSV_FILE

def save_voucher_to_history(voucher_code, employee_id, employee_name, qr_code_data):
    """Save voucher data to CSV history file"""
    file_exists = os.path.exists(HISTORY_CSV)
    
    with open(HISTORY_CSV, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['timestamp', 'voucher_code', 'employee_id', 'employee_name', 'qr_code_data', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'timestamp': datetime.now().isoformat(),
            'voucher_code': voucher_code,
            'employee_id': employee_id,
            'employee_name': employee_name,
            'qr_code_data': qr_code_data,
            'status': 'created'
        })


def create_voucher(employee_id, employee_name, qr_code_data=None):
    """Create unique voucher code with expiration using employee_id + today's date"""
    today = datetime.now().strftime('%Y%m%d')
    voucher_code = f"{employee_id}_{today}"
    created_at = datetime.now()
    expires_at = created_at + timedelta(hours=Config.VOUCHER_VALIDITY_HOURS)
    
    vouchers_db[voucher_code] = {
        'employee_id': employee_id,
        'employee_name': employee_name,
        'created_at': created_at.isoformat(),
        'expires_at': expires_at.isoformat(),
        'redeemed': False,
        'redeemed_at': None,
        'expired': False
    }
    
    # Save to history CSV
    if qr_code_data:
        save_voucher_to_history(voucher_code, employee_id, employee_name, qr_code_data)
    
    return voucher_code


def is_voucher_expired(voucher):
    """Check if voucher has expired"""
    expires_at = datetime.fromisoformat(voucher['expires_at'])
    return datetime.now() > expires_at


def redeem_voucher(code):
    """Redeem a voucher"""
    if code not in vouchers_db:
        return False, 'Invalid voucher code'
    
    voucher = vouchers_db[code]
    
    # Check expiration
    if is_voucher_expired(voucher):
        voucher['expired'] = True
        return False, f'Voucher expired (was valid for {Config.VOUCHER_VALIDITY_HOURS} hours)'
    
    if voucher['redeemed']:
        return False, 'Voucher already redeemed'
    
    voucher['redeemed'] = True
    voucher['redeemed_at'] = datetime.now().isoformat()
    
    return True, voucher


def get_voucher(code):
    """Get voucher details"""
    if code not in vouchers_db:
        return None
    
    voucher = vouchers_db[code]
    voucher['is_expired'] = is_voucher_expired(voucher)
    return voucher


def get_all_vouchers():
    """Get all vouchers (admin) with expiration status"""
    result = {}
    for code, voucher in vouchers_db.items():
        voucher['is_expired'] = is_voucher_expired(voucher)
        result[code] = voucher
    return result