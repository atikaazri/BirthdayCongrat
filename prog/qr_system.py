import os
import uuid
import cv2
import qrcode
from pyzbar.pyzbar import decode

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
    """Create a QR code for a voucher and save it to file."""
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