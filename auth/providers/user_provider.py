"""
Base user provider class for Larapy authentication.

User providers handle retrieving and validating user data.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..user import AuthenticatableUser


class UserProvider(ABC):
    """Base user provider interface."""
    
    @abstractmethod
    def retrieve_by_id(self, identifier: Any) -> Optional[AuthenticatableUser]:
        """Retrieve a user by their unique identifier."""
        pass
        
    @abstractmethod
    async def retrieve_by_credentials(self, credentials: Dict[str, Any]) -> Optional[AuthenticatableUser]:
        """Retrieve a user by their credentials."""
        pass
        
    @abstractmethod
    def retrieve_by_token(self, identifier: str, token: str) -> Optional[AuthenticatableUser]:
        """Retrieve a user by their remember token."""
        pass
        
    @abstractmethod
    async def update_remember_token(self, user: AuthenticatableUser, token: Optional[str]) -> None:
        """Update the remember token for the user."""
        pass
        
    @abstractmethod
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate the user's credentials."""
        pass