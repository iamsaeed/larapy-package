"""
Gate system for authorization in Larapy.

Provides a flexible authorization system with policies and custom rules.
"""

from typing import Dict, Any, Callable, Optional, List, Union
from abc import ABC, abstractmethod
from functools import wraps


class Gate:
    """Authorization gate system."""
    
    _instance = None
    
    def __init__(self):
        self.abilities: Dict[str, Callable] = {}
        self.policies: Dict[str, type] = {}
        self.before_callbacks: List[Callable] = []
        self.after_callbacks: List[Callable] = []
        self.current_user = None
    
    @classmethod
    def get_instance(cls) -> 'Gate':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def define(cls, ability: str, callback: Callable):
        """
        Define an authorization ability.
        
        Args:
            ability: Name of the ability
            callback: Function to check authorization
        """
        instance = cls.get_instance()
        instance.abilities[ability] = callback
    
    @classmethod
    def resource(cls, name: str, policy_class: type, parameters: List[str] = None):
        """
        Register a resource policy.
        
        Args:
            name: Resource name
            policy_class: Policy class
            parameters: List of parameter names
        """
        instance = cls.get_instance()
        instance.policies[name] = policy_class
        
        # Register standard CRUD abilities
        abilities = parameters or ['view', 'create', 'update', 'delete']
        for ability in abilities:
            method_name = ability
            if hasattr(policy_class, method_name):
                cls.define(f"{name}.{ability}", 
                          lambda user, *args, method=method_name, policy=policy_class: 
                          getattr(policy(user), method)(*args))
    
    @classmethod
    def policy(cls, model_class: type, policy_class: type):
        """
        Register a model policy.
        
        Args:
            model_class: Model class
            policy_class: Policy class
        """
        instance = cls.get_instance()
        model_name = model_class.__name__.lower()
        instance.policies[model_name] = policy_class
    
    @classmethod
    def before(cls, callback: Callable):
        """
        Register a before callback that runs before all authorization checks.
        
        Args:
            callback: Function to run before authorization
        """
        instance = cls.get_instance()
        instance.before_callbacks.append(callback)
    
    @classmethod
    def after(cls, callback: Callable):
        """
        Register an after callback that runs after authorization checks.
        
        Args:
            callback: Function to run after authorization
        """
        instance = cls.get_instance()
        instance.after_callbacks.append(callback)
    
    @classmethod
    def for_user(cls, user) -> 'Gate':
        """
        Create gate instance for specific user.
        
        Args:
            user: User instance
            
        Returns:
            Gate instance with user context
        """
        instance = cls.get_instance()
        instance.current_user = user
        return instance
    
    @classmethod
    def allows(cls, ability: str, *arguments) -> bool:
        """
        Check if ability is allowed.
        
        Args:
            ability: Ability name
            *arguments: Additional arguments
            
        Returns:
            True if allowed
        """
        instance = cls.get_instance()
        return instance._check(ability, arguments, True)
    
    @classmethod
    def denies(cls, ability: str, *arguments) -> bool:
        """
        Check if ability is denied.
        
        Args:
            ability: Ability name
            *arguments: Additional arguments
            
        Returns:
            True if denied
        """
        return not cls.allows(ability, *arguments)
    
    @classmethod
    def authorize(cls, ability: str, *arguments):
        """
        Authorize ability or raise exception.
        
        Args:
            ability: Ability name
            *arguments: Additional arguments
            
        Raises:
            AuthorizationError: If not authorized
        """
        if not cls.allows(ability, *arguments):
            raise AuthorizationError(f"Access denied for ability: {ability}")
    
    @classmethod
    def check(cls, abilities: Union[str, List[str]], *arguments) -> bool:
        """
        Check multiple abilities (all must pass).
        
        Args:
            abilities: Ability name or list of abilities
            *arguments: Additional arguments
            
        Returns:
            True if all abilities are allowed
        """
        if isinstance(abilities, str):
            abilities = [abilities]
        
        return all(cls.allows(ability, *arguments) for ability in abilities)
    
    @classmethod
    def any(cls, abilities: List[str], *arguments) -> bool:
        """
        Check if any of the abilities are allowed.
        
        Args:
            abilities: List of ability names
            *arguments: Additional arguments
            
        Returns:
            True if any ability is allowed
        """
        return any(cls.allows(ability, *arguments) for ability in abilities)
    
    def _check(self, ability: str, arguments: tuple, default: bool) -> bool:
        """
        Internal method to check authorization.
        
        Args:
            ability: Ability name
            arguments: Arguments tuple
            default: Default return value
            
        Returns:
            Authorization result
        """
        user = self.current_user
        
        # Run before callbacks
        for callback in self.before_callbacks:
            result = callback(user, ability, *arguments)
            if result is not None:
                return bool(result)
        
        # Check specific ability
        result = self._check_ability(ability, user, arguments)
        
        if result is None:
            result = default
        
        # Run after callbacks
        for callback in self.after_callbacks:
            after_result = callback(user, ability, result, *arguments)
            if after_result is not None:
                result = bool(after_result)
        
        return bool(result)
    
    def _check_ability(self, ability: str, user, arguments: tuple) -> Optional[bool]:
        """
        Check specific ability.
        
        Args:
            ability: Ability name
            user: User instance
            arguments: Arguments tuple
            
        Returns:
            Authorization result or None
        """
        # Check direct ability registration
        if ability in self.abilities:
            callback = self.abilities[ability]
            return callback(user, *arguments)
        
        # Check policy-based abilities
        parts = ability.split('.')
        if len(parts) == 2:
            resource, action = parts
            
            if resource in self.policies:
                policy_class = self.policies[resource]
                policy = policy_class(user)
                
                if hasattr(policy, action):
                    method = getattr(policy, action)
                    return method(*arguments)
        
        return None


class Policy(ABC):
    """Base policy class."""
    
    def __init__(self, user):
        """
        Initialize policy with user.
        
        Args:
            user: Current user
        """
        self.user = user
    
    def before(self, *arguments) -> Optional[bool]:
        """
        Run before any authorization check.
        
        Returns:
            True/False to override, None to continue
        """
        return None
    
    def after(self, result: bool, *arguments) -> Optional[bool]:
        """
        Run after authorization check.
        
        Args:
            result: Current authorization result
            
        Returns:
            True/False to override, None to keep current result
        """
        return None


class AuthorizationError(Exception):
    """Exception raised when authorization fails."""
    pass


# Authorization decorators
def authorize(ability: str):
    """
    Decorator to authorize access to functions.
    
    Args:
        ability: Required ability name
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            Gate.authorize(ability, *args)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def can(ability: str):
    """
    Decorator that passes authorization result as first argument.
    
    Args:
        ability: Ability to check
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            allowed = Gate.allows(ability, *args)
            return func(allowed, *args, **kwargs)
        return wrapper
    return decorator


def requires_role(role_names: Union[str, List[str]]):
    """
    Decorator to require specific roles.
    
    Args:
        role_names: Required role name(s)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would typically check current user's roles
            # Implementation depends on how current user is accessed
            return func(*args, **kwargs)
        return wrapper
    return decorator


def requires_permission(permission_names: Union[str, List[str]]):
    """
    Decorator to require specific permissions.
    
    Args:
        permission_names: Required permission name(s)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would typically check current user's permissions
            # Implementation depends on how current user is accessed
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Policy registration helpers
def register_policies():
    """Register default policies."""
    # This would register common policies
    pass


# Example policies
class UserPolicy(Policy):
    """Example policy for User model."""
    
    def view(self, user_model):
        """Check if user can view another user."""
        # Users can view their own profile or admins can view anyone
        return (self.user.id == user_model.id or 
                self.user.has_role('admin'))
    
    def update(self, user_model):
        """Check if user can update another user."""
        # Users can update their own profile or admins can update anyone
        return (self.user.id == user_model.id or 
                self.user.has_role('admin'))
    
    def delete(self, user_model):
        """Check if user can delete another user.""" 
        # Only admins can delete users, and not themselves
        return (self.user.has_role('admin') and 
                self.user.id != user_model.id)
    
    def create(self):
        """Check if user can create new users."""
        return self.user.has_role('admin')


# Global gate instance
gate = Gate.get_instance()


# Helper functions for common authorization patterns
def user_owns_resource(user, resource) -> bool:
    """Check if user owns a resource."""
    if hasattr(resource, 'user_id'):
        return user.id == resource.user_id
    elif hasattr(resource, 'owner_id'):
        return user.id == resource.owner_id
    return False


def user_is_admin(user) -> bool:
    """Check if user is admin.""" 
    if hasattr(user, 'has_role'):
        return user.has_role('admin')
    return False


def user_has_permission(user, permission: str) -> bool:
    """Check if user has permission."""
    if hasattr(user, 'has_permission'):
        return user.has_permission(permission)
    return False