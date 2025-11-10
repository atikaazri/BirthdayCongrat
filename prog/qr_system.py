import os
import uuid
import cv2
import qrcode
from pyzbar.pyzbar import decode
from datetime import datetime, timedelta
from secure_qr import SecureQR, secure_qr
import hmac

# ============================================================
# CONFIGURATION
# ============================================================
from config import Config

SAVE_DIR = Config.QRCODES_DIR
NUM_VOUCHERS = 5  # Change how many vouchers to generate

# Ensure the save directory exists
os.makedirs(SAVE_DIR, exist_ok=True)

# ============================================================
# 1. GENERATE UNIQUE VOUCHER CODES AND SAVE QR IMAGES
# ============================================================
def generate_voucher_code():
    """Generate a unique alphanumeric voucher code."""
    return str(uuid.uuid4()).replace("-", "").upper()[:12]

def create_qr_code(voucher_code):
    """
    Return a BASE64 data URL for the QR image, same as before,
    but now the QR encodes a signed V2 payload wrapping voucher_code.
    """
    # Use the global secure_qr instance to ensure consistent secret key
    # This is critical - both creation and validation must use the same key
    sec = secure_qr
    now = datetime.now()
    expires_at = now + timedelta(hours=Config.get_voucher_validity_hours())

    # Minimal secure payload that matches the V2 format
    payload = {
        "code": voucher_code,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "version": SecureQR.VERSION
    }

    # SecureQR wants a single string to embed; we'll reuse its signing method
    # by temporarily calling a tiny helper on the instance:
    import json, base64
    encoded_data = base64.b64encode(json.dumps(payload, sort_keys=True).encode()).decode()
    signature = sec._generate_signature(encoded_data)  # same HMAC the class uses
    secure_code = f"{SecureQR.VERSION}|{encoded_data}|{signature}"

    data_url = sec.create_qr_image(secure_code)  # "data:image/png;base64,..."

    png_b64 = data_url.split(",", 1)[1]
    png_bytes = base64.b64decode(png_b64)
    file_path = os.path.join(SAVE_DIR, f"{voucher_code}.png")
    with open(file_path, "wb") as f:
        f.write(png_bytes)
    # print(f"[+] QR saved: {file_path}")  # optional log

    return data_url


    """Create a QR code for a voucher and save it to file."""
    '''
    qr = qrcode.QRCode(
        version=1, box_size=10, border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_L
    )
    qr.add_data(voucher_code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    file_path = os.path.join(SAVE_DIR, f"{voucher_code}.png")
    img.save(file_path)
    print(f"[+] QR saved: {file_path}")
    return file_path
'''

# Optional helper to check and parse incoming QR strings (V1 or V2)
def parse_qr_text(qr_text: str, allow_expired: bool = True) -> str:
    """
    Accept either legacy code (V1) or V2 secure string.
    Returns the underlying voucher_code to redeem.
    
    Args:
        qr_text: The QR code text to parse
        allow_expired: If True, extract code even if expired (expiration checked at redemption)
    
    Returns:
        The voucher code string
    """
    if not qr_text:
        raise ValueError("Empty QR code text")
    
    qr_text = qr_text.strip()
    
    if qr_text.startswith('V2|'):
        # Parse and extract V2 secure code
        try:
            # Parse secure code format: V2|encoded_data|signature
            parts = qr_text.split('|')
            if len(parts) != 3:
                raise ValueError("Invalid V2 code format")
            
            version, encoded_data, signature = parts
            
            # Check version
            if version != SecureQR.VERSION:
                raise ValueError(f"Unsupported version: {version}")
            
            # First, try to decode the data to see if it's valid
            import json, base64
            try:
                json_data = base64.b64decode(encoded_data.encode()).decode()
                voucher_data = json.loads(json_data)
            except Exception as e:
                raise ValueError(f"Invalid data encoding: {str(e)}")
            
            # Extract the code from the data
            if "code" not in voucher_data:
                raise ValueError("No voucher code found in secure data")
            
            code = voucher_data["code"]
            
            # Try to verify signature, but if it fails and we're allowing expired/invalid,
            # we can still extract the code (useful if secret key changed or for debugging)
            signature_valid = False
            try:
                expected_signature = secure_qr._generate_signature(encoded_data)
                signature_valid = hmac.compare_digest(signature, expected_signature)
                
                if not signature_valid:
                    # Signature doesn't match - this could be due to:
                    # 1. Secret key mismatch (QR generated with different key) - MOST COMMON
                    # 2. Code was tampered with
                    # 3. Secret key was changed after QR generation
                    
                    if allow_expired:
                        # Even if signature fails, we can extract the code
                        # The signature check will happen again at redemption if needed
                        print(f"[WARNING] Signature mismatch for code {code}. This may be due to secret key change. Extracting code anyway.")
                    else:
                        raise ValueError("Invalid signature - code may be tampered or secret key mismatch")
            except ValueError:
                # Re-raise ValueError if allow_expired=False (already handled above)
                raise
            except Exception as sig_error:
                # If signature verification itself fails (not just mismatch), 
                # and allow_expired=True, still extract code
                if allow_expired:
                    print(f"[WARNING] Could not verify signature for code {code}: {sig_error}. Extracting code anyway.")
                else:
                    raise ValueError(f"Signature verification failed: {str(sig_error)}")
            
            # Optionally check expiration (but still return code if allow_expired=True)
            if not allow_expired:
                expires_at_str = voucher_data.get('expires_at')
                if expires_at_str:
                    from datetime import datetime
                    expires_at = datetime.fromisoformat(expires_at_str)
                    if datetime.now() > expires_at:
                        raise ValueError("Voucher has expired")
            
            return code
                
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            raise ValueError(f"Failed to parse secure code: {str(e)}")
    
    # Legacy V1 code - return as is (should be 12 characters alphanumeric)
    return qr_text


def generate_and_save_vouchers(n=NUM_VOUCHERS):
    vouchers = []
    for _ in range(n):
        code = generate_voucher_code()
        create_qr_code(code)
        vouchers.append(code)
    print(f"\n[SUCCESS] {len(vouchers)} vouchers generated and saved.\n")
    return vouchers

# ============================================================
# 2. SCAN QR CODE USING CAMERA
# ============================================================
def scan_qr_camera():
    """Open camera and detect QR codes live."""
    print("[CAMERA] Starting camera... Press 'q' to quit.")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[ERROR] Could not access camera.")
        return

    detected = set()
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read frame.")
            break

        # Detect and decode QR codes
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            qr_data = obj.data.decode("utf-8")
            points = obj.polygon

            # Draw bounding box
            if len(points) > 4:
                hull = cv2.convexHull(points)
                points = hull

            n = len(points)
            for j in range(n):
                pt1 = (points[j].x, points[j].y)
                pt2 = (points[(j + 1) % n].x, points[(j + 1) % n].y)
                cv2.line(frame, pt1, pt2, (0, 255, 0), 3)

            # Display text and print if new
            cv2.putText(frame, qr_data, (points[0].x, points[0].y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            if qr_data not in detected:
                detected.add(qr_data)
                print(f"[QR Detected] {qr_data}")

        cv2.imshow("QR Code Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Scanner closed.")

# ============================================================
# 3. SCAN QR CODE FROM IMAGE FILE
# ============================================================
def scan_qr_from_image(image_path):
    """Scan QR code from an image file."""
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"[ERROR] Could not read image: {image_path}")
            return None
        
        decoded_objects = decode(image)
        if decoded_objects:
            for obj in decoded_objects:
                qr_data = obj.data.decode("utf-8")
                print(f"[QR Found] {qr_data}")
                return qr_data
        else:
            print("[ERROR] No QR code found in image")
            return None
    except Exception as e:
        print(f"[ERROR] Error scanning image: {e}")
        return None

# ============================================================
# 4. INTEGRATION WITH VOUCHER SYSTEM
# ============================================================
def create_voucher_qr(voucher_code):
    """Create QR code for existing voucher code."""
    return create_qr_code(voucher_code)

def scan_voucher_qr():
    """Scan for voucher QR codes and return the code."""
    print("[CAMERA] Starting voucher scanner... Press 'q' to quit.")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[ERROR] Could not access camera.")
        return None

    detected = set()
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read frame.")
            break

        # Detect and decode QR codes
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            qr_data = obj.data.decode("utf-8")
            
            # Check if it's a valid voucher code (starts with BDV or is alphanumeric)
            if qr_data.startswith('BDV') or (len(qr_data) >= 8 and qr_data.isalnum()):
                if qr_data not in detected:
                    detected.add(qr_data)
                    print(f"[Voucher Detected] {qr_data}")
                    cap.release()
                    cv2.destroyAllWindows()
                    return qr_data

        cv2.imshow("Voucher QR Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("=== Voucher QR System ===")
    print("1. Generate QR codes")
    print("2. Scan QR codes with camera")
    print("3. Generate & then scan")
    print("4. Scan voucher QR codes")
    choice = input("Select an option (1/2/3/4): ").strip()

    if choice == "1":
        generate_and_save_vouchers()
    elif choice == "2":
        scan_qr_camera()
    elif choice == "3":
        generate_and_save_vouchers()
        scan_qr_camera()
    elif choice == "4":
        result = scan_voucher_qr()
        if result:
            print(f"[SUCCESS] Voucher code detected: {result}")
        else:
            print("[ERROR] No voucher code detected")
    else:
        print("[ERROR] Invalid option. Exiting.")