"""
Authenticatable user interface and implementations for Larapy.

This module provides the base interface for authenticatable users.
"""

from typing import Any, Optional
from ..orm import Model


class AuthenticatableUser:
    """Interface for authenticatable users."""
    
    def get_auth_identifier_name(self) -> str:
        """Get the name of the unique identifier for the user."""
        raise NotImplementedError
        
    def get_auth_identifier(self) -> Any:
        """Get the unique identifier for the user."""
        raise NotImplementedError
        
    def get_auth_password(self) -> str:
        """Get the password for the user."""
        raise NotImplementedError
        
    async def set_remember_token(self, token: Optional[str]) -> None:
        """Set the remember token for the user."""
        raise NotImplementedError
        
    def get_remember_token(self) -> Optional[str]:
        """Get the remember token for the user."""
        raise NotImplementedError
        
    def get_remember_token_name(self) -> str:
        """Get the column name for the remember token."""
        raise NotImplementedError


class User(Model, AuthenticatableUser):
    """Default User model with authentication capabilities."""
    
    table = 'users'
    fillable = ['name', 'email', 'password']
    hidden = ['password', 'remember_token']
    
    # Authentication configuration
    auth_identifier_name = 'id'
    auth_password_name = 'password'
    remember_token_name = 'remember_token'
    
    def get_auth_identifier_name(self) -> str:
        """Get the name of the unique identifier for the user."""
        return self.auth_identifier_name
        
    def get_auth_identifier(self) -> Any:
        """Get the unique identifier for the user."""
        return getattr(self, self.auth_identifier_name)
        
    def get_auth_password(self) -> str:
        """Get the password for the user."""
        return getattr(self, self.auth_password_name, '')
        
    async def set_remember_token(self, token: Optional[str]) -> None:
        """Set the remember token for the user."""
        setattr(self, self.remember_token_name, token)
        await self.save()
        
    def get_remember_token(self) -> Optional[str]:
        """Get the remember token for the user."""
        return getattr(self, self.remember_token_name, None)
        
    def get_remember_token_name(self) -> str:
        """Get the column name for the remember token."""
        return self.remember_token_name
        
    async def set_api_token(self, token: Optional[str]) -> None:
        """Set the API token for the user."""
        self.api_token = token
        await self.save()
        
    def get_api_token(self) -> Optional[str]:
        """Get the API token for the user."""
        return getattr(self, 'api_token', None)
        
    # Additional user methods
    def is_verified(self) -> bool:
        """Check if the user's email is verified."""
        return getattr(self, 'email_verified_at', None) is not None
        
    async def mark_email_as_verified(self) -> None:
        """Mark the user's email as verified."""
        from datetime import datetime
        self.email_verified_at = datetime.now()
        await self.save()
        
    def has_role(self, role_names) -> bool:
        """Check if the user has a specific role or roles."""
        from .models import HasRoles
        if not hasattr(self, '_has_roles_trait'):
            # Add HasRoles functionality
            for method_name in dir(HasRoles):
                if not method_name.startswith('_') and hasattr(HasRoles, method_name):
                    method = getattr(HasRoles, method_name)
                    if callable(method):
                        setattr(self, method_name, method.__get__(self, self.__class__))
            self._has_roles_trait = True
        
        return self.has_role(role_names)
        
    def has_permission(self, permission_names) -> bool:
        """Check if the user has a specific permission or permissions."""
        if not hasattr(self, '_has_roles_trait'):
            # Add HasRoles functionality
            from .models import HasRoles
            for method_name in dir(HasRoles):
                if not method_name.startswith('_') and hasattr(HasRoles, method_name):
                    method = getattr(HasRoles, method_name)
                    if callable(method):
                        setattr(self, method_name, method.__get__(self, self.__class__))
            self._has_roles_trait = True
        
        return self.has_permission(permission_names)
        
    def can(self, ability: str, *args) -> bool:
        """Check if the user can perform an ability using Gate system."""
        from .gate import Gate
        return Gate.for_user(self).allows(ability, *args)
        
    def cannot(self, ability: str, *args) -> bool:
        """Check if the user cannot perform an ability."""
        return not self.can(ability, *args)
    
    def authorize(self, ability: str, *args):
        """Authorize ability or raise exception."""
        from .gate import Gate, AuthorizationError
        if not self.can(ability, *args):
            raise AuthorizationError(f"Access denied for ability: {ability}")
    
    # Authorization convenience methods
    def is_admin(self) -> bool:
        """Check if user is admin.""" 
        return self.has_role(['admin', 'super_admin'])
    
    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        return self.has_role('super_admin')
    
    def can_access_admin(self) -> bool:
        """Check if user can access admin panel."""
        return self.can('view_admin') or self.is_admin()
    
    # Role and permission management methods
    def assign_role(self, role):
        """Assign role to user."""
        if not hasattr(self, '_has_roles_trait'):
            from .models import HasRoles
            for method_name in dir(HasRoles):
                if not method_name.startswith('_') and hasattr(HasRoles, method_name):
                    method = getattr(HasRoles, method_name)
                    if callable(method):
                        setattr(self, method_name, method.__get__(self, self.__class__))
            self._has_roles_trait = True
        
        return self.assign_role(role)
    
    def give_permission_to(self, permission):
        """Give permission to user.""" 
        if not hasattr(self, '_has_roles_trait'):
            from .models import HasRoles
            for method_name in dir(HasRoles):
                if not method_name.startswith('_') and hasattr(HasRoles, method_name):
                    method = getattr(HasRoles, method_name)
                    if callable(method):
                        setattr(self, method_name, method.__get__(self, self.__class__))
            self._has_roles_trait = True
        
        return self.give_permission_to(permission)


class AuthenticatableMixin:
    """Mixin to add authentication capabilities to any model."""
    
    # Configuration
    auth_identifier_name = 'id'
    auth_password_name = 'password'
    remember_token_name = 'remember_token'
    
    def get_auth_identifier_name(self) -> str:
        """Get the name of the unique identifier for the user."""
        return getattr(self, 'auth_identifier_name', 'id')
        
    def get_auth_identifier(self) -> Any:
        """Get the unique identifier for the user."""
        return getattr(self, self.get_auth_identifier_name())
        
    def get_auth_password(self) -> str:
        """Get the password for the user."""
        password_field = getattr(self, 'auth_password_name', 'password')
        return getattr(self, password_field, '')
        
    async def set_remember_token(self, token: Optional[str]) -> None:
        """Set the remember token for the user."""
        token_field = getattr(self, 'remember_token_name', 'remember_token')
        setattr(self, token_field, token)
        if hasattr(self, 'save'):
            await self.save()
        
    def get_remember_token(self) -> Optional[str]:
        """Get the remember token for the user."""
        token_field = getattr(self, 'remember_token_name', 'remember_token')
        return getattr(self, token_field, None)
        
    def get_remember_token_name(self) -> str:
        """Get the column name for the remember token."""
        return getattr(self, 'remember_token_name', 'remember_token')