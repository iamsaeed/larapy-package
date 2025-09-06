"""
Base guard class for Larapy authentication.

This module provides the abstract base guard class that all authentication
guards must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..user import AuthenticatableUser
from ..providers import UserProvider


class Guard(ABC):
    """Base authentication guard."""
    
    def __init__(self, provider: UserProvider, config: Dict[str, Any]):
        self.provider = provider
        self.config = config
        self._user: Optional[AuthenticatableUser] = None
        
    @abstractmethod
    async def attempt(self, credentials: Dict[str, Any], remember: bool = False) -> bool:
        """Attempt to authenticate a user."""
        pass
        
    @abstractmethod
    async def login(self, user: AuthenticatableUser, remember: bool = False) -> None:
        """Log in a user."""
        pass
        
    @abstractmethod
    async def logout(self) -> None:
        """Log out the current user."""
        pass
        
    @abstractmethod
    def user(self) -> Optional[AuthenticatableUser]:
        """Get the currently authenticated user."""
        pass
        
    @abstractmethod
    async def validate(self, credentials: Dict[str, Any]) -> bool:
        """Validate user credentials without logging in."""
        pass
        
    def check(self) -> bool:
        """Check if a user is authenticated."""
        return self.user() is not None
        
    def guest(self) -> bool:
        """Check if the current user is a guest."""
        return not self.check()
        
    def id(self) -> Optional[Any]:
        """Get the ID of the currently authenticated user."""
        user = self.user()
        return user.get_auth_identifier() if user else None
        
    async def once(self, credentials: Dict[str, Any]) -> bool:
        """Log a user in for a single request."""
        if await self.validate(credentials):
            user = await self.provider.retrieve_by_credentials(credentials)
            if user:
                self._user = user
                return True
        return False
        
    def set_user(self, user: AuthenticatableUser) -> None:
        """Set the current user."""
        self._user = user
        
    def has_user(self) -> bool:
        """Check if a user is set."""
        return self._user is not None