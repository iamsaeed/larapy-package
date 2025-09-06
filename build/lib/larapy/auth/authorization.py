"""
Authorization system for Larapy.

Combines models, gates, and policies for comprehensive authorization.
"""

from typing import Dict, Any, Optional, List, Union, Callable
from .models import Role, Permission, HasRoles
from .gate import Gate, Policy, AuthorizationError
from ..middleware.middleware import Middleware
from ..http.request import Request
from ..http.response import Response, JsonResponse


class AuthorizationMiddleware(Middleware):
    """Middleware for route-level authorization."""
    
    def __init__(self, ability: str, *parameters):
        """
        Initialize authorization middleware.
        
        Args:
            ability: Required ability
            *parameters: Additional parameters for authorization check
        """
        self.ability = ability
        self.parameters = parameters
    
    async def handle(self, request: Request, next_handler: Callable) -> Response:
        """
        Handle authorization check.
        
        Args:
            request: HTTP request
            next_handler: Next middleware
            
        Returns:
            Response or authorization error
        """
        # Get current user from request
        user = getattr(request, 'user', None)
        
        if not user:
            return self._unauthorized_response(request)
        
        # Set user context for gate
        Gate.for_user(user)
        
        # Check authorization
        try:
            Gate.authorize(self.ability, *self.parameters)
        except AuthorizationError:
            return self._forbidden_response(request)
        
        # Proceed to next middleware
        return await next_handler(request)
    
    def _unauthorized_response(self, request: Request) -> Response:
        """Create unauthorized response."""
        if self._wants_json(request):
            return JsonResponse({
                'error': 'Unauthorized',
                'message': 'Authentication required'
            }, status=401)
        else:
            # Redirect to login page
            from ..http.response import RedirectResponse
            return RedirectResponse('/login', status=302)
    
    def _forbidden_response(self, request: Request) -> Response:
        """Create forbidden response."""
        if self._wants_json(request):
            return JsonResponse({
                'error': 'Forbidden',
                'message': f'Access denied for ability: {self.ability}'
            }, status=403)
        else:
            return Response('Access Denied', status=403)
    
    def _wants_json(self, request: Request) -> bool:
        """Check if request expects JSON response."""
        accept = request.header('Accept', '')
        return 'application/json' in accept or request.is_ajax()


class RoleMiddleware(Middleware):
    """Middleware to check user roles."""
    
    def __init__(self, *roles: str):
        """
        Initialize role middleware.
        
        Args:
            *roles: Required role names
        """
        self.roles = roles
    
    async def handle(self, request: Request, next_handler: Callable) -> Response:
        """Handle role check."""
        user = getattr(request, 'user', None)
        
        if not user:
            return self._unauthorized_response(request)
        
        # Check if user has any of the required roles
        if not user.has_any_role(list(self.roles)):
            return self._forbidden_response(request, f"Requires roles: {', '.join(self.roles)}")
        
        return await next_handler(request)
    
    def _unauthorized_response(self, request: Request) -> Response:
        """Create unauthorized response."""
        if self._wants_json(request):
            return JsonResponse({
                'error': 'Unauthorized',
                'message': 'Authentication required'
            }, status=401)
        else:
            from ..http.response import RedirectResponse
            return RedirectResponse('/login')
    
    def _forbidden_response(self, request: Request, message: str) -> Response:
        """Create forbidden response."""
        if self._wants_json(request):
            return JsonResponse({
                'error': 'Forbidden',
                'message': message
            }, status=403)
        else:
            return Response(f'Access Denied: {message}', status=403)
    
    def _wants_json(self, request: Request) -> bool:
        """Check if request expects JSON response."""
        accept = request.header('Accept', '')
        return 'application/json' in accept or request.is_ajax()


class PermissionMiddleware(Middleware):
    """Middleware to check user permissions."""
    
    def __init__(self, *permissions: str):
        """
        Initialize permission middleware.
        
        Args:
            *permissions: Required permission names
        """
        self.permissions = permissions
    
    async def handle(self, request: Request, next_handler: Callable) -> Response:
        """Handle permission check."""
        user = getattr(request, 'user', None)
        
        if not user:
            return self._unauthorized_response(request)
        
        # Check if user has any of the required permissions
        if not user.has_any_permission(list(self.permissions)):
            return self._forbidden_response(request, f"Requires permissions: {', '.join(self.permissions)}")
        
        return await next_handler(request)
    
    def _unauthorized_response(self, request: Request) -> Response:
        """Create unauthorized response."""
        if self._wants_json(request):
            return JsonResponse({
                'error': 'Unauthorized',
                'message': 'Authentication required'
            }, status=401)
        else:
            from ..http.response import RedirectResponse
            return RedirectResponse('/login')
    
    def _forbidden_response(self, request: Request, message: str) -> Response:
        """Create forbidden response."""
        if self._wants_json(request):
            return JsonResponse({
                'error': 'Forbidden',
                'message': message
            }, status=403)
        else:
            return Response(f'Access Denied: {message}', status=403)
    
    def _wants_json(self, request: Request) -> bool:
        """Check if request expects JSON response.""" 
        accept = request.header('Accept', '')
        return 'application/json' in accept or request.is_ajax()


class AuthorizationManager:
    """Manager for authorization system setup."""
    
    def __init__(self):
        self.policies_registered = False
        self.default_policies = {}
    
    def register_policies(self, policies: Dict[str, type]):
        """
        Register multiple policies.
        
        Args:
            policies: Dictionary mapping model names to policy classes
        """
        for model_name, policy_class in policies.items():
            Gate.policy(model_name, policy_class)
        
        self.policies_registered = True
    
    def setup_default_abilities(self):
        """Setup default authorization abilities."""
        # Super admin has all permissions
        Gate.before(lambda user, ability, *args: 
                   user.has_role('super_admin') if user else False)
        
        # Common abilities
        Gate.define('admin_panel', lambda user: user.has_role(['admin', 'super_admin']))
        Gate.define('manage_users', lambda user: user.has_permission('manage_users'))
        Gate.define('manage_roles', lambda user: user.has_permission('manage_roles'))
        Gate.define('view_admin', lambda user: user.has_role(['admin', 'super_admin']))
    
    def create_default_roles_and_permissions(self):
        """Create default roles and permissions if they don't exist."""
        # Default permissions
        default_permissions = [
            'view_admin_panel',
            'manage_users',
            'manage_roles', 
            'manage_permissions',
            'view_reports',
            'manage_settings',
            'manage_content',
            'moderate_content'
        ]
        
        for perm_name in default_permissions:
            Permission.create_if_not_exists(perm_name)
        
        # Default roles
        super_admin = Role.create_with_permissions(
            'super_admin',
            default_permissions,
            'Super Administrator',
            'Has all system permissions'
        )
        
        admin = Role.create_with_permissions(
            'admin', 
            ['view_admin_panel', 'manage_users', 'view_reports', 'manage_content'],
            'Administrator',
            'System administrator'
        )
        
        moderator = Role.create_with_permissions(
            'moderator',
            ['view_admin_panel', 'moderate_content'],
            'Moderator', 
            'Content moderator'
        )
        
        user = Role.create_with_permissions(
            'user',
            [],
            'User',
            'Regular user'
        )


# Helper functions for authorization
def authorize(ability: str, *arguments):
    """
    Authorize an ability or raise exception.
    
    Args:
        ability: Ability name
        *arguments: Additional arguments
        
    Raises:
        AuthorizationError: If not authorized
    """
    Gate.authorize(ability, *arguments)


def can(ability: str, *arguments) -> bool:
    """
    Check if current user can perform ability.
    
    Args:
        ability: Ability name
        *arguments: Additional arguments
        
    Returns:
        True if authorized
    """
    return Gate.allows(ability, *arguments)


def cannot(ability: str, *arguments) -> bool:
    """
    Check if current user cannot perform ability.
    
    Args:
        ability: Ability name
        *arguments: Additional arguments
        
    Returns:
        True if not authorized
    """
    return Gate.denies(ability, *arguments)


def policy(model_class: type, policy_class: type):
    """
    Register a policy for a model.
    
    Args:
        model_class: Model class
        policy_class: Policy class
    """
    Gate.policy(model_class, policy_class)


# Context manager for user authorization
class AuthorizedUser:
    """Context manager for setting current user for authorization."""
    
    def __init__(self, user):
        self.user = user
        self.previous_user = None
    
    def __enter__(self):
        gate = Gate.get_instance()
        self.previous_user = gate.current_user
        gate.current_user = self.user
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        gate = Gate.get_instance()
        gate.current_user = self.previous_user


# Global authorization manager
authorization_manager = AuthorizationManager()