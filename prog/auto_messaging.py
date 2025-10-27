#!/usr/bin/env python3
"""
BDVoucher - Automatic Birthday Messaging Scheduler
Runs in background to send birthday messages at configured time
"""
import schedule
import time
import threading
from datetime import datetime
import pytz
from config import Config
from database import get_birthday_today, create_voucher, generate_qr_code
from whatsapp_service import send_whatsapp_message


class AutoMessagingScheduler:
    """Automatic birthday messaging scheduler"""
    
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        
    def send_birthday_messages(self):
        """Send birthday messages to employees with birthdays today"""
        try:
            now = datetime.now(pytz.timezone(Config.AUTO_MESSAGING_TIMEZONE))
            print(f"[AUTO-MSG] Checking for birthdays at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Get employees with birthdays today
            birthdays = get_birthday_today()
            
            if not birthdays:
                print("[AUTO-MSG] No birthdays today")
                return
            
            print(f"[AUTO-MSG] Found {len(birthdays)} birthdays today")
            
            for i, employee in enumerate(birthdays, start=1):
                try:
                    print(f"\n[AUTO-MSG] Processing {i}/{len(birthdays)}: {employee['employee_name']}")

                    # Create voucher
                    voucher_code = create_voucher(employee['employee_id'], employee['employee_name'])
                    print(f"[AUTO-MSG] Created voucher {voucher_code} for {employee['employee_name']}")
                    
                    # Generate QR code
                    qr_code = generate_qr_code(voucher_code)
                    print(f"[AUTO-MSG] Generated QR code for {employee['employee_name']}")
                    
                    # Format message
                    message = self.format_birthday_message(employee, voucher_code)
                    
                    # Send WhatsApp message
                    success = send_whatsapp_message(
                        employee['phone_number'],
                        employee['employee_name'],
                        voucher_code,
                        custom_message=message
                    )
                    
                    if success:
                        print(f"[AUTO-MSG ✅] Birthday message sent to {employee['employee_name']}")
                    else:
                        print(f"[AUTO-MSG ⚠️] Failed to send message to {employee['employee_name']}")
                    
                    # Add a 10-second delay only for TextMeBot
                    if Config.MESSAGING_SERVICE.lower() == 'textmebot':
                        print("[AUTO-MSG] Waiting 10 seconds before sending the next message...")
                        time.sleep(10)
                        
                except Exception as e:
                    print(f"[AUTO-MSG ❌] Error processing {employee['employee_name']}: {e}")
                    
        except Exception as e:
            print(f"[AUTO-MSG ❌] Error in birthday messaging: {e}")
    
    def format_birthday_message(self, employee, voucher_code):
        """Format birthday message using template"""
        try:
            message = Config.BIRTHDAY_MESSAGE_TEMPLATE.format(
                employee_name=employee['employee_name'],
                cafe_name=Config.CAFE_NAME,
                cafe_location=Config.CAFE_LOCATION,
                voucher_reward=Config.VOUCHER_REWARD,
                voucher_value=Config.VOUCHER_VALUE,
                validity_period=Config.get_validity_period_text()
            )
            return message
        except Exception as e:
            print(f"[AUTO-MSG] Error formatting message: {e}")
            # Fallback
            return f"Happy Birthday {employee['employee_name']}! Here's your voucher: {voucher_code}"
    
    def schedule_messages(self):
        """Schedule birthday messages at configured time"""
        if not Config.AUTO_MESSAGING_ENABLED:
            print("[AUTO-MSG] Automatic messaging is disabled")
            return
            
        try:
            hour, minute = map(int, Config.AUTO_MESSAGING_TIME.split(':'))
        except ValueError:
            print(f"[AUTO-MSG] Invalid time format: {Config.AUTO_MESSAGING_TIME}")
            return
            
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.send_birthday_messages)
        print(f"[AUTO-MSG] Scheduled birthday messages for {Config.AUTO_MESSAGING_TIME} {Config.AUTO_MESSAGING_TIMEZONE}")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)
    
    def start(self):
        """Start the automatic messaging scheduler"""
        if not Config.AUTO_MESSAGING_ENABLED:
            print("[AUTO-MSG] Automatic messaging is disabled in config")
            return
            
        if self.running:
            print("[AUTO-MSG] Scheduler already running")
            return
            
        self.running = True
        self.scheduler_thread = threading.Thread(target=self.schedule_messages, daemon=True)
        self.scheduler_thread.start()
        print("[AUTO-MSG] Automatic messaging scheduler started")
    
    def stop(self):
        """Stop the automatic messaging scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("[AUTO-MSG] Automatic messaging scheduler stopped")
    
    def test_messaging(self):
        """Run test immediately"""
        print("[AUTO-MSG] Running test messaging...")
        self.send_birthday_messages()


# Global scheduler instance
auto_scheduler = AutoMessagingScheduler()


def start_auto_messaging():
    """Start automatic messaging (called from main app)"""
    auto_scheduler.start()


def stop_auto_messaging():
    """Stop automatic messaging"""
    auto_scheduler.stop()


def test_auto_messaging():
    """Test automatic messaging immediately"""
    auto_scheduler.test_messaging()


if __name__ == "__main__":
    print("Testing automatic messaging system...")
    test_auto_messaging()
