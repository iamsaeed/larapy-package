"""
Laravel-Style Template Functions for Larapy

Provides Laravel Blade functionality using pure Jinja2 syntax through 
enhanced global variables, functions, and context processors.
"""

from typing import Any, Dict, Optional, Union
import os
import secrets


class TemplateAuth:
    """Authentication context object for templates."""
    
    def __init__(self, auth_manager=None):
        self.auth_manager = auth_manager
    
    def check(self, guard='default'):
        """Check if user is authenticated for given guard."""
        if not self.auth_manager:
            return False
        return self.auth_manager.check(guard)
    
    def guest(self, guard='default'):
        """Check if user is guest (not authenticated)."""
        return not self.check(guard)
    
    def user(self, guard='default'):
        """Get authenticated user for given guard."""
        if not self.auth_manager:
            return None
        return self.auth_manager.user(guard)
    
    def id(self, guard='default'):
        """Get authenticated user ID."""
        user = self.user(guard)
        return user.id if user else None

class TemplateErrors:
    """Error bag context object for templates."""
    
    def __init__(self, error_bag=None):
        self.errors = error_bag or {}
    
    def has(self, key):
        """Check if field has validation errors."""
        return key in self.errors and self.errors[key]
    
    def first(self, key, default=''):
        """Get first error message for field."""
        if self.has(key):
            errors = self.errors[key]
            if isinstance(errors, list) and errors:
                return errors[0]
            elif isinstance(errors, str):
                return errors
        return default
    
    def all(self, key=None):
        """Get all errors for field or all errors."""
        if key:
            return self.errors.get(key, [])
        return self.errors
    
    def count(self, key=None):
        """Get error count for field or total error count."""
        if key:
            errors = self.errors.get(key, [])
            return len(errors) if isinstance(errors, list) else (1 if errors else 0)
        return sum(
            len(v) if isinstance(v, list) else 1 
            for v in self.errors.values() 
            if v
        )


class TemplateConfig:
    """Configuration access object for templates."""
    
    def __init__(self, app=None):
        self.app = app
        self._config_cache = {}
    
    def get(self, key, default=None):
        """Get configuration value with dot notation support."""
        if key in self._config_cache:
            return self._config_cache[key]
        
        # Map common Laravel config keys to environment variables
        config_map = {
            'app.name': os.getenv('APP_NAME', 'Larapy'),
            'app.env': os.getenv('APP_ENV', 'local'),
            'app.debug': os.getenv('APP_DEBUG', 'false').lower() == 'true',
            'app.url': os.getenv('APP_URL', 'http://localhost:8000'),
            'app.timezone': os.getenv('APP_TIMEZONE', 'UTC'),
        }
        
        value = config_map.get(key, default)
        self._config_cache[key] = value
        return value
    
    def __call__(self, key, default=None):
        """Allow config to be called as a function."""
        return self.get(key, default)


def create_template_functions(app):
    """Create Laravel-style template functions for Jinja2."""
    
    def csrf_token():
        """Generate CSRF token."""
        # In a real implementation, this would integrate with CSRF middleware
        try:
            csrf_manager = app.resolve('csrf')
            return csrf_manager.generate_token()
        except:
            # Fallback for demo/development
            return secrets.token_urlsafe(32)
    
    def csrf_field():
        """Generate CSRF hidden input field."""
        token = csrf_token()
        return f'<input type="hidden" name="_token" value="{token}">'
    
    def method_field(method):
        """Generate method spoofing field for forms."""
        if method.upper() in ['PUT', 'PATCH', 'DELETE']:
            return f'<input type="hidden" name="_method" value="{method.upper()}">'
        return ''
    
    def old(key, default=''):
        """Get old input value for form repopulation."""
        try:
            session = app.resolve('session') if app.has('session') else {}
            return session.get('_old_input', {}).get(key, default)
        except:
            return default
    
    def route(name, **params):
        """Generate URL for named route."""
        try:
            router = app.resolve('router')
            # In real implementation, this would use router's URL generation
            base_url = params.pop('_base', '')
            if params:
                param_str = '/'.join(str(v) for v in params.values())
                return f"{base_url}/{name}/{param_str}"
            return f"{base_url}/{name}"
        except:
            # Fallback for demo
            if params:
                param_str = '/'.join(str(v) for v in params.values())
                return f"/{name}/{param_str}"
            return f"/{name}"
    
    def asset(path):
        """Generate asset URL."""
        # Remove leading slash if present
        clean_path = path.lstrip('/')
        return f"/assets/{clean_path}"
    
    def url(path):
        """Generate URL."""
        # Remove leading slash if present, then add it back
        clean_path = path.lstrip('/')
        return f"/{clean_path}"
    
    def can(permission, model=None):
        """Check user permission."""
        try:
            auth = app.resolve('auth')
            # In real implementation, integrate with authorization system
            return True  # Placeholder - always allow for demo
        except:
            return False
    
    def cannot(permission, model=None):
        """Check if user cannot perform action."""
        return not can(permission, model)
    
    def mix(path):
        """Laravel Mix asset helper (for versioned assets)."""
        # In real implementation, this would read from mix-manifest.json
        return asset(path)
    
    def secure_asset(path):
        """Generate secure (HTTPS) asset URL."""
        return f"https://{os.getenv('APP_DOMAIN', 'localhost')}/assets/{path.lstrip('/')}"
    
    def secure_url(path):
        """Generate secure (HTTPS) URL."""
        return f"https://{os.getenv('APP_DOMAIN', 'localhost')}/{path.lstrip('/')}"
    
    def app_name():
        """Get application name."""
        return os.getenv('APP_NAME', 'Larapy')
    
    def env(key, default=None):
        """Get environment variable."""
        return os.getenv(key, default)
    
    return {
        'csrf_token': csrf_token,
        'csrf_field': csrf_field,
        'method_field': method_field,
        'old': old,
        'route': route,
        'asset': asset,
        'url': url,
        'can': can,
        'cannot': cannot,
        'mix': mix,
        'secure_asset': secure_asset,
        'secure_url': secure_url,
        'app_name': app_name,
        'env': env,
    }


def create_template_context(app):
    """Create template context objects."""
    # Get application instances
    auth_manager = None
    error_bag = {}
    session_data = {}
    
    try:
        auth_manager = app.resolve('auth') if app.has('auth') else None
    except:
        pass
    
    try:
        error_bag = app.resolve('errors') if app.has('errors') else {}
    except:
        pass
    
    try:
        session_data = app.resolve('session') if app.has('session') else {}
    except:
        pass
    
    # Create context objects
    template_auth = TemplateAuth(auth_manager) if auth_manager else None
    template_errors = TemplateErrors(error_bag)
    template_config = TemplateConfig(app)
    
    return {
        'auth': template_auth,
        'errors': template_errors,
        'config': template_config,
        'session': session_data,
    }