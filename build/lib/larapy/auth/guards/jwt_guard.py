"""
JWT-based authentication guard for Larapy.

This guard handles authentication using JSON Web Tokens.
"""

import jwt
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .guard import Guard
from ..user import AuthenticatableUser
from ..providers import UserProvider


class JwtGuard(Guard):
    """JWT-based authentication guard."""
    
    def __init__(self, provider: UserProvider, config: Dict[str, Any]):
        super().__init__(provider, config)
        self.secret = config.get('secret', 'your-jwt-secret-key')
        self.algorithm = config.get('algorithm', 'HS256')
        self.ttl = config.get('ttl', 3600)  # Token TTL in seconds
        self.refresh_ttl = config.get('refresh_ttl', 7200)  # Refresh token TTL
        self._current_request = None
        self._token = None
        
    def set_request(self, request: Any) -> None:
        """Set the current request object."""
        self._current_request = request
        
    async def attempt(self, credentials: Dict[str, Any], remember: bool = False) -> bool:
        """Attempt to authenticate a user with credentials."""
        if not await self.validate(credentials):
            return False
            
        user = await self.provider.retrieve_by_credentials(credentials)
        if not user:
            return False
            
        await self.login(user, remember)
        return True
        
    async def login(self, user: AuthenticatableUser, remember: bool = False) -> None:
        """Log in a user."""
        self._user = user
        # JWT tokens are stateless, so login just sets the user
        # The actual token is generated when requested
        
    async def logout(self) -> None:
        """Log out the current user."""
        # For JWT, logout typically means blacklisting the token
        # For now, we'll just clear the user
        self._user = None
        self._token = None
        
    def user(self) -> Optional[AuthenticatableUser]:
        """Get the currently authenticated user."""
        if self._user is not None:
            return self._user
            
        # Get token from request
        token = self._get_token_from_request()
        if not token:
            return None
            
        # Decode and validate token
        try:
            payload = self._decode_token(token)
            user_id = payload.get('sub')  # Subject claim
            
            if user_id:
                self._user = self.provider.retrieve_by_id(user_id)
                self._token = token
                
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
            pass
            
        return self._user
        
    async def validate(self, credentials: Dict[str, Any]) -> bool:
        """Validate user credentials without logging in."""
        return await self.provider.validate_credentials(credentials)
        
    def token(self) -> Optional[str]:
        """Get the current JWT token."""
        if self._token:
            return self._token
            
        # Try to get from request
        return self._get_token_from_request()
        
    async def generate_token(self, user: AuthenticatableUser, custom_claims: Optional[Dict[str, Any]] = None) -> str:
        """Generate a JWT token for a user."""
        now = datetime.utcnow()
        payload = {
            'sub': str(user.get_auth_identifier()),  # Subject
            'iat': now,  # Issued at
            'exp': now + timedelta(seconds=self.ttl),  # Expires
            'iss': 'larapy',  # Issuer
        }
        
        # Add custom claims
        if custom_claims:
            payload.update(custom_claims)
            
        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        return token
        
    async def refresh_token(self, token: str) -> Optional[str]:
        """Refresh a JWT token."""
        try:
            # Decode without verifying expiration
            payload = jwt.decode(
                token, 
                self.secret, 
                algorithms=[self.algorithm],
                options={'verify_exp': False}
            )
            
            # Check if token is within refresh window
            iat = payload.get('iat')
            if iat:
                token_age = (datetime.utcnow() - datetime.fromtimestamp(iat)).total_seconds()
                if token_age > self.refresh_ttl:
                    return None  # Token too old to refresh
                    
            # Get user
            user_id = payload.get('sub')
            if not user_id:
                return None
                
            user = self.provider.retrieve_by_id(user_id)
            if not user:
                return None
                
            # Generate new token
            return await self.generate_token(user)
            
        except jwt.InvalidTokenError:
            return None
            
    def _get_token_from_request(self) -> Optional[str]:
        """Extract JWT token from the request."""
        if not self._current_request:
            return None
            
        # Try to get token from Authorization header
        auth_header = getattr(self._current_request, 'headers', {}).get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
            
        # Try to get from cookies
        cookies = getattr(self._current_request, 'cookies', {})
        token = cookies.get('jwt_token')
        if token:
            return token
            
        return None
        
    def _decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a JWT token."""
        return jwt.decode(token, self.secret, algorithms=[self.algorithm])
        
    async def blacklist_token(self, token: str) -> bool:
        """Blacklist a JWT token (prevent further use)."""
        # In a real implementation, you would store blacklisted tokens
        # in a cache or database until they expire
        # For now, this is a placeholder
        return True
        
    def get_token_payload(self, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the payload of the current or specified token."""
        if not token:
            token = self.token()
            
        if not token:
            return None
            
        try:
            return self._decode_token(token)
        except jwt.InvalidTokenError:
            return None