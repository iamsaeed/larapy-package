"""
Session-based authentication guard for Larapy.

This guard handles authentication using server-side sessions.
"""

from typing import Dict, Any, Optional
from .guard import Guard
from ..user import AuthenticatableUser
from ..providers import UserProvider


class SessionGuard(Guard):
    """Session-based authentication guard."""
    
    def __init__(self, provider: UserProvider, config: Dict[str, Any]):
        super().__init__(provider, config)
        self.session_key = config.get('session_key', 'auth_user_id')
        self.remember_key = config.get('remember_key', 'auth_remember_token')
        self._current_session = None
        
    def set_session(self, session: Any) -> None:
        """Set the current session object."""
        self._current_session = session
        
    async def attempt(self, credentials: Dict[str, Any], remember: bool = False) -> bool:
        """Attempt to authenticate a user with credentials."""
        # Validate credentials
        if not await self.validate(credentials):
            return False
            
        # Retrieve user
        user = await self.provider.retrieve_by_credentials(credentials)
        if not user:
            return False
            
        # Log in the user
        await self.login(user, remember)
        return True
        
    async def login(self, user: AuthenticatableUser, remember: bool = False) -> None:
        """Log in a user."""
        self._user = user
        
        # Store user ID in session
        if self._current_session:
            self._current_session[self.session_key] = user.get_auth_identifier()
            
        # Handle remember me functionality
        if remember:
            await self._queue_remember_cookie(user)
            
    async def logout(self) -> None:
        """Log out the current user."""
        if self._current_session and self.session_key in self._current_session:
            del self._current_session[self.session_key]
            
        # Clear remember token
        if self._user:
            await self._clear_remember_token()
            
        self._user = None
        
    def user(self) -> Optional[AuthenticatableUser]:
        """Get the currently authenticated user."""
        if self._user is not None:
            return self._user
            
        # Try to get user from session
        if self._current_session and self.session_key in self._current_session:
            user_id = self._current_session[self.session_key]
            if user_id:
                self._user = self.provider.retrieve_by_id(user_id)
                
        # If no session user, try remember token
        if self._user is None:
            self._user = self._user_from_remember_token()
            
        return self._user
        
    async def validate(self, credentials: Dict[str, Any]) -> bool:
        """Validate user credentials without logging in."""
        return await self.provider.validate_credentials(credentials)
        
    async def _queue_remember_cookie(self, user: AuthenticatableUser) -> None:
        """Queue a remember me cookie."""
        # Generate remember token
        import secrets
        token = secrets.token_urlsafe(32)
        
        # Store token with user
        await user.set_remember_token(token)
        
        # In a real implementation, this would set an HTTP cookie
        # For now, we'll just store it in a way that can be retrieved
        
    def _user_from_remember_token(self) -> Optional[AuthenticatableUser]:
        """Get user from remember token cookie."""
        # In a real implementation, this would read from HTTP cookies
        # For now, this is a placeholder
        return None
        
    async def _clear_remember_token(self) -> None:
        """Clear the remember token."""
        if self._user:
            await self._user.set_remember_token(None)
            
    def via_remember(self) -> bool:
        """Check if user was authenticated via remember token."""
        # This would track how the user was authenticated
        return False