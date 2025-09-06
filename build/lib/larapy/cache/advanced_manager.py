"""
Advanced Cache Manager

Comprehensive cache management system with multiple drivers and advanced features.
"""

import time
import hashlib
import threading
from typing import Any, Optional, Dict, List, Callable, Union, Set
from .drivers import CacheDriver, MemoryDriver, FileDriver, RedisDriver, DatabaseDriver, NullDriver


class CacheStore:
    """
    Individual cache store with tagging and statistics.
    """
    
    def __init__(self, driver: CacheDriver, prefix: str = ''):
        """
        Initialize cache store.
        
        Args:
            driver: Cache driver instance
            prefix: Key prefix for this store
        """
        self.driver = driver
        self.prefix = prefix
        self._tags: Dict[str, Set[str]] = {}
        self._stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'deletes': 0
        }
        self._lock = threading.Lock()
    
    def _make_key(self, key: str) -> str:
        """Make prefixed cache key."""
        return f"{self.prefix}{key}" if self.prefix else key
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        prefixed_key = self._make_key(key)
        value = self.driver.get(prefixed_key)
        
        with self._lock:
            if value is not None:
                self._stats['hits'] += 1
            else:
                self._stats['misses'] += 1
        
        return value
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None, tags: List[str] = None) -> bool:
        """Put value in cache with optional tags."""
        prefixed_key = self._make_key(key)
        result = self.driver.put(prefixed_key, value, ttl)
        
        if result and tags:
            self._add_tags(prefixed_key, tags)
        
        with self._lock:
            self._stats['writes'] += 1
        
        return result
    
    def forget(self, key: str) -> bool:
        """Remove value from cache."""
        prefixed_key = self._make_key(key)
        result = self.driver.forget(prefixed_key)
        
        self._remove_from_tags(prefixed_key)
        
        with self._lock:
            self._stats['deletes'] += 1
        
        return result
    
    def has(self, key: str) -> bool:
        """Check if key exists in cache."""
        prefixed_key = self._make_key(key)
        return self.driver.has(prefixed_key)
    
    def remember(self, key: str, callback: Callable, ttl: Optional[int] = None, tags: List[str] = None) -> Any:
        """Remember value from callback if not in cache."""
        value = self.get(key)
        if value is not None:
            return value
        
        value = callback()
        self.put(key, value, ttl, tags)
        return value
    
    def forget_by_tags(self, tags: List[str]) -> int:
        """Forget all cached items with specified tags."""
        keys_to_forget = set()
        
        for tag in tags:
            if tag in self._tags:
                keys_to_forget.update(self._tags[tag])
        
        count = 0
        for key in keys_to_forget:
            if self.driver.forget(key):
                count += 1
        
        # Clean up tag tracking
        for tag in tags:
            if tag in self._tags:
                del self._tags[tag]
        
        return count
    
    def _add_tags(self, key: str, tags: List[str]):
        """Add tags for a cache key."""
        for tag in tags:
            if tag not in self._tags:
                self._tags[tag] = set()
            self._tags[tag].add(key)
    
    def _remove_from_tags(self, key: str):
        """Remove key from all tag tracking."""
        for tag_keys in self._tags.values():
            tag_keys.discard(key)
    
    def flush(self) -> bool:
        """Clear all cache entries."""
        result = self.driver.flush()
        self._tags.clear()
        return result
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                **self._stats,
                'total_requests': total_requests,
                'hit_rate': round(hit_rate, 2)
            }
    
    def increment(self, key: str, value: int = 1) -> int:
        """Increment numeric value."""
        return self.driver.increment(self._make_key(key), value)
    
    def decrement(self, key: str, value: int = 1) -> int:
        """Decrement numeric value."""
        return self.driver.decrement(self._make_key(key), value)


class AdvancedCacheManager:
    """
    Advanced cache manager with multiple stores and drivers.
    """
    
    def __init__(self, default_store: str = 'memory'):
        """
        Initialize cache manager.
        
        Args:
            default_store: Name of default cache store
        """
        self._stores: Dict[str, CacheStore] = {}
        self._default_store = default_store
        self._lock = threading.Lock()
        
        # Initialize default stores
        self._initialize_default_stores()
    
    def _initialize_default_stores(self):
        """Initialize default cache stores."""
        # Memory store
        self.add_store('memory', MemoryDriver())
        
        # File store
        self.add_store('file', FileDriver())
        
        # Database store
        self.add_store('database', DatabaseDriver())
        
        # Null store
        self.add_store('null', NullDriver())
    
    def add_store(self, name: str, driver: CacheDriver, prefix: str = '') -> 'AdvancedCacheManager':
        """
        Add cache store.
        
        Args:
            name: Store name
            driver: Cache driver instance
            prefix: Key prefix for this store
            
        Returns:
            Self for method chaining
        """
        with self._lock:
            self._stores[name] = CacheStore(driver, prefix)
        return self
    
    def store(self, name: Optional[str] = None) -> CacheStore:
        """
        Get cache store by name.
        
        Args:
            name: Store name (uses default if None)
            
        Returns:
            Cache store instance
        """
        store_name = name or self._default_store
        
        if store_name not in self._stores:
            raise ValueError(f"Cache store '{store_name}' not found")
        
        return self._stores[store_name]
    
    def get(self, key: str, default: Any = None, store: Optional[str] = None) -> Any:
        """Get value from cache."""
        value = self.store(store).get(key)
        return value if value is not None else default
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None, 
            tags: List[str] = None, store: Optional[str] = None) -> bool:
        """Put value in cache."""
        return self.store(store).put(key, value, ttl, tags)
    
    def forget(self, key: str, store: Optional[str] = None) -> bool:
        """Remove value from cache."""
        return self.store(store).forget(key)
    
    def has(self, key: str, store: Optional[str] = None) -> bool:
        """Check if key exists in cache."""
        return self.store(store).has(key)
    
    def remember(self, key: str, callback: Callable, ttl: Optional[int] = None, 
                tags: List[str] = None, store: Optional[str] = None) -> Any:
        """Remember value from callback if not in cache."""
        return self.store(store).remember(key, callback, ttl, tags)
    
    def forget_by_tags(self, tags: List[str], store: Optional[str] = None) -> int:
        """Forget all cached items with specified tags."""
        return self.store(store).forget_by_tags(tags)
    
    def flush(self, store: Optional[str] = None) -> bool:
        """Clear cache entries."""
        if store:
            return self.store(store).flush()
        else:
            # Flush all stores
            results = []
            for store_instance in self._stores.values():
                results.append(store_instance.flush())
            return all(results)
    
    def increment(self, key: str, value: int = 1, store: Optional[str] = None) -> int:
        """Increment numeric value."""
        return self.store(store).increment(key, value)
    
    def decrement(self, key: str, value: int = 1, store: Optional[str] = None) -> int:
        """Decrement numeric value."""
        return self.store(store).decrement(key, value)
    
    def get_stats(self, store: Optional[str] = None) -> Union[Dict[str, int], Dict[str, Dict[str, int]]]:
        """Get cache statistics."""
        if store:
            return self.store(store).get_stats()
        else:
            # Get stats for all stores
            return {name: store_instance.get_stats() for name, store_instance in self._stores.items()}
    
    def cleanup_expired(self) -> Dict[str, int]:
        """Clean up expired entries in all applicable stores."""
        results = {}
        
        for name, store in self._stores.items():
            if hasattr(store.driver, 'cleanup_expired'):
                results[name] = store.driver.cleanup_expired()
        
        return results
    
    # Context manager support
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass


class RateLimiter:
    """
    Rate limiter using cache for storage.
    """
    
    def __init__(self, cache_manager: AdvancedCacheManager, store: str = 'memory'):
        """
        Initialize rate limiter.
        
        Args:
            cache_manager: Cache manager instance
            store: Cache store to use
        """
        self.cache = cache_manager
        self.store = store
    
    def attempt(self, key: str, max_attempts: int, decay_seconds: int) -> bool:
        """
        Check if attempt is allowed within rate limit.
        
        Args:
            key: Rate limit key
            max_attempts: Maximum attempts allowed
            decay_seconds: Time window in seconds
            
        Returns:
            True if attempt is allowed, False otherwise
        """
        current_time = int(time.time())
        cache_key = f"rate_limit:{key}:{current_time // decay_seconds}"
        
        current_attempts = self.cache.get(cache_key, 0, self.store)
        
        if current_attempts >= max_attempts:
            return False
        
        # Increment attempts
        self.cache.put(cache_key, current_attempts + 1, decay_seconds, store=self.store)
        return True
    
    def remaining(self, key: str, max_attempts: int, decay_seconds: int) -> int:
        """Get remaining attempts."""
        current_time = int(time.time())
        cache_key = f"rate_limit:{key}:{current_time // decay_seconds}"
        
        current_attempts = self.cache.get(cache_key, 0, self.store)
        return max(0, max_attempts - current_attempts)
    
    def reset(self, key: str, decay_seconds: int) -> bool:
        """Reset rate limit for key."""
        current_time = int(time.time())
        cache_key = f"rate_limit:{key}:{current_time // decay_seconds}"
        return self.cache.forget(cache_key, self.store)


# Global advanced cache manager instance
advanced_cache_manager = AdvancedCacheManager()

# Helper functions for global access
def cache_get_advanced(key: str, default: Any = None) -> Any:
    """Get value from advanced cache store."""
    return advanced_cache_manager.get(key, default)

def cache_put_advanced(key: str, value: Any, ttl: Optional[int] = None, tags: List[str] = None) -> bool:
    """Put value in advanced cache store."""
    return advanced_cache_manager.put(key, value, ttl, tags)

def cache_forget_advanced(key: str) -> bool:
    """Remove value from advanced cache store."""
    return advanced_cache_manager.forget(key)

def cache_remember_advanced(key: str, callback: Callable, ttl: Optional[int] = None, tags: List[str] = None) -> Any:
    """Remember value from callback if not in cache."""
    return advanced_cache_manager.remember(key, callback, ttl, tags)

def cache_flush_advanced() -> bool:
    """Clear all advanced cache entries."""
    return advanced_cache_manager.flush()

def cache_stats() -> Dict[str, Dict[str, int]]:
    """Get cache statistics for all stores."""
    return advanced_cache_manager.get_stats()

def cache_tag_flush(tags: List[str]) -> int:
    """Flush cache entries by tags."""
    return advanced_cache_manager.forget_by_tags(tags)