#!/usr/bin/env python3
"""
WhatsApp messaging service for BDVoucher
"""
import requests
from config import Config

def send_whatsapp_message(phone, employee_name, voucher_code, custom_message=None):
    """Send WhatsApp message with optional custom message"""
    try:
        if custom_message:
            message_text = custom_message
        else:
            message_text = f"Happy Birthday {employee_name}!\n\nEnjoy a {Config.VOUCHER_REWARD} at {Config.CAFE_NAME}!\nValue: {Config.VOUCHER_VALUE}\nVoucher Code: {voucher_code}\n\nShow this QR code to redeem your gift!"
        
        if Config.MESSAGING_SERVICE == 'ultramsg' and Config.ULTRAMSG_INSTANCE_ID and Config.ULTRAMSG_TOKEN:
            # Generate QR code
            from database import generate_qr_code
            qr_image = generate_qr_code(voucher_code)
            
            url = f"https://api.ultramsg.com/{Config.ULTRAMSG_INSTANCE_ID}/messages/image"
            payload = {
                "to": phone,
                "image": qr_image,
                "caption": message_text,
                "token": Config.ULTRAMSG_TOKEN
            }
            
            response = requests.post(url, data=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('sent'):
                    return True
                else:
                    print(f"UltraMsg error: {result.get('error', 'Unknown error')}")
            else:
                print(f"UltraMsg API error: {response.status_code}")
        
        return False
        
    except Exception as e:
        print(f"Error sending message: {e}")
        return False
