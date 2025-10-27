#!/usr/bin/env python3
"""
Configuration settings for BDVoucher system
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Basic settings
    CAFE_NAME = os.getenv('CAFE_NAME', 'Hey Hey Cafe')
    CAFE_LOCATION = os.getenv('CAFE_LOCATION', 'Muscat, Oman')
    VOUCHER_REWARD = os.getenv('VOUCHER_REWARD', 'FREE Drink')
    VOUCHER_VALUE = os.getenv('VOUCHER_VALUE', '$15')
    
    # Voucher settings - Easily configurable
    VOUCHER_VALIDITY_HOURS = int(os.getenv('VOUCHER_VALIDITY_HOURS', 24))
    VOUCHER_VALIDITY_DAYS = int(os.getenv('VOUCHER_VALIDITY_DAYS', 1))  # Alternative to hours
    VOUCHER_EXPIRY_MODE = os.getenv('VOUCHER_EXPIRY_MODE', 'hours').lower()  # 'hours' or 'days'
    
    # Data files (absolute paths to ensure they work from any directory)
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    EMPLOYEES_CSV = os.path.join(PROJECT_ROOT, 'data', 'employees.csv')
    VOUCHER_HISTORY_CSV = os.path.join(PROJECT_ROOT, 'data', 'voucher_history.csv')
    QRCODES_DIR = os.path.join(PROJECT_ROOT, 'data', 'qrcodes')
    
    # WhatsApp settings
    MESSAGING_SERVICE = os.getenv('MESSAGING_SERVICE', 'ultramsg').lower()
    ULTRAMSG_INSTANCE_ID = os.getenv('ULTRAMSG_INSTANCE_ID', '')
    ULTRAMSG_TOKEN = os.getenv('ULTRAMSG_TOKEN', '')
    TEXTMEBOT_KEY = os.getenv('TEXTMEBOT_KEY', '')
    
    # Automatic messaging settings
    AUTO_MESSAGING_ENABLED = os.getenv('AUTO_MESSAGING_ENABLED', 'True').lower() == 'true'
    AUTO_MESSAGING_TIME = os.getenv('AUTO_MESSAGING_TIME', '09:00')  # HH:MM format
    AUTO_MESSAGING_TIMEZONE = os.getenv('AUTO_MESSAGING_TIMEZONE', 'Asia/Muscat')
    
    # Message formatting
    BIRTHDAY_MESSAGE_TEMPLATE = os.getenv('BIRTHDAY_MESSAGE_TEMPLATE', 
        'Happy Birthday {employee_name}!\n\n'
        'From all of us at {cafe_name}, we hope you have a wonderful day! '
        'As a special birthday treat, here\'s a voucher for a {voucher_reward} worth {voucher_value}.\n\n'
        'Location: {cafe_location}\n'
        'Valid for: {validity_period}\n\n'
        'Enjoy your special day!')
    
    # Server settings
    HOST = '0.0.0.0'
    PORT = int(os.getenv('PORT', 5000))
    CAFE_PORT = int(os.getenv('CAFE_PORT', 5001))
    ADMIN_PORT = int(os.getenv('ADMIN_PORT', 5002))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    @classmethod
    def get_voucher_validity_hours(cls):
        """Get voucher validity in hours based on configuration"""
        if cls.VOUCHER_EXPIRY_MODE == 'days':
            return cls.VOUCHER_VALIDITY_DAYS * 24
        else:
            return cls.VOUCHER_VALIDITY_HOURS
    
    @classmethod
    def get_validity_period_text(cls):
        """Get human-readable validity period"""
        if cls.VOUCHER_EXPIRY_MODE == 'days':
            if cls.VOUCHER_VALIDITY_DAYS == 1:
                return "24 hours"
            else:
                return f"{cls.VOUCHER_VALIDITY_DAYS} days"
        else:
            if cls.VOUCHER_VALIDITY_HOURS == 24:
                return "24 hours"
            elif cls.VOUCHER_VALIDITY_HOURS < 24:
                return f"{cls.VOUCHER_VALIDITY_HOURS} hours"
            else:
                days = cls.VOUCHER_VALIDITY_HOURS // 24
                hours = cls.VOUCHER_VALIDITY_HOURS % 24
                if hours == 0:
                    return f"{days} days"
                else:
                    return f"{days} days and {hours} hours"
