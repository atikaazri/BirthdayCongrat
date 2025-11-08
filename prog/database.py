#!/usr/bin/env python3
"""
Centralized database interface for BDVoucher system
All interfaces use this file for data operations
"""
import csv
import os
import secrets
import string
from datetime import datetime, timedelta
import base64
import qrcode
from io import BytesIO
from config import Config
from secure_qr import secure_qr  # V2 QR signer

class VoucherDatabase:
    """Centralized database interface for voucher operations"""
    
    def __init__(self):
        self.vouchers_db = {}
        self.employees_cache = []
        self.load_all_data()
    
    def load_all_data(self):
        """Load all data from CSV files"""
        self.load_employees()
        self.load_vouchers_from_csv()
    
    def load_employees(self):
        """Load employees from CSV"""
        self.employees_cache = []
        try:
            with open(Config.EMPLOYEES_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.employees_cache.append(row)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading employees: {e}")
        return self.employees_cache
    
    def load_vouchers_from_csv(self):
        """Load vouchers from voucher history CSV file"""
        self.vouchers_db = {}
        
        try:
            with open(Config.VOUCHER_HISTORY_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    voucher_code = row['voucher_code']
                    status = row['status']
                    
                    if status == 'created':
                        # Create voucher entry from creation record
                        created_at = datetime.fromisoformat(row['timestamp'])
                        expires_at = created_at + timedelta(hours=Config.get_voucher_validity_hours())
                        
                        self.vouchers_db[voucher_code] = {
                            'employee_id': row['employee_id'],
                            'employee_name': row['employee_name'],
                            'created_at': row['timestamp'],
                            'expires_at': expires_at.isoformat(),
                            'redeemed': False,
                            'redeemed_at': None
                        }
                    elif status == 'redeemed' and voucher_code in self.vouchers_db:
                        # Update redemption status
                        self.vouchers_db[voucher_code]['redeemed'] = True
                        self.vouchers_db[voucher_code]['redeemed_at'] = row['timestamp']
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading vouchers: {e}")
    
    def get_employees(self):
        """Get all employees"""
        return self.employees_cache
    
    def get_birthday_today(self):
        """Get employees with birthday today"""
        today = datetime.now()
        birthdays = []
        
        for employee in self.employees_cache:
            try:
                # Parse birthday (assuming format: YYYY-MM-DD or MM-DD)
                birthday_str = employee.get('date_of_birth', '')
                if not birthday_str:
                    continue
                
                # Handle different date formats
                if len(birthday_str.split('-')) == 3:
                    # Full date: YYYY-MM-DD
                    birthday = datetime.strptime(birthday_str, '%Y-%m-%d')
                else:
                    # Month-Day: MM-DD
                    birthday = datetime.strptime(birthday_str, '%m-%d')
                    birthday = birthday.replace(year=today.year)
                
                if birthday.month == today.month and birthday.day == today.day:
                    birthdays.append(employee)
            except ValueError:
                continue
        
        return birthdays
    
    def generate_secure_code(self, employee_id, date_of_birth):
        """Generate secure voucher code using UUID like your system"""
        import uuid
        return str(uuid.uuid4()).replace("-", "").upper()[:12]
    
    def create_voucher(self, employee_id, employee_name):
        """Create a voucher with secure code"""
        # Reload vouchers to ensure we have latest data
        self.load_vouchers_from_csv()
        
        # Check if employee already has an active voucher
        for code, voucher in self.vouchers_db.items():
            if voucher['employee_id'] == employee_id and not voucher['redeemed']:
                # Employee already has an active voucher, return existing code
                return code
        
        # Get employee's date of birth
        employee = None
        for emp in self.employees_cache:
            if emp['employee_id'] == employee_id:
                employee = emp
                break
        
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")
        
        date_of_birth = employee.get('date_of_birth', '')
        
        # Generate unique secure code based on ID and date of birth
        voucher_code = self.generate_secure_code(employee_id, date_of_birth)
        
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=Config.get_voucher_validity_hours())
        
        self.vouchers_db[voucher_code] = {
            'employee_id': employee_id,
            'employee_name': employee_name,
            'created_at': created_at.isoformat(),
            'expires_at': expires_at.isoformat(),
            'redeemed': False,
            'redeemed_at': None
        }
        
        # Save to history
        self.save_voucher_to_history(voucher_code, employee_id, employee_name, 'created')
        
        return voucher_code
    
    def check_voucher_status(self, voucher_code):
        """Check if voucher is valid and active"""
        # Reload vouchers to ensure we have latest data
        self.load_vouchers_from_csv()
        
        if voucher_code not in self.vouchers_db:
            return False, 'Voucher not found'
        
        voucher = self.vouchers_db[voucher_code]
        
        # Check if already redeemed
        if voucher['redeemed']:
            return False, 'Voucher already redeemed'
        
        # Check expiration
        expires_at = datetime.fromisoformat(voucher['expires_at'])
        if datetime.now() > expires_at:
            return False, 'Voucher expired'
        
        return True, 'Voucher is valid and active'
    
    def redeem_voucher(self, voucher_code):
        """Redeem a voucher with proper validation"""
        # First check voucher status
        is_valid, message = self.check_voucher_status(voucher_code)
        if not is_valid:
            return False, message
        
        voucher = self.vouchers_db[voucher_code]
        
        # Mark as redeemed
        voucher['redeemed'] = True
        voucher['redeemed_at'] = datetime.now().isoformat()
        
        # Save to history
        self.save_voucher_to_history(voucher_code, voucher['employee_id'], voucher['employee_name'], 'redeemed')
        
        # Clean up QR image after redemption
        self.cleanup_qr_images(voucher_code)
        
        return True, voucher
    
    def get_all_vouchers(self):
        """Get all vouchers"""
        # Reload vouchers to ensure we have latest data
        self.load_vouchers_from_csv()
        return self.vouchers_db
    
    def get_voucher_history(self):
        """Get voucher history from CSV"""
        history = []
        try:
            with open(Config.VOUCHER_HISTORY_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    history.append(row)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading history: {e}")
        return history
    
    def save_voucher_to_history(self, voucher_code, employee_id, employee_name, status):
        """Save voucher action to history"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(Config.VOUCHER_HISTORY_CSV), exist_ok=True)
            
            # Check if file exists and has headers
            file_exists = os.path.exists(Config.VOUCHER_HISTORY_CSV)
            
            # Use a more robust approach - read existing data, append new row, write back
            existing_data = []
            if file_exists:
                try:
                    with open(Config.VOUCHER_HISTORY_CSV, 'r', encoding='utf-8', newline='') as f:
                        reader = csv.reader(f)
                        existing_data = list(reader)
                except Exception as e:
                    print(f"Error reading existing history: {e}")
                    existing_data = []
            
            # Add new row
            new_row = [
                datetime.now().isoformat(),
                voucher_code,
                employee_id,
                employee_name,
                status
            ]
            
            # If file doesn't exist or is empty, add header
            if not file_exists or len(existing_data) == 0:
                existing_data = [['timestamp', 'voucher_code', 'employee_id', 'employee_name', 'status']]
            
            existing_data.append(new_row)
            
            # Write all data back to file
            with open(Config.VOUCHER_HISTORY_CSV, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(existing_data)
                
            print(f"[HISTORY] Saved {status} for voucher {voucher_code}")
        except Exception as e:
            print(f"Error saving to history: {e}")


   
    '''
    def generate_qr_code(self, voucher_code):
        Generate QR code for voucher and save to fil
        # Import QR system functions
        from qr_system import create_qr_code
        
        # Create and save QR code image
        qr_filename = create_qr_code(voucher_code)
        
        # Also create base64 for web display
        img = qrcode.make(voucher_code)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    '''
    
    def generate_qr_code(self, voucher_code):
        """Generate QR code for voucher and return a base64 data URL"""
        from qr_system import create_qr_code
        # single source of truth (now secure V2 payload)
        return create_qr_code(voucher_code)

    
  

    
    def clear_voucher_history(self):
        """Clear voucher history (for testing)"""
        try:
            with open(Config.VOUCHER_HISTORY_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'voucher_code', 'employee_id', 'employee_name', 'status'])
        except Exception as e:
            print(f"Error clearing history: {e}")
    
    def cleanup_qr_images(self, voucher_code):
        """Clean up QR image file if voucher is redeemed or expired"""
        try:
            qr_path = os.path.join(Config.QRCODES_DIR, f"{voucher_code}.png")
            if os.path.exists(qr_path):
                os.remove(qr_path)
                print(f"[CLEANUP] Removed QR image: {qr_path}")
        except Exception as e:
            print(f"Error cleaning up QR image: {e}")
    
    def cleanup_expired_vouchers(self):
        """Clean up expired vouchers and their QR images"""
        from datetime import datetime
        
        expired_codes = []
        for code, voucher in self.vouchers_db.items():
            try:
                expires_at = datetime.fromisoformat(voucher['expires_at'])
                if datetime.now() > expires_at and not voucher['redeemed']:
                    expired_codes.append(code)
            except:
                continue
        
        for code in expired_codes:
            self.cleanup_qr_images(code)
            print(f"[CLEANUP] Expired voucher: {code}")
        
        return len(expired_codes)
    
    def get_voucher_info(self, voucher_code):
        """Get detailed voucher information including status"""
        # Reload vouchers to ensure we have latest data
        self.load_vouchers_from_csv()
        
        if voucher_code not in self.vouchers_db:
            return None, 'Voucher not found'
        
        voucher = self.vouchers_db[voucher_code]
        expires_at = datetime.fromisoformat(voucher['expires_at'])
        current_time = datetime.now()
        
        # Determine status
        if voucher['redeemed']:
            status = 'redeemed'
            status_message = 'Already redeemed'
        elif current_time > expires_at:
            status = 'expired'
            status_message = 'Expired'
        else:
            status = 'active'
            status_message = 'Valid and active'
        
        return {
            'voucher_code': voucher_code,
            'employee_id': voucher['employee_id'],
            'employee_name': voucher['employee_name'],
            'created_at': voucher['created_at'],
            'expires_at': voucher['expires_at'],
            'redeemed': voucher['redeemed'],
            'redeemed_at': voucher.get('redeemed_at'),
            'status': status,
            'status_message': status_message,
            'time_remaining': str(expires_at - current_time) if status == 'active' else None
        }, status_message
    
    def get_system_stats(self):
        """Get system statistics"""
        self.load_all_data()
        
        active_vouchers = sum(1 for v in self.vouchers_db.values() if not v['redeemed'])
        total_vouchers = len(self.vouchers_db)
        
        # Get fresh birthday count
        birthdays_today = self.get_birthday_today()
        
        return {
            'employees_count': len(self.employees_cache),
            'birthdays_count': len(birthdays_today),
            'vouchers_count': active_vouchers,
            'total_vouchers': total_vouchers,
            'messaging_service': Config.MESSAGING_SERVICE
        }
    
    def refresh_data(self):
        """Refresh all data from CSV files"""
        self.load_all_data()

# Global database instance
db = VoucherDatabase()

# Convenience functions for backward compatibility
def load_employees():
    return db.get_employees()

def get_birthday_today():
    return db.get_birthday_today()

def create_voucher(employee_id, employee_name):
    return db.create_voucher(employee_id, employee_name)

def redeem_voucher(voucher_code):
    return db.redeem_voucher(voucher_code)

def check_voucher_status(voucher_code):
    return db.check_voucher_status(voucher_code)

def get_voucher_info(voucher_code):

    return db.get_voucher_info(voucher_code)

def cleanup_expired_vouchers():
    return db.cleanup_expired_vouchers()

def get_all_vouchers():
    return db.get_all_vouchers()

def get_voucher_history():
    return db.get_voucher_history()

def generate_qr_code(voucher_code):
    return db.generate_qr_code(voucher_code)

def clear_voucher_history():
    return db.clear_voucher_history()

def get_system_stats():
    return db.get_system_stats()

def refresh_data():
    return db.refresh_data()
