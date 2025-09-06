"""
Template Security Features for Larapy

Implements Laravel-equivalent security features for template rendering including
XSS protection, CSRF protection, content security policy, and secure directives.
"""

import re
import html
import hashlib
import secrets
import json
import urllib.parse
from typing import Dict, Any, List, Optional, Union, Callable
from markupsafe import Markup, escape
from jinja2 import Environment, select_autoescape


class TemplateSecurity:
    """
    Template security manager providing Laravel-equivalent security features.
    """
    
    def __init__(self):
        """Initialize template security with default settings."""
        self.csrf_token_name = '_token'
        self.csp_nonce = None
        self.allowed_tags = {
            'b', 'i', 'u', 'strong', 'em', 'p', 'br', 'span', 'div',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li',
            'blockquote', 'code', 'pre'
        }
        self.allowed_attributes = {
            '*': ['class', 'id'],
            'a': ['href', 'title', 'rel', 'target'],
            'img': ['src', 'alt', 'width', 'height', 'class'],
        }
        
    def configure_jinja2_security(self, env: Environment) -> Environment:
        """
        Configure Jinja2 environment with security features.
        
        Args:
            env: Jinja2 environment to configure
            
        Returns:
            Configured environment with security features
        """
        # Enable autoescape for security
        env.autoescape = select_autoescape(['html', 'xml', 'htm'])
        
        # Add security filters
        self._add_security_filters(env)
        
        # Add security globals
        self._add_security_globals(env)
        
        # Add security tests
        self._add_security_tests(env)
        
        return env
    
    def _add_security_filters(self, env: Environment):
        """Add security-focused template filters."""
        
        # Laravel's {!! !!} equivalent - render unescaped (use carefully)
        def raw_filter(value):
            """Render content without escaping (Laravel's {!! !!} equivalent)."""
            if value is None:
                return ''
            return Markup(str(value))
        
        # Laravel's {{ }} equivalent - auto-escaped output
        def escaped_filter(value):
            """Auto-escaped output (Laravel's {{ }} equivalent)."""
            if value is None:
                return ''
            return escape(str(value))
        
        # Clean HTML filter
        def clean_html_filter(value, allowed_tags=None, allowed_attrs=None):
            """Clean HTML content allowing only specified tags and attributes."""
            if not value:
                return ''
                
            try:
                from bleach import clean
                tags = allowed_tags or list(self.allowed_tags)
                attrs = allowed_attrs or self.allowed_attributes
                return Markup(clean(str(value), tags=tags, attributes=attrs, strip=True))
            except ImportError:
                # Fallback to basic HTML escaping
                return escape(str(value))
        
        # JSON encode filter (for safe JavaScript embedding)
        def json_encode_filter(value):
            """JSON encode value for safe JavaScript embedding."""
            return Markup(json.dumps(value, separators=(',', ':')))
        
        # URL encode filter
        def url_encode_filter(value):
            """URL encode value for safe URL embedding."""
            if value is None:
                return ''
            return urllib.parse.quote_plus(str(value))
        
        # Attribute encode filter
        def attr_filter(value):
            """Encode value for safe HTML attribute embedding."""
            if value is None:
                return ''
            return html.escape(str(value), quote=True)
        
        # CSS encode filter
        def css_filter(value):
            """Encode value for safe CSS embedding."""
            if value is None:
                return ''
            # Basic CSS escaping - remove dangerous characters
            value = re.sub(r'[<>&"\']', '', str(value))
            value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
            value = re.sub(r'expression\s*\(', '', value, flags=re.IGNORECASE)
            return value
        
        # Add filters to environment
        env.filters['raw'] = raw_filter
        env.filters['e'] = escaped_filter  # Laravel's e() function equivalent
        env.filters['clean_html'] = clean_html_filter
        env.filters['json_encode'] = json_encode_filter
        env.filters['url_encode'] = url_encode_filter
        env.filters['attr'] = attr_filter
        env.filters['css'] = css_filter
    
    def _add_security_globals(self, env: Environment):
        """Add security-focused global functions."""
        
        def csrf_token():
            """Generate CSRF token (Laravel equivalent)."""
            # In a real implementation, this would get from session/request
            return secrets.token_hex(20)
        
        def csrf_field():
            """Generate CSRF hidden field (Laravel equivalent)."""
            token = csrf_token()
            return Markup(f'<input type="hidden" name="{self.csrf_token_name}" value="{token}">')
        
        def method_field(method):
            """Generate method spoofing field (Laravel equivalent)."""
            method = str(method).upper()
            if method in ['PUT', 'PATCH', 'DELETE']:
                return Markup(f'<input type="hidden" name="_method" value="{method}">')
            return ''
        
        def nonce():
            """Generate CSP nonce for inline scripts/styles."""
            if self.csp_nonce is None:
                self.csp_nonce = secrets.token_urlsafe(16)
            return self.csp_nonce
        
        def secure_url(path, **kwargs):
            """Generate secure (HTTPS) URL."""
            # In real implementation, this would check app configuration
            base_url = "https://localhost"  # Should come from config
            query_string = urllib.parse.urlencode(kwargs) if kwargs else ''
            url = f"{base_url}/{path.lstrip('/')}"
            return f"{url}?{query_string}" if query_string else url
        
        def asset_with_version(path, version=None):
            """Generate versioned asset URL for cache busting."""
            if version is None:
                # Generate version hash based on file or app version
                version = hashlib.md5(path.encode()).hexdigest()[:8]
            return f"/assets/{path.lstrip('/')}?v={version}"
        
        def config(key, default=None):
            """Get configuration value (Laravel equivalent)."""
            # In real implementation, this would access app config
            config_values = {
                'app.name': 'Larapy Framework',
                'app.env': 'local',
                'app.debug': True,
                'app.url': 'http://localhost:8000',
                'app.version': '1.0.0',
            }
            return config_values.get(key, default)
        
        def auth_user():
            """Get authenticated user (Laravel equivalent)."""
            # In real implementation, this would get from request context
            return None  # Placeholder
        
        def can(permission, model=None):
            """Check user permission (Laravel equivalent)."""
            # In real implementation, this would check authorization
            return False  # Placeholder
        
        # Add globals to environment
        env.globals['csrf_token'] = csrf_token
        env.globals['csrf_field'] = csrf_field
        env.globals['method_field'] = method_field
        env.globals['nonce'] = nonce
        env.globals['secure_url'] = secure_url
        env.globals['asset'] = asset_with_version
        env.globals['config'] = config
        env.globals['auth'] = auth_user
        env.globals['can'] = can
    
    def _add_security_tests(self, env: Environment):
        """Add security-focused template tests."""
        
        def test_authenticated(value):
            """Test if user is authenticated."""
            return value is not None
        
        def test_guest(value):
            """Test if user is guest (not authenticated)."""
            return value is None
        
        def test_secure_url(url):
            """Test if URL is using HTTPS."""
            return str(url).startswith('https://')
        
        def test_safe_content(content):
            """Test if content is safe (Markup object)."""
            return isinstance(content, Markup)
        
        # Add tests to environment
        env.tests['authenticated'] = test_authenticated
        env.tests['guest'] = test_guest
        env.tests['secure'] = test_secure_url
        env.tests['safe'] = test_safe_content


class CSRFProtection:
    """
    CSRF protection for templates (Laravel equivalent).
    """
    
    def __init__(self, secret_key: str):
        """
        Initialize CSRF protection.
        
        Args:
            secret_key: Secret key for token generation
        """
        self.secret_key = secret_key
        self.token_name = '_token'
        self.header_name = 'X-CSRF-TOKEN'
    
    def generate_token(self, session_id: str = None) -> str:
        """Generate CSRF token for session."""
        if session_id is None:
            session_id = secrets.token_hex(16)
        
        # Create token based on session and secret
        data = f"{session_id}{self.secret_key}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_token(self, token: str, session_id: str = None) -> bool:
        """Verify CSRF token."""
        if not token or not session_id:
            return False
        
        expected_token = self.generate_token(session_id)
        return secrets.compare_digest(token, expected_token)
    
    def get_token_field(self, session_id: str = None) -> str:
        """Get CSRF token as hidden form field."""
        token = self.generate_token(session_id)
        return f'<input type="hidden" name="{self.token_name}" value="{token}">'
    
    def get_meta_tag(self, session_id: str = None) -> str:
        """Get CSRF token as meta tag for AJAX requests."""
        token = self.generate_token(session_id)
        return f'<meta name="csrf-token" content="{token}">'


class ContentSecurityPolicy:
    """
    Content Security Policy helper for templates.
    """
    
    def __init__(self):
        """Initialize CSP with default secure policy."""
        self.directives = {
            'default-src': ["'self'"],
            'script-src': ["'self'", "'unsafe-inline'"],  # Will be made stricter with nonces
            'style-src': ["'self'", "'unsafe-inline'"],   # Will be made stricter with nonces
            'img-src': ["'self'", "data:", "https:"],
            'font-src': ["'self'", "https:"],
            'connect-src': ["'self'"],
            'media-src': ["'self'"],
            'object-src': ["'none'"],
            'child-src': ["'self'"],
            'frame-ancestors': ["'self'"],
            'form-action': ["'self'"],
            'base-uri': ["'self'"],
            'upgrade-insecure-requests': [],
        }
        self.nonce = None
    
    def generate_nonce(self) -> str:
        """Generate nonce for inline scripts/styles."""
        self.nonce = secrets.token_urlsafe(16)
        return self.nonce
    
    def add_nonce_to_scripts(self):
        """Add nonce to script-src directive."""
        if self.nonce and "'unsafe-inline'" in self.directives['script-src']:
            self.directives['script-src'].remove("'unsafe-inline'")
        if self.nonce:
            nonce_value = f"'nonce-{self.nonce}'"
            if nonce_value not in self.directives['script-src']:
                self.directives['script-src'].append(nonce_value)
    
    def add_nonce_to_styles(self):
        """Add nonce to style-src directive."""
        if self.nonce and "'unsafe-inline'" in self.directives['style-src']:
            self.directives['style-src'].remove("'unsafe-inline'")
        if self.nonce:
            nonce_value = f"'nonce-{self.nonce}'"
            if nonce_value not in self.directives['style-src']:
                self.directives['style-src'].append(nonce_value)
    
    def get_header_value(self) -> str:
        """Get CSP header value."""
        policy_parts = []
        for directive, sources in self.directives.items():
            if sources:
                policy_parts.append(f"{directive} {' '.join(sources)}")
            elif directive in ['upgrade-insecure-requests']:
                policy_parts.append(directive)
        
        return '; '.join(policy_parts)
    
    def get_meta_tag(self) -> str:
        """Get CSP as meta tag."""
        return f'<meta http-equiv="Content-Security-Policy" content="{self.get_header_value()}">'


class TemplateSecurityMiddleware:
    """
    Template security middleware to add security headers and context.
    """
    
    def __init__(self, csrf_protection: CSRFProtection = None, csp: ContentSecurityPolicy = None):
        """
        Initialize template security middleware.
        
        Args:
            csrf_protection: CSRF protection instance
            csp: Content Security Policy instance
        """
        self.csrf_protection = csrf_protection
        self.csp = csp or ContentSecurityPolicy()
        
    def process_template_context(self, context: Dict[str, Any], request=None) -> Dict[str, Any]:
        """
        Process template context to add security-related variables.
        
        Args:
            context: Template context dictionary
            request: Request object (if available)
            
        Returns:
            Enhanced context with security features
        """
        # Generate CSP nonce
        nonce = self.csp.generate_nonce()
        self.csp.add_nonce_to_scripts()
        self.csp.add_nonce_to_styles()
        
        # Add security context
        security_context = {
            'csp_nonce': nonce,
            'csp_meta': self.csp.get_meta_tag(),
            'is_secure': request.is_secure if request and hasattr(request, 'is_secure') else False,
        }
        
        # Add CSRF protection if available
        if self.csrf_protection:
            session_id = getattr(request, 'session_id', None) if request else None
            security_context.update({
                'csrf_token': lambda: self.csrf_protection.generate_token(session_id),
                'csrf_field': Markup(self.csrf_protection.get_token_field(session_id)),
                'csrf_meta': Markup(self.csrf_protection.get_meta_tag(session_id)),
            })
        else:
            # Fallback CSRF functions
            security_context.update({
                'csrf_token': lambda: 'demo-token',
                'csrf_field': Markup('<input type="hidden" name="_token" value="demo-token">'),
                'csrf_meta': Markup('<meta name="csrf-token" content="demo-token">'),
            })
        
        # Add essential template functions
        def config(key, default=None):
            """Get configuration value (Laravel equivalent)."""
            config_values = {
                'app.name': 'Larapy Framework',
                'app.env': 'local',
                'app.debug': True,
                'app.url': 'http://localhost:8000',
                'app.version': '1.0.0',
            }
            return config_values.get(key, default)
        
        def auth_user():
            """Get authenticated user (Laravel equivalent)."""
            return None  # Placeholder
        
        security_context.update({
            'config': config,
            'auth': auth_user(),
        })
        
        # Merge with existing context
        return {**context, **security_context}
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers to add to response."""
        headers = {}
        
        # Content Security Policy
        headers['Content-Security-Policy'] = self.csp.get_header_value()
        
        # Other security headers
        headers.update({
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        })
        
        return headers


# Global security instance
template_security = TemplateSecurity()

# Helper functions
def configure_template_security(env: Environment, secret_key: str = None) -> Environment:
    """Configure Jinja2 environment with security features."""
    return template_security.configure_jinja2_security(env)

def create_csrf_protection(secret_key: str) -> CSRFProtection:
    """Create CSRF protection instance."""
    return CSRFProtection(secret_key)

def create_csp() -> ContentSecurityPolicy:
    """Create Content Security Policy instance."""
    return ContentSecurityPolicy()

def create_security_middleware(secret_key: str = None) -> TemplateSecurityMiddleware:
    """Create template security middleware."""
    csrf = CSRFProtection(secret_key) if secret_key else None
    csp = ContentSecurityPolicy()
    return TemplateSecurityMiddleware(csrf, csp)