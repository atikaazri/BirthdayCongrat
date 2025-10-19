"""
Loads settings from .env file with validation and defaults
"""
import os
from dotenv import load_dotenv
from datetime import time
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class Config:
    """Master configuration class"""
    
    # ============= MESSAGING SERVICE =============
    MESSAGING_SERVICE = os.getenv('MESSAGING_SERVICE', 'ultramsg').lower()
    
    # Twilio Settings
    TWILIO_SID = os.getenv('TWILIO_SID')
    TWILIO_AUTH = os.getenv('TWILIO_AUTH')
    TWILIO_PHONE = os.getenv('TWILIO_PHONE')
    
    # UltraMsg Settings
    ULTRAMSG_INSTANCE_ID = os.getenv('ULTRAMSG_INSTANCE_ID')
    ULTRAMSG_TOKEN = os.getenv('ULTRAMSG_TOKEN')
    ULTRAMSG_API_URL = "https://api.ultramsg.com"
    
    # ============= SERVER PORTS =============
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FASTAPI_PORT = int(os.getenv('FASTAPI_PORT', 8000))
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    # ============= CAFE CUSTOMIZATION =============
    CAFE_NAME = os.getenv('CAFE_NAME', 'Hey Hey Cafe')
    CAFE_LOCATION = os.getenv('CAFE_LOCATION', 'Dubai, UAE')
    CAFE_PHONE = os.getenv('CAFE_PHONE', '+971-4-XXXX-XXXX')
    CAFE_EMAIL = os.getenv('CAFE_EMAIL', 'info@heyheycafe.com')
    CAFE_WEBSITE = os.getenv('CAFE_WEBSITE', 'www.heyheycafe.com')
    CAFE_LOGO_URL = os.getenv('CAFE_LOGO_URL', 'https://via.placeholder.com/200')
    CAFE_TIMEZONE = os.getenv('CAFE_TIMEZONE', 'Asia/Dubai')
    
    # ============= VOUCHER SETTINGS =============
    VOUCHER_VALIDITY_HOURS = int(os.getenv('VOUCHER_VALIDITY_HOURS', 24))
    VOUCHER_REWARD = os.getenv('VOUCHER_REWARD', 'FREE Drink')
    VOUCHER_VALUE = os.getenv('VOUCHER_VALUE', '$15')
    
    # ============= BIRTHDAY MESSAGE SCHEDULING =============
    BIRTHDAY_MESSAGE_ENABLED = os.getenv('BIRTHDAY_MESSAGE_ENABLED', 'True').lower() == 'true'
    BIRTHDAY_MESSAGE_HOUR = int(os.getenv('BIRTHDAY_MESSAGE_HOUR', 13))
    BIRTHDAY_MESSAGE_MINUTE = int(os.getenv('BIRTHDAY_MESSAGE_MINUTE', 30))
    
    # Validate hour and minute
    if not (0 <= BIRTHDAY_MESSAGE_HOUR <= 23):
        logger.warning(f"Invalid BIRTHDAY_MESSAGE_HOUR: {BIRTHDAY_MESSAGE_HOUR}. Defaulting to 7")
        BIRTHDAY_MESSAGE_HOUR = 7
    if not (0 <= BIRTHDAY_MESSAGE_MINUTE <= 59):
        logger.warning(f"Invalid BIRTHDAY_MESSAGE_MINUTE: {BIRTHDAY_MESSAGE_MINUTE}. Defaulting to 0")
        BIRTHDAY_MESSAGE_MINUTE = 0
    
    BIRTHDAY_SEND_TIME = time(BIRTHDAY_MESSAGE_HOUR, BIRTHDAY_MESSAGE_MINUTE)
    
    # ============= MESSAGE TEMPLATES =============
    # Message variables available: {cafe_name}, {employee_name}, {voucher_reward}, 
    # {voucher_value}, {validity_hours}, {cafe_location}, {cafe_phone}
    
    BIRTHDAY_MESSAGE_TEMPLATE = '{emoji} Happy Birthday {employee_name}! 🎂\n\nEnjoy a {voucher_reward} at {cafe_name}!\nValue: {voucher_value}\nVoucher valid for {validity_hours} hours.\n\nVoucher Code: {voucher_code}\n\nShow this QR code or use the code above to redeem your gift!\nThank you for being awesome! 🎉'
    
    BIRTHDAY_NOTIFICATION_ENABLED = os.getenv('BIRTHDAY_NOTIFICATION_ENABLED', 'True').lower() == 'true'
    BIRTHDAY_NOTIFICATION_MESSAGE = os.getenv(
        'BIRTHDAY_NOTIFICATION_MESSAGE',
        '🎉 Birthday wish sent to {employee_name} ({phone_number})'
    )
    
    # ============= BRANDING =============
    BRAND_COLOR_PRIMARY = os.getenv('BRAND_COLOR_PRIMARY', '#4CAF50')
    BRAND_COLOR_SECONDARY = os.getenv('BRAND_COLOR_SECONDARY', '#45a049')
    BRAND_EMOJI = os.getenv('BRAND_EMOJI', '☕')
    
    # ============= FEATURES =============
    ENABLE_QR_CODE_GENERATION = os.getenv('ENABLE_QR_CODE_GENERATION', 'True').lower() == 'true'
    ENABLE_FLASK_UI = os.getenv('ENABLE_FLASK_UI', 'True').lower() == 'true'
    ENABLE_FASTAPI = os.getenv('ENABLE_FASTAPI', 'True').lower() == 'true'
    ENABLE_WHATSAPP_SENDING = os.getenv('ENABLE_WHATSAPP_SENDING', 'True').lower() == 'true'
    
    # ============= DATA SOURCE CONFIGURATION =============
    # CSV Configuration (easily changeable for future DB connection)
    EMPLOYEES_CSV_FILE = os.getenv('EMPLOYEES_CSV_FILE', 'employees.csv')
    VOUCHER_HISTORY_CSV_FILE = os.getenv('VOUCHER_HISTORY_CSV_FILE', 'voucher_history.csv')
    
    # CSV Column names (easily changeable for different CSV formats)
    CSV_COLUMNS = {
        'employee_id': os.getenv('CSV_COLUMN_EMPLOYEE_ID', 'employee_id'),
        'employee_name': os.getenv('CSV_COLUMN_EMPLOYEE_NAME', 'employee_name'),
        'phone_number': os.getenv('CSV_COLUMN_PHONE_NUMBER', 'phone_number'),
        'date_of_birth': os.getenv('CSV_COLUMN_DATE_OF_BIRTH', 'date_of_birth')
    }
    
    # Date format for parsing (easily changeable)
    DATE_FORMAT = os.getenv('DATE_FORMAT', '%Y-%m-%d')
    
    # ============= LOGGING =============
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'birthday_system.log')
    
    @classmethod
    def validate(cls):
        """Validate critical configuration"""
        errors = []
        
        if cls.MESSAGING_SERVICE not in ['twilio', 'ultramsg']:
            errors.append(f"Invalid MESSAGING_SERVICE: {cls.MESSAGING_SERVICE}. Must be 'twilio' or 'ultramsg'")
        
        if cls.MESSAGING_SERVICE == 'twilio':
            if not all([cls.TWILIO_SID, cls.TWILIO_AUTH, cls.TWILIO_PHONE]):
                errors.append("Twilio credentials missing (TWILIO_SID, TWILIO_AUTH, TWILIO_PHONE)")
        
        elif cls.MESSAGING_SERVICE == 'ultramsg':
            if not all([cls.ULTRAMSG_INSTANCE_ID, cls.ULTRAMSG_TOKEN]):
                errors.append("UltraMsg credentials missing (ULTRAMSG_INSTANCE_ID, ULTRAMSG_TOKEN)")
        
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return False
        
        logger.info("✓ Configuration validated successfully")
        return True
    
    @classmethod
    def get_birthday_message(cls, employee_name, phone_number=None, voucher_code=None):
        """Generate birthday message with variable substitution"""
        message = cls.BIRTHDAY_MESSAGE_TEMPLATE.format(
            emoji=cls.BRAND_EMOJI,
            employee_name=employee_name,
            voucher_reward=cls.VOUCHER_REWARD,
            voucher_value=cls.VOUCHER_VALUE,
            validity_hours=cls.VOUCHER_VALIDITY_HOURS,
            cafe_name=cls.CAFE_NAME,
            cafe_location=cls.CAFE_LOCATION,
            cafe_phone=cls.CAFE_PHONE,
            phone_number=phone_number or 'N/A',
            voucher_code=voucher_code or 'N/A'
        )
        return message
    
    @classmethod
    def get_notification_message(cls, employee_name, phone_number):
        """Generate notification message"""
        message = cls.BIRTHDAY_NOTIFICATION_MESSAGE.format(
            employee_name=employee_name,
            phone_number=phone_number,
            cafe_name=cls.CAFE_NAME
        )
        return message
    
    @classmethod
    def summary(cls):
        """Print configuration summary"""
        print("\n" + "="*60)
        print("  BIRTHDAY VOUCHER SYSTEM - CONFIGURATION SUMMARY")
        print("="*60)
        print(f"\nMessaging Service: {cls.MESSAGING_SERVICE.upper()}")
        print(f"Cafe: {cls.CAFE_NAME} ({cls.CAFE_LOCATION})")
        print(f"Voucher: {cls.VOUCHER_REWARD} - {cls.VOUCHER_VALUE}")
        print(f"Validity: {cls.VOUCHER_VALIDITY_HOURS} hours")
        print(f"Birthday Send Time: {cls.BIRTHDAY_SEND_TIME.strftime('%H:%M')} ({cls.CAFE_TIMEZONE})")
        print(f"Brand Color: {cls.BRAND_COLOR_PRIMARY}")
        print(f"Debug Mode: {cls.DEBUG_MODE}")
        print(f"Servers: Flask:{cls.FLASK_PORT} | FastAPI:{cls.FASTAPI_PORT}")
        print("\n" + "="*60 + "\n")
    
    @classmethod
    def to_dict(cls):
        """Convert config to dictionary"""
        return {
            'messaging_service': cls.MESSAGING_SERVICE,
            'cafe_name': cls.CAFE_NAME,
            'cafe_location': cls.CAFE_LOCATION,
            'voucher_reward': cls.VOUCHER_REWARD,
            'voucher_value': cls.VOUCHER_VALUE,
            'voucher_validity_hours': cls.VOUCHER_VALIDITY_HOURS,
            'birthday_send_time': cls.BIRTHDAY_SEND_TIME.isoformat(),
            'timezone': cls.CAFE_TIMEZONE,
            'brand_emoji': cls.BRAND_EMOJI,
            'brand_color_primary': cls.BRAND_COLOR_PRIMARY,
            'brand_color_secondary': cls.BRAND_COLOR_SECONDARY,
        }


# Initialize config validation
Config.validate()
Config.summary()