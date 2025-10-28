#!/usr/bin/env python3
"""
Secure QR Code Generation and Validation Module
Implements cryptographic signatures for QR code security
"""
import os
import secrets
import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict
import qrcode
from io import BytesIO

class SecureQR:
    """
    Secure QR code generator with HMAC signature validation
    """
    
    # QR Code Version
    VERSION = 'V2'
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize secure QR generator
        
        Args:
            secret_key: Secret key for HMAC signing (defaults to environment variable)
        """
        env_key = os.getenv('VOUCHER_SECRET_KEY')
        self.secret_key = secret_key or env_key or secrets.token_urlsafe(32)
        
        if len(self.secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
    
    def generate_secure_voucher(self, 
                                employee_id: str, 
                                employee_name: str,
                                validity_hours: int = 24) -> Dict:
        """
        Generate a secure voucher with signature
        
        Args:
            employee_id: Employee ID
            employee_name: Employee name
            validity_hours: Voucher validity in hours
            
        Returns:
            Dictionary containing voucher code and QR data
        """
        # Generate random code
        code = self._generate_random_code(12)
        
        # Create voucher data
        now = datetime.now()
        expires_at = now + timedelta(hours=validity_hours)
        
        voucher_data = {
            'code': code,
            'employee_id': employee_id,
            'employee_name': employee_name,
            'created_at': now.isoformat(),
            'expires_at': expires_at.isoformat(),
            'version': self.VERSION
        }
        
        # Encode data
        json_data = json.dumps(voucher_data, sort_keys=True)
        encoded_data = base64.b64encode(json_data.encode()).decode()
        
        # Generate signature
        signature = self._generate_signature(encoded_data)
        
        # Create secure code
        secure_code = f"{self.VERSION}|{encoded_data}|{signature}"
        
        return {
            'voucher_code': code,  # Original code for database
            'secure_code': secure_code,  # Full secure code with signature
            'employee_id': employee_id,
            'employee_name': employee_name,
            'created_at': now.isoformat(),
            'expires_at': expires_at.isoformat(),
            'signature': signature
        }
    
    def validate_secure_code(self, secure_code: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Validate a secure QR code
        
        Args:
            secure_code: Secure code to validate
            
        Returns:
            Tuple of (is_valid, voucher_data, message)
        """
        try:
            # Parse secure code
            parts = secure_code.split('|')
            
            if len(parts) != 3:
                return False, None, "Invalid code format"
            
            version, encoded_data, signature = parts
            
            # Check version compatibility
            if version != self.VERSION:
                return False, None, f"Unsupported version: {version}"
            
            # Verify signature
            expected_signature = self._generate_signature(encoded_data)
            
            # Use constant-time comparison to prevent timing attacks
            if not hmac.compare_digest(signature, expected_signature):
                return False, None, "Invalid signature - code may be tampered"
            
            # Decode data
            try:
                json_data = base64.b64decode(encoded_data.encode()).decode()
                voucher_data = json.loads(json_data)
            except Exception as e:
                return False, None, f"Invalid data encoding: {str(e)}"
            
            # Verify expiration
            expires_at_str = voucher_data.get('expires_at')
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if datetime.now() > expires_at:
                    return False, voucher_data, "Voucher has expired"
            
            # Success
            return True, voucher_data, "Valid voucher"
            
        except Exception as e:
            return False, None, f"Validation error: {str(e)}"
    
    def create_qr_image(self, secure_code: str, save_path: Optional[str] = None) -> str:
        """
        Create QR code image from secure code
        
        Args:
            secure_code: Secure voucher code
            save_path: Optional path to save image
            
        Returns:
            Base64 encoded image or file path
        """
        # Create QR code with higher error correction
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4,
            error_correction=qrcode.constants.ERROR_CORRECT_M  # Medium error correction
        )
        
        qr.add_data(secure_code)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to file if path provided
        if save_path:
            img.save(save_path)
            return save_path
        
        # Return base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    
    def _generate_random_code(self, length: int = 12) -> str:
        """
        Generate a cryptographically secure random code
        
        Args:
            length: Length of code
            
        Returns:
            Random alphanumeric code
        """
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Excludes ambiguous characters
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _generate_signature(self, data: str) -> str:
        """
        Generate HMAC signature for data
        
        Args:
            data: Data to sign
            
        Returns:
            Base64 encoded HMAC-SHA256 signature
        """
        signature = hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode()
    
    @staticmethod
    def check_compatbility(code: str) -> str:
        """
        Check if code is V1 (legacy) or V2 (secure)
        
        Args:
            code: Voucher code
            
        Returns:
            'V1' or 'V2'
        """
        if code.startswith('V2|'):
            return 'V2'
        elif len(code) == 12 and code.isalnum():
            return 'V1'
        else:
            return 'UNKNOWN'


# Rate Limiting Class
class RateLimiter:
    """
    Simple in-memory rate limiter
    In production, use Redis or similar
    """
    
    def __init__(self):
        self.attempts = {}  # {identifier: [timestamps]}
        self.max_attempts = 10  # Max attempts per window
        self.window_seconds = 3600  # 1 hour window
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed
        
        Args:
            identifier: Unique identifier (IP, code, etc.)
            
        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.now()
        
        # Clean old attempts
        if identifier in self.attempts:
            self.attempts[identifier] = [
                ts for ts in self.attempts[identifier]
                if (now - ts).total_seconds() < self.window_seconds
            ]
        
        # Check attempts
        attempt_count = len(self.attempts.get(identifier, []))
        
        if attempt_count >= self.max_attempts:
            return False
        
        # Record attempt
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        self.attempts[identifier].append(now)
        
        return True
    
    def reset(self, identifier: str):
        """Reset attempts for identifier"""
        if identifier in self.attempts:
            del self.attempts[identifier]


# Global instances
secure_qr = SecureQR()
rate_limiter = RateLimiter()


# Convenience functions
def generate_secure_voucher(employee_id: str, employee_name: str, validity_hours: int = 24) -> Dict:
    """Generate a secure voucher"""
    return secure_qr.generate_secure_voucher(employee_id, employee_name, validity_hours)


def validate_secure_code(secure_code: str, check_rate_limit: bool = True) -> Tuple[bool, Optional[Dict], str]:
    """Validate a secure code with optional rate limiting"""
    # Check rate limit
    if check_rate_limit:
        if not rate_limiter.is_allowed(secure_code):
            return False, None, "Too many validation attempts. Please try again later."
    
    # Validate code
    is_valid, data, message = secure_qr.validate_secure_code(secure_code)
    
    return is_valid, data, message


def create_qr_image(secure_code: str, save_path: Optional[str] = None) -> str:
    """Create QR image from secure code"""
    return secure_qr.create_qr_image(secure_code, save_path)


# Testing
if __name__ == "__main__":
    print("=== Secure QR Code Testing ===\n")
    
    # Generate a secure voucher
    print("1. Generating secure voucher...")
    voucher = generate_secure_voucher("EMP001", "John Doe", 24)
    print(f"   Voucher Code: {voucher['voucher_code']}")
    print(f"   Secure Code: {voucher['secure_code'][:50]}...")
    print(f"   Employee: {voucher['employee_name']}")
    print()
    
    # Create QR image
    print("2. Creating QR code image...")
    qr_image = create_qr_image(voucher['secure_code'])
    print(f"   Generated base64 image (length: {len(qr_image)} chars)")
    print()
    
    # Validate correct code
    print("3. Validating correct code...")
    is_valid, data, message = validate_secure_code(voucher['secure_code'])
    print(f"   Valid: {is_valid}")
    print(f"   Message: {message}")
    if data:
        print(f"   Employee ID: {data.get('employee_id')}")
    print()
    
    # Try to tamper with code
    print("4. Testing tamper detection...")
    tampered_code = voucher['secure_code'][:-5] + "XXXXX"
    is_valid, data, message = validate_secure_code(tampered_code)
    print(f"   Valid: {is_valid}")
    print(f"   Message: {message}")
    print()
    
    # Test rate limiting
    print("5. Testing rate limiting...")
    allowed = []
    for i in range(15):
        result = rate_limiter.is_allowed("test_code")
        allowed.append(result)
    print(f"   First 10 requests allowed: {sum(allowed[:10]) == 10}")
    print(f"   Blocked after limit: {sum(allowed[10:]) == 0}")
    
    print("\n=== Tests Complete ===")

