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
    VOUCHER_VALIDITY_HOURS = int(os.getenv('VOUCHER_VALIDITY_HOURS', 24))
    
    # Data files
    EMPLOYEES_CSV = 'data/employees.csv'
    VOUCHER_HISTORY_CSV = 'data/voucher_history.csv'
    
    # WhatsApp settings
    MESSAGING_SERVICE = os.getenv('MESSAGING_SERVICE', 'ultramsg').lower()
    ULTRAMSG_INSTANCE_ID = os.getenv('ULTRAMSG_INSTANCE_ID', '')
    ULTRAMSG_TOKEN = os.getenv('ULTRAMSG_TOKEN', '')
    
    # Server settings
    HOST = '0.0.0.0'
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
