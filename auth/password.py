"""
Password hashing and verification for Larapy authentication.

This module provides secure password hashing using modern algorithms.
"""

from typing import Optional
import secrets
from passlib.context import CryptContext
from passlib.hash import argon2, bcrypt


class PasswordHasher:
    """Handles password hashing and verification."""
    
    def __init__(self, algorithm: str = 'argon2', rounds: Optional[int] = None):
        self.algorithm = algorithm
        
        # Configure password context based on algorithm
        if algorithm == 'argon2':
            schemes = ['argon2']
            self.context = CryptContext(
                schemes=schemes,
                deprecated='auto',
                argon2__time_cost=rounds or 2,
                argon2__memory_cost=65536,
                argon2__parallelism=1,
            )
        elif algorithm == 'bcrypt':
            schemes = ['bcrypt']
            self.context = CryptContext(
                schemes=schemes,
                deprecated='auto',
                bcrypt__rounds=rounds or 12,
            )
        else:
            # Default to argon2 with bcrypt fallback
            schemes = ['argon2', 'bcrypt']
            self.context = CryptContext(
                schemes=schemes,
                deprecated='auto',
                argon2__time_cost=2,
                argon2__memory_cost=65536,
                argon2__parallelism=1,
                bcrypt__rounds=12,
            )
    
    def hash(self, password: str) -> str:
        """Hash a password."""
        return self.context.hash(password)
    
    def check(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        try:
            return self.context.verify(password, hashed)
        except Exception:
            return False
    
    def needs_rehash(self, hashed: str) -> bool:
        """Check if a hash needs to be rehashed with current settings."""
        return self.context.needs_update(hashed)
    
    def get_info(self, hashed: str) -> dict:
        """Get information about a password hash."""
        return self.context.identify(hashed)


class PasswordStrengthValidator:
    """Validates password strength."""
    
    def __init__(self, min_length: int = 8, require_uppercase: bool = True,
                 require_lowercase: bool = True, require_digits: bool = True,
                 require_symbols: bool = True):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_symbols = require_symbols
    
    def validate(self, password: str) -> tuple[bool, list[str]]:
        """Validate password strength. Returns (is_valid, errors)."""
        errors = []
        
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.require_digits and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if self.require_symbols and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    def score(self, password: str) -> int:
        """Calculate password strength score (0-100)."""
        score = 0
        
        # Length score
        score += min(password.__len__() * 4, 25)
        
        # Character variety
        if any(c.isupper() for c in password):
            score += 10
        if any(c.islower() for c in password):
            score += 10
        if any(c.isdigit() for c in password):
            score += 10
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 15
        
        # Patterns and repetition penalties
        if len(set(password)) < len(password) * 0.6:
            score -= 10  # Too much repetition
        
        # Common patterns penalty
        common_patterns = ['123', 'abc', 'qwerty', 'password']
        for pattern in common_patterns:
            if pattern.lower() in password.lower():
                score -= 15
        
        return max(0, min(100, score))


class PasswordGenerator:
    """Generates secure passwords."""
    
    def __init__(self, length: int = 16, use_symbols: bool = True,
                 use_ambiguous: bool = False):
        self.length = length
        self.use_symbols = use_symbols
        self.use_ambiguous = use_ambiguous
    
    def generate(self) -> str:
        """Generate a secure password."""
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        
        if self.use_symbols:
            chars += '!@#$%^&*()_+-=[]{}|;:,.<>?'
        
        if not self.use_ambiguous:
            # Remove ambiguous characters
            ambiguous = 'il1Lo0O'
            chars = ''.join(c for c in chars if c not in ambiguous)
        
        return ''.join(secrets.choice(chars) for _ in range(self.length))
    
    def generate_memorable(self, word_count: int = 4, separator: str = '-') -> str:
        """Generate a memorable password using words."""
        # Simple word list (in a real implementation, you'd use a larger dictionary)
        words = [
            'apple', 'brave', 'chair', 'dance', 'eagle', 'flame', 'grape', 'house',
            'island', 'jungle', 'knight', 'lemon', 'music', 'night', 'ocean', 'peace',
            'quiet', 'river', 'smile', 'tower', 'umbrella', 'voice', 'water', 'xerus',
            'yellow', 'zebra'
        ]
        
        selected_words = [secrets.choice(words) for _ in range(word_count)]
        
        # Capitalize first letter of each word
        selected_words = [word.capitalize() for word in selected_words]
        
        # Add a random number
        selected_words.append(str(secrets.randbelow(100)))
        
        return separator.join(selected_words)


# Global password hasher instance
_password_hasher = None

def get_password_hasher() -> PasswordHasher:
    """Get the global password hasher instance."""
    global _password_hasher
    if _password_hasher is None:
        _password_hasher = PasswordHasher()
    return _password_hasher

def hash_password(password: str) -> str:
    """Hash a password using the global hasher."""
    return get_password_hasher().hash(password)

def check_password(password: str, hashed: str) -> bool:
    """Check a password against its hash using the global hasher."""
    return get_password_hasher().check(password, hashed)

def password_needs_rehash(hashed: str) -> bool:
    """Check if a password hash needs to be updated."""
    return get_password_hasher().needs_rehash(hashed)