"""
Input Sanitization System

Provides comprehensive input sanitization and validation for security.
"""

import re
import html
import urllib.parse
from typing import Any, Dict, List, Union, Optional, Callable
from bleach import clean, ALLOWED_TAGS, ALLOWED_ATTRIBUTES
import unicodedata


class InputSanitizer:
    """
    Comprehensive input sanitization system for security.
    """
    
    # Default allowed HTML tags for rich text content
    DEFAULT_ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'i', 'b', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'span', 'div'
    ]
    
    # Default allowed HTML attributes
    DEFAULT_ALLOWED_ATTRS = {
        '*': ['class', 'id'],
        'a': ['href', 'title', 'rel'],
        'img': ['src', 'alt', 'width', 'height'],
    }
    
    def __init__(self):
        """Initialize the sanitizer with default settings."""
        self.rules = {}
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default sanitization rules."""
        self.rules = {
            'email': self._sanitize_email,
            'url': self._sanitize_url,
            'phone': self._sanitize_phone,
            'text': self._sanitize_text,
            'html': self._sanitize_html,
            'filename': self._sanitize_filename,
            'sql': self._sanitize_sql,
            'xss': self._sanitize_xss,
            'csrf': self._sanitize_csrf,
            'unicode': self._sanitize_unicode,
        }
    
    def sanitize(self, data: Any, rule: str, **options) -> Any:
        """
        Sanitize input data using specified rule.
        
        Args:
            data: Input data to sanitize
            rule: Sanitization rule to apply
            **options: Additional options for sanitization
            
        Returns:
            Sanitized data
        """
        if not isinstance(data, (str, dict, list)):
            return data
            
        if rule not in self.rules:
            raise ValueError(f"Unknown sanitization rule: {rule}")
        
        if isinstance(data, str):
            return self.rules[rule](data, **options)
        elif isinstance(data, dict):
            return {k: self.sanitize(v, rule, **options) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize(item, rule, **options) for item in data]
        
        return data
    
    def _sanitize_email(self, email: str, **options) -> str:
        """Sanitize email address."""
        # Remove whitespace and convert to lowercase
        email = email.strip().lower()
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return ""
        
        # Remove potentially dangerous characters
        email = re.sub(r'[<>"\']', '', email)
        
        return email
    
    def _sanitize_url(self, url: str, **options) -> str:
        """Sanitize URL."""
        allowed_schemes = options.get('allowed_schemes', ['http', 'https', 'ftp'])
        
        # Remove whitespace
        url = url.strip()
        
        # Parse URL
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme and parsed.scheme not in allowed_schemes:
                return ""
            
            # Encode special characters
            url = urllib.parse.quote(url, safe=':/?#[]@!$&\'()*+,;=')
            
        except Exception:
            return ""
        
        return url
    
    def _sanitize_phone(self, phone: str, **options) -> str:
        """Sanitize phone number."""
        # Remove all non-digit characters except + and spaces
        phone = re.sub(r'[^\d+\s\-().]', '', phone)
        
        # Remove extra spaces
        phone = re.sub(r'\s+', ' ', phone).strip()
        
        return phone
    
    def _sanitize_text(self, text: str, **options) -> str:
        """Sanitize plain text."""
        max_length = options.get('max_length', 10000)
        strip_html = options.get('strip_html', True)
        
        # Strip HTML tags if requested
        if strip_html:
            text = re.sub(r'<[^>]+>', '', text)
        
        # Escape HTML entities
        text = html.escape(text)
        
        # Remove control characters
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    def _sanitize_html(self, html_content: str, **options) -> str:
        """Sanitize HTML content."""
        allowed_tags = options.get('allowed_tags', self.DEFAULT_ALLOWED_TAGS)
        allowed_attrs = options.get('allowed_attrs', self.DEFAULT_ALLOWED_ATTRS)
        strip = options.get('strip', True)
        
        # Clean HTML using bleach
        cleaned = clean(
            html_content,
            tags=allowed_tags,
            attributes=allowed_attrs,
            strip=strip,
            strip_comments=True
        )
        
        return cleaned
    
    def _sanitize_filename(self, filename: str, **options) -> str:
        """Sanitize filename."""
        max_length = options.get('max_length', 255)
        
        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'[\x00-\x1f\x80-\x9f]', '', filename)
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Limit length
        if len(filename) > max_length:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            name = name[:max_length - len(ext) - 1]
            filename = f"{name}.{ext}" if ext else name
        
        return filename
    
    def _sanitize_sql(self, query: str, **options) -> str:
        """Sanitize SQL query (basic protection)."""
        dangerous_patterns = [
            r'(;|\s+)(drop|delete|truncate|insert|update|create|alter)\s+',
            r'(union\s+select|exec|execute)',
            r'(script|javascript|vbscript)',
        ]
        
        query_lower = query.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, query_lower):
                raise ValueError("Potentially dangerous SQL detected")
        
        return query
    
    def _sanitize_xss(self, content: str, **options) -> str:
        """Sanitize against XSS attacks."""
        # Remove script tags and event handlers
        xss_patterns = [
            r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe\b[^>]*>.*?</iframe>',
            r'<object\b[^>]*>.*?</object>',
            r'<embed\b[^>]*>',
        ]
        
        for pattern in xss_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Escape remaining HTML
        content = html.escape(content)
        
        return content
    
    def _sanitize_csrf(self, token: str, **options) -> str:
        """Sanitize CSRF token."""
        # CSRF tokens should be alphanumeric
        token = re.sub(r'[^a-zA-Z0-9]', '', token)
        
        # Check length (typical CSRF tokens are 32-64 characters)
        if not 32 <= len(token) <= 64:
            return ""
        
        return token
    
    def _sanitize_unicode(self, text: str, **options) -> str:
        """Sanitize Unicode text."""
        # Normalize Unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Remove zero-width characters
        text = re.sub(r'[\u200b-\u200f\u2028-\u202f\u205f-\u206f\ufeff]', '', text)
        
        return text
    
    def add_rule(self, name: str, sanitizer_func: Callable):
        """
        Add custom sanitization rule.
        
        Args:
            name: Rule name
            sanitizer_func: Function that takes (text, **options) and returns sanitized text
        """
        self.rules[name] = sanitizer_func
    
    def sanitize_dict(self, data: Dict[str, Any], rules: Dict[str, str]) -> Dict[str, Any]:
        """
        Sanitize dictionary based on field-specific rules.
        
        Args:
            data: Input dictionary
            rules: Dictionary mapping field names to sanitization rules
            
        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        
        for key, value in data.items():
            if key in rules:
                sanitized[key] = self.sanitize(value, rules[key])
            else:
                # Apply default text sanitization
                sanitized[key] = self.sanitize(value, 'text')
        
        return sanitized
    
    def validate_and_sanitize(self, data: Any, rule: str, validator: Optional[Callable] = None, **options) -> tuple[bool, Any]:
        """
        Validate and sanitize data.
        
        Args:
            data: Input data
            rule: Sanitization rule
            validator: Optional validation function
            **options: Additional options
            
        Returns:
            Tuple of (is_valid, sanitized_data)
        """
        try:
            # Sanitize first
            sanitized = self.sanitize(data, rule, **options)
            
            # Validate if validator provided
            if validator:
                is_valid = validator(sanitized)
                return is_valid, sanitized
            
            # Basic validation - check if sanitized data is meaningful
            if isinstance(sanitized, str) and not sanitized.strip():
                return False, sanitized
            
            return True, sanitized
            
        except Exception:
            return False, None


class FormSanitizer(InputSanitizer):
    """
    Specialized sanitizer for form data.
    """
    
    def sanitize_form_data(self, form_data: Dict[str, Any], field_rules: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Sanitize form data with field-specific rules.
        
        Args:
            form_data: Form data dictionary
            field_rules: Optional field-specific rules
            
        Returns:
            Sanitized form data
        """
        if not field_rules:
            field_rules = {}
        
        sanitized = {}
        
        for field, value in form_data.items():
            rule = field_rules.get(field, 'text')
            sanitized[field] = self.sanitize(value, rule)
        
        return sanitized


# Global sanitizer instance
sanitizer = InputSanitizer()

# Helper functions for common sanitization tasks
def sanitize_input(data: Any, rule: str = 'text', **options) -> Any:
    """Sanitize input data using global sanitizer."""
    return sanitizer.sanitize(data, rule, **options)

def sanitize_html(html_content: str, **options) -> str:
    """Sanitize HTML content."""
    return sanitizer.sanitize(html_content, 'html', **options)

def sanitize_text(text: str, **options) -> str:
    """Sanitize plain text."""
    return sanitizer.sanitize(text, 'text', **options)

def sanitize_email(email: str) -> str:
    """Sanitize email address."""
    return sanitizer.sanitize(email, 'email')

def sanitize_url(url: str, **options) -> str:
    """Sanitize URL."""
    return sanitizer.sanitize(url, 'url', **options)