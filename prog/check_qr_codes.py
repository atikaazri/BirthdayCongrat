#!/usr/bin/env python3
"""
QR Code Verification Tool
Check if QR codes have been generated and verify their status
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from config import Config
from database import get_all_vouchers, get_voucher_history, refresh_data
from qr_system import scan_qr_from_image
import cv2
from pyzbar.pyzbar import decode

def check_qr_directory():
    """Check QR code directory and list all QR code files"""
    qr_dir = Config.QRCODES_DIR
    
    print("=" * 60)
    print("QR CODE DIRECTORY CHECK")
    print("=" * 60)
    print(f"Directory: {qr_dir}")
    print(f"Exists: {os.path.exists(qr_dir)}")
    print()
    
    if not os.path.exists(qr_dir):
        print("[ERROR] QR code directory does not exist!")
        return []
    
    # Get all PNG files
    qr_files = list(Path(qr_dir).glob("*.png"))
    
    print(f"Found {len(qr_files)} QR code file(s)")
    print()
    
    if qr_files:
        print("QR Code Files:")
        print("-" * 60)
        for i, qr_file in enumerate(qr_files, 1):
            # Extract voucher code from filename
            voucher_code = qr_file.stem
            file_size = qr_file.stat().st_size
            modified = datetime.fromtimestamp(qr_file.stat().st_mtime)
            
            print(f"{i}. {voucher_code}")
            print(f"   File: {qr_file.name}")
            print(f"   Size: {file_size:,} bytes ({file_size/1024:.2f} KB)")
            print(f"   Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Verify QR code is readable
            try:
                qr_data = scan_qr_from_image(str(qr_file))
                if qr_data:
                    print(f"   [OK] Valid QR - Contains: {qr_data}")
                else:
                    print(f"   [WARN] QR code exists but cannot be read")
            except Exception as e:
                print(f"   [ERROR] Error reading QR: {e}")
            print()
    else:
        print("[INFO] No QR code files found in directory")
        print()
    
    return qr_files


def check_voucher_history():
    """Check voucher history for created vouchers"""
    print("=" * 60)
    print("VOUCHER HISTORY CHECK")
    print("=" * 60)
    
    refresh_data()
    history = get_voucher_history()
    
    created_vouchers = [h for h in history if h.get('status') == 'created']
    redeemed_vouchers = [h for h in history if h.get('status') == 'redeemed']
    
    print(f"Total History Records: {len(history)}")
    print(f"Created Vouchers: {len(created_vouchers)}")
    print(f"Redeemed Vouchers: {len(redeemed_vouchers)}")
    print()
    
    if created_vouchers:
        print("Recently Created Vouchers:")
        print("-" * 60)
        for voucher in created_vouchers[-10:]:  # Show last 10
            code = voucher.get('voucher_code', 'N/A')
            employee = voucher.get('employee_name', 'N/A')
            timestamp = voucher.get('timestamp', 'N/A')
            
            # Check if QR file exists
            qr_path = os.path.join(Config.QRCODES_DIR, f"{code}.png")
            qr_exists = os.path.exists(qr_path)
            
            status_icon = "[OK]" if qr_exists else "[MISSING]"
            print(f"{status_icon} {code}")
            print(f"   Employee: {employee}")
            print(f"   Created: {timestamp}")
            print(f"   QR File: {'Exists' if qr_exists else 'MISSING'}")
            print()
    else:
        print("[INFO] No vouchers have been created yet")
        print()
    
    return created_vouchers


def check_active_vouchers():
    """Check active vouchers and their QR codes"""
    print("=" * 60)
    print("ACTIVE VOUCHERS CHECK")
    print("=" * 60)
    
    refresh_data()
    all_vouchers = get_all_vouchers()
    
    active_vouchers = {code: v for code, v in all_vouchers.items() if not v.get('redeemed', False)}
    
    print(f"Total Vouchers: {len(all_vouchers)}")
    print(f"Active Vouchers: {len(active_vouchers)}")
    print()
    
    if active_vouchers:
        print("Active Vouchers with QR Status:")
        print("-" * 60)
        for code, voucher in active_vouchers.items():
            employee = voucher.get('employee_name', 'N/A')
            expires_at = voucher.get('expires_at', 'N/A')
            
            # Check QR file
            qr_path = os.path.join(Config.QRCODES_DIR, f"{code}.png")
            qr_exists = os.path.exists(qr_path)
            
            status_icon = "[OK]" if qr_exists else "[MISSING]"
            print(f"{status_icon} {code}")
            print(f"   Employee: {employee}")
            print(f"   Expires: {expires_at}")
            print(f"   QR Code: {'[OK] Generated' if qr_exists else '[MISSING] Not Found'}")
            print()
    else:
        print("[INFO] No active vouchers found")
        print()
    
    return active_vouchers


def verify_qr_code(qr_file_path):
    """Verify a specific QR code file"""
    print("=" * 60)
    print(f"VERIFYING QR CODE: {os.path.basename(qr_file_path)}")
    print("=" * 60)
    
    if not os.path.exists(qr_file_path):
        print(f"[ERROR] File does not exist: {qr_file_path}")
        return False
    
    try:
        # Read and decode QR code
        image = cv2.imread(qr_file_path)
        if image is None:
            print("[ERROR] Cannot read image file")
            return False
        
        decoded_objects = decode(image)
        
        if decoded_objects:
            qr_data = decoded_objects[0].data.decode("utf-8")
            print(f"[OK] QR Code is valid and readable")
            print(f"   Contains: {qr_data}")
            print(f"   Format: {'Secure (V2)' if qr_data.startswith('V2|') else 'Standard (V1)'}")
            return True
        else:
            print("[WARN] QR code file exists but cannot be decoded")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error verifying QR code: {e}")
        return False


def generate_test_qr():
    """Generate a test QR code to verify system is working"""
    print("=" * 60)
    print("GENERATING TEST QR CODE")
    print("=" * 60)
    
    try:
        from qr_system import create_qr_code, generate_voucher_code
        
        test_code = generate_voucher_code()
        print(f"Generated test code: {test_code}")
        
        qr_path = create_qr_code(test_code)
        print(f"[OK] Test QR code created: {qr_path}")
        
        # Verify it
        if verify_qr_code(qr_path):
            print("[OK] Test QR code verification successful!")
            print(f"   You can view it at: {qr_path}")
            return True
        else:
            print("[ERROR] Test QR code verification failed!")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error generating test QR: {e}")
        return False


def summary_report():
    """Generate a summary report"""
    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)
    
    refresh_data()
    
    # Count QR files
    qr_dir = Config.QRCODES_DIR
    qr_files = list(Path(qr_dir).glob("*.png")) if os.path.exists(qr_dir) else []
    
    # Count vouchers
    all_vouchers = get_all_vouchers()
    active_vouchers = {code: v for code, v in all_vouchers.items() if not v.get('redeemed', False)}
    
    # Count history
    history = get_voucher_history()
    created_count = len([h for h in history if h.get('status') == 'created'])
    
    print(f"Statistics:")
    print(f"   QR Code Files: {len(qr_files)}")
    print(f"   Total Vouchers: {len(all_vouchers)}")
    print(f"   Active Vouchers: {len(active_vouchers)}")
    print(f"   Created Vouchers: {created_count}")
    print()
    
    # Check for missing QR codes
    missing_qrs = []
    for code in active_vouchers.keys():
        qr_path = os.path.join(Config.QRCODES_DIR, f"{code}.png")
        if not os.path.exists(qr_path):
            missing_qrs.append(code)
    
    if missing_qrs:
        print(f"[WARN] Warning: {len(missing_qrs)} active vouchers missing QR codes:")
        for code in missing_qrs[:5]:  # Show first 5
            print(f"   - {code}")
        if len(missing_qrs) > 5:
            print(f"   ... and {len(missing_qrs) - 5} more")
    else:
        print("[OK] All active vouchers have QR codes generated")
    
    print()


def main():
    """Main verification function"""
    print("\n" + "=" * 60)
    print("QR CODE VERIFICATION TOOL")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all checks
    qr_files = check_qr_directory()
    print()
    
    created_vouchers = check_voucher_history()
    print()
    
    active_vouchers = check_active_vouchers()
    print()
    
    summary_report()
    
    # Interactive menu
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            print()
            generate_test_qr()
        elif command == 'verify' and len(sys.argv) > 2:
            qr_file = sys.argv[2]
            verify_qr_code(qr_file)
        elif command == 'summary':
            summary_report()
        else:
            print("Usage:")
            print("  python check_qr_codes.py           # Full report")
            print("  python check_qr_codes.py test     # Generate test QR")
            print("  python check_qr_codes.py verify <file>  # Verify specific QR")
            print("  python check_qr_codes.py summary  # Summary only")
    else:
        print("\nTip: Run 'python check_qr_codes.py test' to generate a test QR code")
    
    print()


if __name__ == "__main__":
    main()

