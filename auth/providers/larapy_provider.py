"""
Larapy user provider for Larapy authentication.

This provider uses Larapy models to retrieve and validate users.
"""

from typing import Dict, Any, Optional, Type
from .user_provider import UserProvider
from ..user import AuthenticatableUser
from ...orm import Model
import asyncio


class LarapyUserProvider(UserProvider):
    """Larapy-based user provider."""
    
    def __init__(self, model_class: Type[Model]):
        self.model_class = model_class
        
    def retrieve_by_id(self, identifier: Any) -> Optional[AuthenticatableUser]:
        """Retrieve a user by their unique identifier."""
        try:
            # Since we can't use await in a sync method, we need to handle this differently
            # In a real implementation, this would be refactored to be async
            return asyncio.run(self.model_class.find(identifier))
        except Exception:
            return None
            
    async def retrieve_by_credentials(self, credentials: Dict[str, Any]) -> Optional[AuthenticatableUser]:
        """Retrieve a user by their credentials."""
        # Build query based on credentials
        query = self.model_class.query()
        
        # Filter by all credentials except password
        for key, value in credentials.items():
            if key != 'password':
                query = query.where(key, value)
                
        # Get the first matching user
        return await query.first()
        
    def retrieve_by_token(self, identifier: str, token: str) -> Optional[AuthenticatableUser]:
        """Retrieve a user by their remember or API token."""
        try:
            return asyncio.run(
                self.model_class.query()
                .where(identifier, token)
                .first()
            )
        except Exception:
            return None
            
    async def update_remember_token(self, user: AuthenticatableUser, token: Optional[str]) -> None:
        """Update the remember token for the user."""
        if hasattr(user, 'remember_token'):
            user.remember_token = token
            await user.save()
            
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate the user's credentials."""
        user = await self.retrieve_by_credentials(credentials)
        if not user:
            return False
            
        # Check password if provided
        password = credentials.get('password')
        if password:
            return await self._check_password(user, password)
            
        return True
        
    async def _check_password(self, user: AuthenticatableUser, password: str) -> bool:
        """Check if the password matches the user's password."""
        if not hasattr(user, 'password') or not user.password:
            return False
            
        # Use password hashing to verify
        from ..password import PasswordHasher
        hasher = PasswordHasher()
        return hasher.check(password, user.password)
        
    def get_model_class(self) -> Type[Model]:
        """Get the model class used by this provider."""
        return self.model_class