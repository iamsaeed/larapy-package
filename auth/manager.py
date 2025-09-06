"""
Authentication manager for Larapy.

This module provides the main authentication manager that handles multiple
authentication drivers and user authentication.
"""

from typing import Dict, Any, Optional, Type, Union
from abc import ABC, abstractmethod
from .guards import Guard, SessionGuard, TokenGuard, JwtGuard
from .providers import UserProvider, LarapyUserProvider
from .user import AuthenticatableUser


class AuthManager:
    """Main authentication manager."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.guards: Dict[str, Guard] = {}
        self.user_providers: Dict[str, UserProvider] = {}
        self.default_guard = config.get('default', 'web')
        
        # Initialize guards and providers from config
        self._create_user_providers()
        self._create_guards()
        
    def guard(self, name: Optional[str] = None) -> Guard:
        """Get a guard instance."""
        guard_name = name or self.default_guard
        
        if guard_name not in self.guards:
            self._create_guard(guard_name)
            
        return self.guards[guard_name]
        
    def user_provider(self, name: str) -> UserProvider:
        """Get a user provider instance."""
        if name not in self.user_providers:
            raise ValueError(f"User provider '{name}' not configured")
        return self.user_providers[name]
        
    async def attempt(self, credentials: Dict[str, Any], remember: bool = False,
                     guard: Optional[str] = None) -> bool:
        """Attempt to authenticate a user with credentials."""
        guard_instance = self.guard(guard)
        return await guard_instance.attempt(credentials, remember)
        
    async def login(self, user: AuthenticatableUser, remember: bool = False,
                   guard: Optional[str] = None) -> None:
        """Log in a user."""
        guard_instance = self.guard(guard)
        await guard_instance.login(user, remember)
        
    async def logout(self, guard: Optional[str] = None) -> None:
        """Log out the current user."""
        guard_instance = self.guard(guard)
        await guard_instance.logout()
        
    def user(self, guard: Optional[str] = None) -> Optional[AuthenticatableUser]:
        """Get the currently authenticated user."""
        guard_instance = self.guard(guard)
        return guard_instance.user()
        
    def id(self, guard: Optional[str] = None) -> Optional[Any]:
        """Get the ID of the currently authenticated user."""
        guard_instance = self.guard(guard)
        return guard_instance.id()
        
    def check(self, guard: Optional[str] = None) -> bool:
        """Check if a user is authenticated."""
        guard_instance = self.guard(guard)
        return guard_instance.check()
        
    def guest(self, guard: Optional[str] = None) -> bool:
        """Check if the current user is a guest."""
        guard_instance = self.guard(guard)
        return guard_instance.guest()
        
    async def validate(self, credentials: Dict[str, Any], guard: Optional[str] = None) -> bool:
        """Validate user credentials without logging in."""
        guard_instance = self.guard(guard)
        return await guard_instance.validate(credentials)
        
    def _create_user_providers(self) -> None:
        """Create user provider instances from config."""
        providers_config = self.config.get('providers', {})
        
        for name, provider_config in providers_config.items():
            driver = provider_config.get('driver', 'larapy')
            
            if driver == 'larapy':
                model_class = provider_config.get('model')
                if not model_class:
                    raise ValueError(f"Model class required for Larapy provider '{name}'")
                self.user_providers[name] = LarapyUserProvider(model_class)
            else:
                raise ValueError(f"Unsupported user provider driver: {driver}")
                
    def _create_guards(self) -> None:
        """Create guard instances from config."""
        guards_config = self.config.get('guards', {})
        
        for name, guard_config in guards_config.items():
            self._create_guard(name, guard_config)
            
    def _create_guard(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Create a single guard instance."""
        if config is None:
            config = self.config.get('guards', {}).get(name, {})
            
        driver = config.get('driver', 'session')
        provider_name = config.get('provider')
        
        if not provider_name:
            raise ValueError(f"Provider required for guard '{name}'")
            
        provider = self.user_provider(provider_name)
        
        if driver == 'session':
            self.guards[name] = SessionGuard(provider, config)
        elif driver == 'token':
            self.guards[name] = TokenGuard(provider, config)
        elif driver == 'jwt':
            self.guards[name] = JwtGuard(provider, config)
        else:
            raise ValueError(f"Unsupported guard driver: {driver}")
            
    def extend_guard(self, name: str, guard_class: Type[Guard]) -> None:
        """Register a custom guard driver."""
        # This would allow custom guard implementations
        pass
        
    def extend_provider(self, name: str, provider_class: Type[UserProvider]) -> None:
        """Register a custom user provider driver."""
        # This would allow custom provider implementations
        pass


# Default authentication configuration
DEFAULT_AUTH_CONFIG = {
    'default': 'web',
    'guards': {
        'web': {
            'driver': 'session',
            'provider': 'users'
        },
        'api': {
            'driver': 'token',
            'provider': 'users',
            'hash': False
        },
        'jwt': {
            'driver': 'jwt',
            'provider': 'users'
        }
    },
    'providers': {
        'users': {
            'driver': 'larapy',
            'model': 'app.models.User'
        }
    },
    'passwords': {
        'users': {
            'provider': 'users',
            'table': 'password_resets',
            'expire': 60
        }
    }
}