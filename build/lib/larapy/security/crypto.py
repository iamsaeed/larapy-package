"""
Encryption and Cryptographic Utilities

Provides secure encryption, hashing, and token generation functionality.
"""

import os
import base64
import hashlib
import secrets
import hmac
import time
from typing import Union, Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import bcrypt
import jwt


class CryptoManager:
    """
    Main cryptographic operations manager.
    """
    
    def __init__(self, app_key: Optional[str] = None):
        """
        Initialize crypto manager.
        
        Args:
            app_key: Application encryption key
        """
        self.app_key = app_key or os.environ.get('APP_KEY', self._generate_key())
        self._fernet = None
        self._initialize_fernet()
    
    def _initialize_fernet(self):
        """Initialize Fernet encryption."""
        if len(self.app_key) < 32:
            # Derive key from app key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'larapy_salt_2024',
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.app_key.encode()))
        else:
            key = base64.urlsafe_b64encode(self.app_key.encode()[:32])
        
        self._fernet = Fernet(key)
    
    @staticmethod
    def _generate_key() -> str:
        """Generate a secure random key."""
        return secrets.token_urlsafe(32)
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """
        Encrypt data using Fernet symmetric encryption.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Base64 encoded encrypted data
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted = self._fernet.encrypt(data)
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data using Fernet symmetric encryption.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted string
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {e}")
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """
        Encrypt dictionary as JSON.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Encrypted JSON string
        """
        import json
        json_data = json.dumps(data, separators=(',', ':'))
        return self.encrypt(json_data)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt JSON dictionary.
        
        Args:
            encrypted_data: Encrypted JSON string
            
        Returns:
            Decrypted dictionary
        """
        import json
        json_data = self.decrypt(encrypted_data)
        return json.loads(json_data)


class HasherManager:
    """
    Password hashing and verification manager.
    """
    
    @staticmethod
    def hash_password(password: str, rounds: int = 12) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
            rounds: Number of rounds for bcrypt
            
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            True if password matches hash
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def hash_string(data: str, algorithm: str = 'sha256') -> str:
        """
        Hash string using specified algorithm.
        
        Args:
            data: String to hash
            algorithm: Hash algorithm (md5, sha1, sha256, sha512)
            
        Returns:
            Hexadecimal hash
        """
        hash_func = getattr(hashlib, algorithm.lower())
        return hash_func(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def hmac_hash(data: str, key: str, algorithm: str = 'sha256') -> str:
        """
        Create HMAC hash.
        
        Args:
            data: Data to hash
            key: Secret key
            algorithm: Hash algorithm
            
        Returns:
            HMAC hash in hex format
        """
        hash_func = getattr(hashlib, algorithm.lower())
        return hmac.new(
            key.encode('utf-8'),
            data.encode('utf-8'),
            hash_func
        ).hexdigest()


class TokenManager:
    """
    Secure token generation and management.
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize token manager.
        
        Args:
            secret_key: Secret key for token signing
        """
        self.secret_key = secret_key or os.environ.get('SECRET_KEY', secrets.token_urlsafe(32))
    
    def generate_token(self, length: int = 32, url_safe: bool = True) -> str:
        """
        Generate secure random token.
        
        Args:
            length: Token length in bytes
            url_safe: Whether token should be URL safe
            
        Returns:
            Random token
        """
        if url_safe:
            return secrets.token_urlsafe(length)
        else:
            return secrets.token_hex(length)
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token."""
        return self.generate_token(32)
    
    def generate_api_key(self, prefix: str = 'lpk') -> str:
        """
        Generate API key with prefix.
        
        Args:
            prefix: API key prefix
            
        Returns:
            API key with prefix
        """
        token = self.generate_token(24)
        return f"{prefix}_{token}"
    
    def create_jwt_token(self, payload: Dict[str, Any], expires_in: int = 3600, algorithm: str = 'HS256') -> str:
        """
        Create JWT token.
        
        Args:
            payload: Token payload
            expires_in: Expiration time in seconds
            algorithm: Signing algorithm
            
        Returns:
            JWT token
        """
        payload['exp'] = int(time.time()) + expires_in
        payload['iat'] = int(time.time())
        
        return jwt.encode(payload, self.secret_key, algorithm=algorithm)
    
    def verify_jwt_token(self, token: str, algorithm: str = 'HS256') -> Optional[Dict[str, Any]]:
        """
        Verify JWT token.
        
        Args:
            token: JWT token to verify
            algorithm: Signing algorithm
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def generate_signed_token(self, data: str, expires_in: Optional[int] = None) -> str:
        """
        Generate signed token with optional expiration.
        
        Args:
            data: Data to include in token
            expires_in: Expiration time in seconds
            
        Returns:
            Signed token
        """
        payload = {'data': data}
        if expires_in:
            payload['exp'] = int(time.time()) + expires_in
        
        return self.create_jwt_token(payload)
    
    def verify_signed_token(self, token: str) -> Optional[str]:
        """
        Verify signed token and return data.
        
        Args:
            token: Signed token
            
        Returns:
            Token data if valid, None otherwise
        """
        payload = self.verify_jwt_token(token)
        return payload.get('data') if payload else None


class PasswordValidator:
    """
    Password strength validation.
    """
    
    def __init__(self):
        """Initialize password validator with default rules."""
        self.min_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digits = True
        self.require_special = True
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    def validate(self, password: str) -> tuple[bool, list[str]]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.require_digits and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if self.require_special and not any(c in self.special_chars for c in password):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password.lower() in weak_passwords:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors
    
    def generate_password(self, length: int = 12) -> str:
        """
        Generate secure password.
        
        Args:
            length: Password length
            
        Returns:
            Secure random password
        """
        import string
        
        characters = ""
        if self.require_lowercase:
            characters += string.ascii_lowercase
        if self.require_uppercase:
            characters += string.ascii_uppercase
        if self.require_digits:
            characters += string.digits
        if self.require_special:
            characters += self.special_chars
        
        if not characters:
            characters = string.ascii_letters + string.digits
        
        password = ''.join(secrets.choice(characters) for _ in range(length))
        
        # Ensure password meets requirements
        is_valid, _ = self.validate(password)
        if not is_valid:
            return self.generate_password(length)
        
        return password


class DataSigner:
    """
    Data signing and verification for integrity.
    """
    
    def __init__(self, secret_key: str):
        """
        Initialize data signer.
        
        Args:
            secret_key: Secret key for signing
        """
        self.secret_key = secret_key
    
    def sign(self, data: str) -> str:
        """
        Sign data with timestamp.
        
        Args:
            data: Data to sign
            
        Returns:
            Signed data with signature
        """
        timestamp = str(int(time.time()))
        message = f"{data}.{timestamp}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{data}.{timestamp}.{signature}"
    
    def unsign(self, signed_data: str, max_age: Optional[int] = None) -> Optional[str]:
        """
        Verify and unsign data.
        
        Args:
            signed_data: Signed data to verify
            max_age: Maximum age in seconds
            
        Returns:
            Original data if valid, None otherwise
        """
        try:
            parts = signed_data.rsplit('.', 2)
            if len(parts) != 3:
                return None
            
            data, timestamp, signature = parts
            message = f"{data}.{timestamp}"
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            # Check age if specified
            if max_age:
                age = int(time.time()) - int(timestamp)
                if age > max_age:
                    return None
            
            return data
            
        except (ValueError, IndexError):
            return None


# Global instances
crypto = CryptoManager()
hasher = HasherManager()
token_manager = TokenManager()
password_validator = PasswordValidator()

# Helper functions
def encrypt(data: Union[str, bytes]) -> str:
    """Encrypt data using global crypto manager."""
    return crypto.encrypt(data)

def decrypt(encrypted_data: str) -> str:
    """Decrypt data using global crypto manager."""
    return crypto.decrypt(encrypted_data)

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return hasher.hash_password(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hasher.verify_password(password, hashed)

def generate_token(length: int = 32) -> str:
    """Generate secure random token."""
    return token_manager.generate_token(length)

def generate_csrf_token() -> str:
    """Generate CSRF token."""
    return token_manager.generate_csrf_token()

def create_jwt(payload: Dict[str, Any], expires_in: int = 3600) -> str:
    """Create JWT token."""
    return token_manager.create_jwt_token(payload, expires_in)

def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token."""
    return token_manager.verify_jwt_token(token)

def validate_password(password: str) -> tuple[bool, list[str]]:
    """Validate password strength."""
    return password_validator.validate(password)