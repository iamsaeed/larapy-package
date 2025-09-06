"""
Cache manager for Larapy.

Provides a simple cache management system.
"""

from typing import Any, Optional
import time


class CacheManager:
    """Simple cache manager."""
    
    def __init__(self):
        """Initialize cache manager."""
        self._cache = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        if key in self._cache:
            value, expires_at = self._cache[key]
            if expires_at is None or time.time() < expires_at:
                return value
            else:
                del self._cache[key]
        return default
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None):
        """Put value in cache."""
        expires_at = None
        if ttl:
            expires_at = time.time() + ttl
        self._cache[key] = (value, expires_at)
    
    def forget(self, key: str):
        """Remove key from cache."""
        if key in self._cache:
            del self._cache[key]
    
    def flush(self):
        """Clear all cache."""
        self._cache.clear()
    
    def remember(self, key: str, ttl: int, callback):
        """Remember value using callback."""
        value = self.get(key)
        if value is None:
            value = callback()
            self.put(key, value, ttl)
        return value