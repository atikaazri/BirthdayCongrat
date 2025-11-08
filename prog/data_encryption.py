#!/usr/bin/env python3
"""
Data Encryption Module
Handles encryption/decryption of sensitive data like phone numbers and API tokens
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# Generate encryption key from environment variable or use default (for development)
ENCRYPTION_KEY_ENV = os.getenv('ENCRYPTION_KEY', '')
ENCRYPTION_PASSWORD = os.getenv('ENCRYPTION_PASSWORD', 'default-password-change-in-production-12345')


def get_encryption_key():
    """Get or generate encryption key using environment variables"""
    if ENCRYPTION_KEY_ENV:
        # If a direct encryption key is provided, use it
        try:
            return base64.urlsafe_b64decode(ENCRYPTION_KEY_ENV.encode())
        except Exception:
            pass

    # Load or derive salt securely from environment
    salt_env = os.getenv('ENCRYPTION_SALT', '')
    if salt_env:
        try:
            salt = base64.urlsafe_b64decode(salt_env.encode())
        except Exception:
            print("Warning: Invalid ENCRYPTION_SALT format, using default salt.")
            salt = b'default_fallback_salt_2024'
    else:
        salt = b'default_fallback_salt_2024'  # only for dev; change in production!

    # Derive key from password and salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_PASSWORD.encode()))
    return key


# Initialize Fernet cipher
_key = get_encryption_key()
_cipher = Fernet(_key)


def encrypt_data(plaintext):
    """Encrypt sensitive data"""
    if not plaintext:
        return ''
    try:
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        encrypted = _cipher.encrypt(plaintext)
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"Encryption error: {e}")
        return plaintext  # Return original if encryption fails


def decrypt_data(ciphertext):
    """Decrypt sensitive data"""
    if not ciphertext:
        return ''
    try:
        # Check if data is already encrypted (base64 encoded)
        if isinstance(ciphertext, str):
            # Try to decode
            encrypted = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
            decrypted = _cipher.decrypt(encrypted)
            return decrypted.decode('utf-8')
    except Exception as e:
        # If decryption fails, might be plaintext (backward compatibility)
        print(f"Decryption error (might be plaintext): {e}")
        return ciphertext
    
    return ciphertext


def encrypt_phone_number(phone):
    """Encrypt phone number"""
    return encrypt_data(phone)


def decrypt_phone_number(encrypted_phone):
    """Decrypt phone number"""
    return decrypt_data(encrypted_phone)


def encrypt_api_token(token):
    """Encrypt API token"""
    return encrypt_data(token)


def decrypt_api_token(encrypted_token):
    """Decrypt API token"""
    return decrypt_data(encrypted_token)


def mask_phone_number(phone):
    """Mask phone number for display (e.g., +123****7890)"""
    if not phone:
        return ''
    if len(phone) > 7:
        return phone[:3] + '*' * (len(phone) - 7) + phone[-4:]
    return '*' * len(phone)


def is_encrypted(data):
    """Check if data appears to be encrypted"""
    if not data:
        return False
    try:
        # Try to decode base64
        base64.urlsafe_b64decode(data.encode('utf-8'))
        # Try to decrypt
        decrypt_data(data)
        return True
    except:
        return False

