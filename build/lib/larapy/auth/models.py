"""
Authorization models for Larapy.

Provides Role and Permission models for RBAC implementation.
"""

from typing import List, Optional, Any
from ..orm.model import Model


class Role(Model):
    """Role model for role-based access control."""
    
    table = 'roles'
    fillable = ['name', 'display_name', 'description', 'guard_name']
    
    def __init__(self, **attributes):
        super().__init__(**attributes)
        # Set default guard if not provided
        if 'guard_name' not in attributes:
            self.guard_name = 'web'
    
    def __str__(self) -> str:
        return self.display_name or self.name


class Permission(Model):
    """Permission model for granular access control."""
    
    table = 'permissions'
    fillable = ['name', 'display_name', 'description', 'guard_name']
    
    def __init__(self, **attributes):
        super().__init__(**attributes)
        # Set default guard if not provided
        if 'guard_name' not in attributes:
            self.guard_name = 'web'
    
    def __str__(self) -> str:
        return self.display_name or self.name


# Trait for models that can have roles and permissions
class HasRoles:
    """Trait for models that can have roles and permissions."""
    
    def has_role(self, role_names) -> bool:
        """
        Check if user has role(s).
        
        Args:
            role_names: Single role name or list of role names
            
        Returns:
            True if user has any of the roles
        """
        # Placeholder implementation - would integrate with database
        return False
    
    def has_permission(self, permission_names) -> bool:
        """
        Check if user has permission(s) directly or through roles.
        
        Args:
            permission_names: Single permission name or list of permission names
            
        Returns:
            True if user has any of the permissions
        """
        # Placeholder implementation - would integrate with database
        return False
    
    def assign_role(self, role) -> 'HasRoles':
        """
        Assign role to user.
        
        Args:
            role: Role instance or name
            
        Returns:
            Self for method chaining
        """
        # Placeholder implementation - would integrate with database
        return self
    
    def give_permission_to(self, permission) -> 'HasRoles':
        """
        Give permission directly to user.
        
        Args:
            permission: Permission instance or name
            
        Returns:
            Self for method chaining
        """
        # Placeholder implementation - would integrate with database
        return self