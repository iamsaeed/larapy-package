"""
Secure Template Directives for Larapy

Implements Laravel Blade-equivalent directives with security features.
"""

from typing import Dict, Any, Callable, Optional
from markupsafe import Markup, escape
import re


class SecureDirectives:
    """
    Secure template directives system inspired by Laravel Blade.
    """
    
    def __init__(self):
        """Initialize secure directives."""
        self.directives: Dict[str, Callable] = {}
        self._register_default_directives()
    
    def _register_default_directives(self):
        """Register default secure directives."""
        
        # Authentication directives
        self.register('auth', self._auth_directive)
        self.register('guest', self._guest_directive)
        self.register('endauth', lambda: '')
        self.register('endguest', lambda: '')
        
        # Authorization directives
        self.register('can', self._can_directive)
        self.register('cannot', self._cannot_directive)
        self.register('endcan', lambda: '')
        self.register('endcannot', lambda: '')
        
        # Environment directives
        self.register('env', self._env_directive)
        self.register('endenv', lambda: '')
        self.register('production', self._production_directive)
        self.register('endproduction', lambda: '')
        
        # Security directives
        self.register('csrf', self._csrf_directive)
        self.register('method', self._method_directive)
        self.register('error', self._error_directive)
        self.register('enderror', lambda: '')
        
        # Content directives
        self.register('verbatim', self._verbatim_directive)
        self.register('endverbatim', lambda: '')
        self.register('json', self._json_directive)
        
        # Conditional directives
        self.register('unless', self._unless_directive)
        self.register('endunless', lambda: '')
        self.register('empty', self._empty_directive)
        self.register('endempty', lambda: '')
        
        # Loop directives
        self.register('forelse', self._forelse_directive)
        self.register('empty_forelse', lambda: '')
        self.register('endforelse', lambda: '')
        
        # Include directives
        self.register('include', self._include_directive)
        self.register('includeIf', self._include_if_directive)
        self.register('includeWhen', self._include_when_directive)
        
        # Asset directives
        self.register('asset', self._asset_directive)
        self.register('url', self._url_directive)
        self.register('route', self._route_directive)
    
    def register(self, name: str, callback: Callable):
        """
        Register a new directive.
        
        Args:
            name: Directive name
            callback: Callback function
        """
        self.directives[name] = callback
    
    def compile(self, template_content: str) -> str:
        """
        Compile template directives to Jinja2 syntax.
        
        Args:
            template_content: Raw template content
            
        Returns:
            Compiled template with Jinja2 syntax
        """
        # Process directives in order of specificity
        content = template_content
        
        # Process @directive(...) patterns
        directive_pattern = r'@(\w+)(?:\(([^)]*)\))?'
        
        def replace_directive(match):
            directive_name = match.group(1)
            args = match.group(2) or ''
            
            if directive_name in self.directives:
                try:
                    return self.directives[directive_name](args)
                except Exception:
                    # If directive fails, return original
                    return match.group(0)
            
            return match.group(0)
        
        content = re.sub(directive_pattern, replace_directive, content)
        
        # Process special Laravel-style output syntax
        content = self._process_output_syntax(content)
        
        return content
    
    def _process_output_syntax(self, content: str) -> str:
        """Process Laravel-style output syntax."""
        # Convert {!! $var !!} to {{ var|raw }} (unescaped)
        content = re.sub(r'\{\!!\s*(.*?)\s*\!\!\}', r'{{ \1|raw }}', content)
        
        # Convert {{ $var }} to {{ var|e }} (escaped) - already handled by Jinja2
        # Just ensure it's properly formatted
        content = re.sub(r'\{\{\s*\$(.*?)\s*\}\}', r'{{ \1|e }}', content)
        
        return content
    
    # Authentication Directives
    def _auth_directive(self, args: str = '') -> str:
        """@auth directive for authenticated users."""
        guard = args.strip().strip("'\"") if args else 'default'
        return f"{{% if auth and auth.check('{guard}') %}}"
    
    def _guest_directive(self, args: str = '') -> str:
        """@guest directive for guest users."""
        guard = args.strip().strip("'\"") if args else 'default'
        return f"{{% if not auth or not auth.check('{guard}') %}}"
    
    # Authorization Directives
    def _can_directive(self, args: str) -> str:
        """@can directive for authorization."""
        parts = [p.strip().strip("'\"") for p in args.split(',')]
        permission = parts[0] if parts else ''
        model = parts[1] if len(parts) > 1 else 'None'
        return f"{{% if can('{permission}', {model}) %}}"
    
    def _cannot_directive(self, args: str) -> str:
        """@cannot directive for authorization."""
        parts = [p.strip().strip("'\"") for p in args.split(',')]
        permission = parts[0] if parts else ''
        model = parts[1] if len(parts) > 1 else 'None'
        return f"{{% if not can('{permission}', {model}) %}}"
    
    # Environment Directives
    def _env_directive(self, args: str) -> str:
        """@env directive for environment checking."""
        envs = [e.strip().strip("'\"") for e in args.split(',')]
        env_check = ' or '.join([f"config('app.env') == '{env}'" for env in envs])
        return f"{{% if {env_check} %}}"
    
    def _production_directive(self, args: str = '') -> str:
        """@production directive for production environment."""
        return "{% if config('app.env') == 'production' %}"
    
    # Security Directives
    def _csrf_directive(self, args: str = '') -> str:
        """@csrf directive for CSRF token field."""
        return "{{ csrf_field()|safe }}"
    
    def _method_directive(self, args: str) -> str:
        """@method directive for HTTP method spoofing."""
        method = args.strip().strip("'\"").upper()
        return f"{{{{ method_field('{method}')|safe }}}}"
    
    def _error_directive(self, args: str) -> str:
        """@error directive for validation errors."""
        field = args.strip().strip("'\"")
        return f"{{% if errors and errors.has('{field}') %}}"
    
    # Content Directives
    def _verbatim_directive(self, args: str = '') -> str:
        """@verbatim directive to prevent processing."""
        return "{% raw %}"
    
    def _json_directive(self, args: str) -> str:
        """@json directive for safe JSON output."""
        return f"{{{{ {args}|json_encode|safe }}}}"
    
    # Conditional Directives
    def _unless_directive(self, args: str) -> str:
        """@unless directive (opposite of @if)."""
        return f"{{% if not ({args}) %}}"
    
    def _empty_directive(self, args: str) -> str:
        """@empty directive for empty checks."""
        return f"{{% if not {args} or ({args}|length == 0) %}}"
    
    # Loop Directives
    def _forelse_directive(self, args: str) -> str:
        """@forelse directive for loops with empty fallback."""
        # Parse "item in items" syntax
        parts = args.split(' in ')
        if len(parts) == 2:
            item, collection = parts[0].strip(), parts[1].strip()
            return f"{{% for {item} in {collection} %}}"
        return f"{{% for {args} %}}"
    
    # Include Directives
    def _include_directive(self, args: str) -> str:
        """@include directive for template inclusion."""
        parts = [p.strip().strip("'\"") for p in args.split(',')]
        template = parts[0]
        
        if len(parts) > 1:
            # Has data parameter
            data = parts[1]
            return f"{{% include '{template}' with {data} %}}"
        else:
            return f"{{% include '{template}' %}}"
    
    def _include_if_directive(self, args: str) -> str:
        """@includeIf directive for conditional inclusion."""
        parts = [p.strip().strip("'\"") for p in args.split(',')]
        template = parts[0]
        return f"{{% include '{template}' ignore missing %}}"
    
    def _include_when_directive(self, args: str) -> str:
        """@includeWhen directive for conditional inclusion."""
        parts = [p.strip() for p in args.split(',')]
        condition = parts[0]
        template = parts[1].strip().strip("'\"") if len(parts) > 1 else ''
        
        return f"{{% if {condition} %}}{{% include '{template}' %}}{{% endif %}}"
    
    # Asset Directives
    def _asset_directive(self, args: str) -> str:
        """@asset directive for asset URLs."""
        path = args.strip().strip("'\"")
        return f"{{{{ asset('{path}') }}}}"
    
    def _url_directive(self, args: str) -> str:
        """@url directive for URL generation."""
        path = args.strip().strip("'\"")
        return f"{{{{ url('{path}') }}}}"
    
    def _route_directive(self, args: str) -> str:
        """@route directive for named route URLs."""
        parts = [p.strip().strip("'\"") for p in args.split(',')]
        route_name = parts[0]
        
        if len(parts) > 1:
            # Has parameters
            params = ', '.join(parts[1:])
            return f"{{{{ route('{route_name}', {params}) }}}}"
        else:
            return f"{{{{ route('{route_name}') }}}}"


class DirectiveCompiler:
    """
    Directive compiler that integrates with Jinja2 engine.
    """
    
    def __init__(self):
        """Initialize directive compiler."""
        self.directives = SecureDirectives()
    
    def compile_template(self, template_content: str) -> str:
        """
        Compile template with directives.
        
        Args:
            template_content: Raw template content
            
        Returns:
            Compiled template ready for Jinja2
        """
        return self.directives.compile(template_content)
    
    def register_directive(self, name: str, callback: Callable):
        """Register custom directive."""
        self.directives.register(name, callback)


# Global directive compiler instance
directive_compiler = DirectiveCompiler()

# Helper functions
def compile_directives(template_content: str) -> str:
    """Compile template directives to Jinja2 syntax."""
    return directive_compiler.compile_template(template_content)

def register_directive(name: str, callback: Callable):
    """Register a custom template directive."""
    directive_compiler.register_directive(name, callback)

def create_auth_directive(user_provider: Optional[Callable] = None):
    """Create authentication directive with user provider."""
    def auth_check():
        if user_provider:
            return user_provider()
        return None
    
    register_directive('auth_user', lambda args: f"{{{{ {auth_check()} }}}}")

def create_permission_directive(permission_checker: Optional[Callable] = None):
    """Create permission directive with permission checker."""
    def can_check(permission: str, model=None):
        if permission_checker:
            return permission_checker(permission, model)
        return False
    
    register_directive('permission', 
                      lambda args: f"{{{{ can_check('{args}') }}}}")