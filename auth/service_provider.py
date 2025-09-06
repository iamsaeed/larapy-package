"""
Authorization service provider for Larapy.

Registers authorization components and sets up default configuration.
"""

from ..providers.service_provider import ServiceProvider
from .authorization import AuthorizationManager, authorization_manager
from .gate import Gate, UserPolicy
from .models import Role, Permission


class AuthorizationServiceProvider(ServiceProvider):
    """Service provider for authorization system."""
    
    def register(self):
        """Register authorization services.""" 
        # Register authorization manager as singleton
        self.app.singleton('auth.gate', lambda app: Gate.get_instance())
        self.app.singleton('auth.authorization', lambda app: authorization_manager)
        
        # Register model classes
        self.app.bind('auth.role', lambda app: Role)
        self.app.bind('auth.permission', lambda app: Permission)
    
    def boot(self):
        """Boot the authorization system."""
        # Setup default abilities
        authorization_manager.setup_default_abilities()
        
        # Register default policies
        self._register_default_policies()
        
        # Create default roles and permissions if configured
        if self.app.config.get('auth.create_default_roles', True):
            self._create_default_roles()
    
    def _register_default_policies(self):
        """Register default policies.""" 
        from .user import User
        
        # Register user policy
        Gate.policy(User, UserPolicy)
        
        # Register any additional default policies
        policies = self.app.config.get('auth.policies', {})
        for model_name, policy_class in policies.items():
            try:
                # Try to import the model class
                model_class = self.app.resolve(model_name)
                Gate.policy(model_class, policy_class)
            except:
                # Model not found, skip
                pass
    
    def _create_default_roles(self):
        """Create default roles and permissions."""
        try:
            authorization_manager.create_default_roles_and_permissions()
        except Exception as e:
            # Database might not be ready, skip for now
            pass


def create_authorization_config():
    """Create default authorization configuration."""
    return {
        'auth': {
            'create_default_roles': True,
            'policies': {
                # Map of model names to policy classes
            },
            'default_permissions': [
                'view_admin_panel',
                'manage_users', 
                'manage_roles',
                'manage_permissions',
                'view_reports',
                'manage_settings',
                'manage_content',
                'moderate_content'
            ],
            'default_roles': {
                'super_admin': {
                    'display_name': 'Super Administrator',
                    'description': 'Has all system permissions',
                    'permissions': 'all'  # Special value for all permissions
                },
                'admin': {
                    'display_name': 'Administrator', 
                    'description': 'System administrator',
                    'permissions': [
                        'view_admin_panel',
                        'manage_users',
                        'view_reports', 
                        'manage_content'
                    ]
                },
                'moderator': {
                    'display_name': 'Moderator',
                    'description': 'Content moderator',
                    'permissions': [
                        'view_admin_panel',
                        'moderate_content'
                    ]
                },
                'user': {
                    'display_name': 'User',
                    'description': 'Regular user',
                    'permissions': []
                }
            }
        }
    }