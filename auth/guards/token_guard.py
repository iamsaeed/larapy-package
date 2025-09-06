"""
Token-based authentication guard for Larapy.

This guard handles authentication using API tokens.
"""

from typing import Dict, Any, Optional
from .guard import Guard
from ..user import AuthenticatableUser
from ..providers import UserProvider


class TokenGuard(Guard):
    """Token-based authentication guard."""
    
    def __init__(self, provider: UserProvider, config: Dict[str, Any]):
        super().__init__(provider, config)
        self.hash_tokens = config.get('hash', True)
        self.token_key = config.get('token_key', 'api_token')
        self.storage_key = config.get('storage_key', 'api_token')
        self._current_request = None
        
    def set_request(self, request: Any) -> None:
        """Set the current request object."""
        self._current_request = request
        
    async def attempt(self, credentials: Dict[str, Any], remember: bool = False) -> bool:
        """Attempt to authenticate a user with credentials."""
        # Token guard doesn't support attempt with credentials
        # Tokens are typically pre-generated
        return False
        
    async def login(self, user: AuthenticatableUser, remember: bool = False) -> None:
        """Log in a user."""
        self._user = user
        
    async def logout(self) -> None:
        """Log out the current user."""
        # For token authentication, logout typically means revoking the token
        if self._user:
            # In a real implementation, you might want to revoke the current token
            pass
        self._user = None
        
    def user(self) -> Optional[AuthenticatableUser]:
        """Get the currently authenticated user."""
        if self._user is not None:
            return self._user
            
        # Get token from request
        token = self._get_token_from_request()
        if not token:
            return None
            
        # Hash token if needed
        if self.hash_tokens:
            token = self._hash_token(token)
            
        # Retrieve user by token
        self._user = self.provider.retrieve_by_token(self.storage_key, token)
        return self._user
        
    async def validate(self, credentials: Dict[str, Any]) -> bool:
        """Validate user credentials without logging in."""
        # Token guard validates by checking if token exists
        token = credentials.get(self.token_key)
        if not token:
            return False
            
        if self.hash_tokens:
            token = self._hash_token(token)
            
        user = self.provider.retrieve_by_token(self.storage_key, token)
        return user is not None
        
    def _get_token_from_request(self) -> Optional[str]:
        """Extract token from the request."""
        if not self._current_request:
            return None
            
        # Try to get token from Authorization header
        auth_header = getattr(self._current_request, 'headers', {}).get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
            
        # Try to get token from query parameter
        if hasattr(self._current_request, 'query_params'):
            token = self._current_request.query_params.get(self.token_key)
            if token:
                return token
                
        # Try to get token from form data
        if hasattr(self._current_request, 'form'):
            token = self._current_request.form.get(self.token_key)
            if token:
                return token
                
        return None
        
    def _hash_token(self, token: str) -> str:
        """Hash the token if hashing is enabled."""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()
        
    async def generate_token(self, user: AuthenticatableUser) -> str:
        """Generate a new API token for a user."""
        import secrets
        token = secrets.token_urlsafe(40)
        
        # Store the token (hashed if needed) with the user
        storage_token = self._hash_token(token) if self.hash_tokens else token
        await user.set_api_token(storage_token)
        
        # Return the plain token (what the client will use)
        return token
        
    async def revoke_token(self, user: AuthenticatableUser) -> bool:
        """Revoke a user's API token."""
        await user.set_api_token(None)
        return True