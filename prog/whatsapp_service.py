#!/usr/bin/env python3
"""
WhatsApp messaging service for BDVoucher
"""
import time
import requests
import urllib.parse
from config import Config

def send_whatsapp_message(phone, employee_name, voucher_code, custom_message=None):
    """Send WhatsApp message with optional custom message"""
    try:
        message_text = custom_message or (
            f"🎉 Happy Birthday {employee_name}!\n\n"
            f"Enjoy a {Config.VOUCHER_REWARD} at {Config.CAFE_NAME}!\n"
            f"Value: {Config.VOUCHER_VALUE}\nVoucher Code: {voucher_code}\n\n"
            f"Show this code to redeem your gift!"
        )

        if Config.MESSAGING_SERVICE == 'textmebot' and Config.TEXTMEBOT_KEY:
            encoded_text = urllib.parse.quote_plus(message_text)
            url = (
                f"https://api.textmebot.com/send.php"
                f"?recipient={phone}"
                f"&apikey={Config.TEXTMEBOT_KEY}"
                f"&text={encoded_text}"
            )

            response = requests.get(url)
            if response.status_code == 200:
                if "success" in response.text.lower():
                    print("✅ Message sent successfully via TextMeBot.")
                    return True
                else:
                    print(f"⚠️ TextMeBot response: {response.text}")
            else:
                print(f"❌ TextMeBot API error: {response.status_code}")
            time.sleep(10)

        # fallback to UltraMsg for image support
        elif Config.MESSAGING_SERVICE == 'ultramsg':
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
                if result.get("sent"):
                    return True
                else:
                    print(f"UltraMsg error: {result.get('error', 'Unknown error')}")
            else:
                print(f"UltraMsg API error: {response.status_code}")

        return False

    except Exception as e:
        print(f"💥 Error sending message: {e}")
        return False

