"""
Birthday automation - runs independently
Usage: python send_birthday.py <path_to_csv>
"""
import csv
import io
import base64
import qrcode
from datetime import datetime
from twilio.rest import Client
from config import Config
from vouchers import create_voucher
import sys


def load_employees(csv_file=None):
    """Load employee data from CSV using configurable file name"""
    from config import Config
    
    if csv_file is None:
        csv_file = Config.EMPLOYEES_CSV_FILE
    
    employees = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            employees.append(row)
    return employees


def get_birthday_today(employees):
    """Filter employees with birthday today (check day and month only, not year)"""
    today = datetime.now()
    birthdays = []
    
    for emp in employees:
        # Parse date using configurable format
        from config import Config
        dob = datetime.strptime(emp[Config.CSV_COLUMNS['date_of_birth']], Config.DATE_FORMAT)
        
        # Check only month and day, ignore year
        if dob.month == today.month and dob.day == today.day:
            birthdays.append(emp)
    
    return birthdays


def generate_qr_code(voucher_code):
    """Generate QR code and return base64 image"""
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(voucher_code)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"


def send_whatsapp_message(phone, employee_name, qr_image_url, voucher_code):
    """Send WhatsApp birthday message with QR code and voucher code"""
    try:
        from config import Config
        import requests
        
        message_text = Config.get_birthday_message(employee_name, phone, voucher_code)
        
        if Config.MESSAGING_SERVICE == 'ultramsg':
            # UltraMsg API
            url = f"https://api.ultramsg.com/{Config.ULTRAMSG_INSTANCE_ID}/messages/image"
            payload = {
                "to": phone,
                "image": qr_image_url,
                "caption": message_text,
                "token": Config.ULTRAMSG_TOKEN
            }
            
            response = requests.post(url, data=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('sent'):
                    print(f"✓ Message sent via UltraMsg to {phone}")
                    if Config.BIRTHDAY_NOTIFICATION_ENABLED:
                        notification = Config.get_notification_message(employee_name, phone)
                        print(f"  {notification}")
                    return True
                else:
                    print(f"✗ UltraMsg error: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"✗ UltraMsg API error: {response.status_code} - {response.text}")
                return False
        
        elif Config.MESSAGING_SERVICE == 'twilio':
            # Twilio API
            from twilio.rest import Client
            client = Client(Config.TWILIO_SID, Config.TWILIO_AUTH)
            message = client.messages.create(
                from_=f"whatsapp:{Config.TWILIO_PHONE}",
                to=f"whatsapp:{phone}",
                body=message_text,
                media_url=[qr_image_url]
            )
            print(f"✓ Message sent via Twilio to {phone} (SID: {message.sid})")
            if Config.BIRTHDAY_NOTIFICATION_ENABLED:
                notification = Config.get_notification_message(employee_name, phone)
                print(f"  {notification}")
            return True
        
        else:
            print(f"✗ Unsupported messaging service: {Config.MESSAGING_SERVICE}")
            print("Available options: 'ultramsg' or 'twilio'")
            return False
    
    except Exception as e:
        print(f"✗ Failed to send message: {e}")
        return False


def send_birthday_wishes(csv_file=None):
    """Main automation function"""
    employees = load_employees(csv_file)
    birthdays = get_birthday_today(employees)
    
    if not birthdays:
        print("No birthdays today!")
        return
    
    print(f"Found {len(birthdays)} birthday(ies) today!\n")
    
    for emp in birthdays:
        # Use configurable column names
        phone = emp[Config.CSV_COLUMNS['phone_number']]
        name = emp[Config.CSV_COLUMNS['employee_name']]
        emp_id = emp.get(Config.CSV_COLUMNS['employee_id'], emp[Config.CSV_COLUMNS['employee_name']])
        
        # Generate QR code first
        qr_image = generate_qr_code(f"{emp_id}_{datetime.now().strftime('%Y%m%d')}")
        
        # Create voucher with QR code data
        voucher_code = create_voucher(emp_id, name, qr_image)
        
        send_whatsapp_message(phone, name, qr_image, voucher_code)
        print(f"  - {name} ({phone}): Voucher {voucher_code}\n")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        send_birthday_wishes(sys.argv[1])
    else:
        # Use default configurable file name
        send_birthday_wishes()
