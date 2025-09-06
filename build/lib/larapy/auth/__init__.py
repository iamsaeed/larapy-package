"""
Authentication module for Larapy.

Provides user authentication, authorization, and access control functionality.
"""

from .manager import AuthManager
from .guards import Guard, SessionGuard, TokenGuard, JwtGuard
from .user import User, AuthenticatableUser, AuthenticatableMixin
from .providers import UserProvider, LarapyUserProvider
from .password import PasswordHasher, PasswordStrengthValidator, hash_password, check_password
from .models import Role, Permission, HasRoles
from .gate import Gate, Policy, AuthorizationError
from .authorization import (
    AuthorizationManager, AuthorizationMiddleware, RoleMiddleware, PermissionMiddleware,
    authorize, can, cannot, policy, AuthorizedUser
)

__all__ = [
    'AuthManager', 'Guard', 'SessionGuard', 'TokenGuard', 'JwtGuard',
    'User', 'AuthenticatableUser', 'AuthenticatableMixin',
    'UserProvider', 'LarapyUserProvider',
    'PasswordHasher', 'PasswordStrengthValidator', 'hash_password', 'check_password',
    'Role', 'Permission', 'HasRoles',
    'Gate', 'Policy', 'AuthorizationError',
    'AuthorizationManager', 'AuthorizationMiddleware', 'RoleMiddleware', 'PermissionMiddleware',
    'authorize', 'can', 'cannot', 'policy', 'AuthorizedUser'
]