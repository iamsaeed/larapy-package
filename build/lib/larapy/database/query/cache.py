"""
Query caching system for Larapy.

This module provides query result caching capabilities to improve
database performance by caching frequently executed queries.
"""

import hashlib
import json
import pickle
import time
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
from datetime import datetime, timedelta


class QueryCache(ABC):
    """Abstract base class for query caching implementations."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        pass
        
    @abstractmethod
    async def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value in cache with optional TTL in seconds."""
        pass
        
    @abstractmethod
    async def forget(self, key: str) -> bool:
        """Remove value from cache."""
        pass
        
    @abstractmethod
    async def flush(self) -> bool:
        """Clear all cached values."""
        pass
        
    @abstractmethod
    async def has(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class MemoryQueryCache(QueryCache):
    """In-memory query cache implementation."""
    
    def __init__(self, default_ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        if key in self.cache:
            entry = self.cache[key]
            if self._is_expired(entry):
                del self.cache[key]
                return None
            return entry['value']
        return None
        
    async def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value in cache with optional TTL."""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None
        
        self.cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': time.time()
        }
        
    async def forget(self, key: str) -> bool:
        """Remove value from cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
        
    async def flush(self) -> bool:
        """Clear all cached values."""
        self.cache.clear()
        return True
        
    async def has(self, key: str) -> bool:
        """Check if key exists in cache."""
        if key in self.cache:
            entry = self.cache[key]
            if self._is_expired(entry):
                del self.cache[key]
                return False
            return True
        return False
        
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        if entry['expires_at'] is None:
            return False
        return time.time() > entry['expires_at']


class FileQueryCache(QueryCache):
    """File-based query cache implementation."""
    
    def __init__(self, cache_dir: str = 'cache/queries', default_ttl: int = 3600):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        
        # Ensure cache directory exists
        import os
        os.makedirs(cache_dir, exist_ok=True)
        
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        file_path = self._get_file_path(key)
        
        try:
            import os
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
                
            if self._is_expired(data):
                os.unlink(file_path)
                return None
                
            return data['value']
        except (FileNotFoundError, pickle.PickleError, KeyError):
            return None
            
    async def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value in cache with optional TTL."""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None
        
        file_path = self._get_file_path(key)
        data = {
            'value': value,
            'expires_at': expires_at,
            'created_at': time.time()
        }
        
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
        except (pickle.PickleError, IOError):
            pass  # Silently fail caching
            
    async def forget(self, key: str) -> bool:
        """Remove value from cache."""
        file_path = self._get_file_path(key)
        try:
            import os
            if os.path.exists(file_path):
                os.unlink(file_path)
                return True
        except OSError:
            pass
        return False
        
    async def flush(self) -> bool:
        """Clear all cached values."""
        try:
            import os
            import shutil
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
            return True
        except OSError:
            return False
            
    async def has(self, key: str) -> bool:
        """Check if key exists in cache."""
        file_path = self._get_file_path(key)
        
        try:
            import os
            if not os.path.exists(file_path):
                return False
                
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
                
            if self._is_expired(data):
                os.unlink(file_path)
                return False
                
            return True
        except (FileNotFoundError, pickle.PickleError, KeyError):
            return False
            
    def _get_file_path(self, key: str) -> str:
        """Get file path for cache key."""
        import os
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.cache")
        
    def _is_expired(self, data: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        if data['expires_at'] is None:
            return False
        return time.time() > data['expires_at']


class CacheableQueryBuilder:
    """Mixin to add caching capabilities to QueryBuilder."""
    
    def __init__(self):
        self._cache_enabled = False
        self._cache_ttl = None
        self._cache_tags = []
        self._cache_key = None
        
    def cache(self, ttl: Optional[int] = None, tags: Optional[List[str]] = None) -> 'CacheableQueryBuilder':
        """Enable caching for this query."""
        self._cache_enabled = True
        self._cache_ttl = ttl
        self._cache_tags = tags or []
        return self
        
    def cache_key(self, key: str) -> 'CacheableQueryBuilder':
        """Set a custom cache key."""
        self._cache_key = key
        return self
        
    def remember(self, ttl: int, key: Optional[str] = None) -> 'CacheableQueryBuilder':
        """Remember query results for specified TTL."""
        self._cache_enabled = True
        self._cache_ttl = ttl
        if key:
            self._cache_key = key
        return self
        
    def remember_forever(self, key: Optional[str] = None) -> 'CacheableQueryBuilder':
        """Remember query results forever."""
        self._cache_enabled = True
        self._cache_ttl = 0  # 0 means no expiration
        if key:
            self._cache_key = key
        return self
        
    def dont_cache(self) -> 'CacheableQueryBuilder':
        """Disable caching for this query."""
        self._cache_enabled = False
        return self
        
    def _generate_cache_key(self) -> str:
        """Generate cache key from query parameters."""
        if self._cache_key:
            return self._cache_key
            
        # Create key from query components
        key_components = {
            'table': self.table_name,
            'select': self._select_columns,
            'where': self._where_clauses,
            'joins': self._joins,
            'group_by': self._group_by,
            'having': self._having,
            'order_by': self._order_by,
            'limit': self._limit_count,
            'offset': self._offset_count
        }
        
        # Serialize and hash
        key_string = json.dumps(key_components, sort_keys=True)
        return f"query:{hashlib.md5(key_string.encode()).hexdigest()}"
        
    async def _get_cached_result(self, cache: QueryCache, cache_key: str) -> Optional[Any]:
        """Get result from cache."""
        if not self._cache_enabled:
            return None
        return await cache.get(cache_key)
        
    async def _cache_result(self, cache: QueryCache, cache_key: str, result: Any) -> None:
        """Store result in cache."""
        if not self._cache_enabled:
            return
        await cache.put(cache_key, result, self._cache_ttl)


class QueryCacheManager:
    """Manages query caching operations."""
    
    def __init__(self, cache: QueryCache):
        self.cache = cache
        self._tag_mappings: Dict[str, List[str]] = {}
        
    async def get(self, key: str) -> Optional[Any]:
        """Get cached query result."""
        return await self.cache.get(key)
        
    async def put(self, key: str, result: Any, ttl: Optional[int] = None, 
                 tags: Optional[List[str]] = None) -> None:
        """Cache query result."""
        await self.cache.put(key, result, ttl)
        
        # Store tag mappings
        if tags:
            for tag in tags:
                if tag not in self._tag_mappings:
                    self._tag_mappings[tag] = []
                if key not in self._tag_mappings[tag]:
                    self._tag_mappings[tag].append(key)
                    
    async def forget(self, key: str) -> bool:
        """Remove cached query result."""
        return await self.cache.forget(key)
        
    async def flush_tag(self, tag: str) -> int:
        """Remove all cached results with the specified tag."""
        if tag not in self._tag_mappings:
            return 0
            
        keys = self._tag_mappings[tag]
        count = 0
        
        for key in keys:
            if await self.cache.forget(key):
                count += 1
                
        # Clean up tag mapping
        del self._tag_mappings[tag]
        return count
        
    async def flush_tags(self, tags: List[str]) -> int:
        """Remove all cached results with the specified tags."""
        total_count = 0
        for tag in tags:
            total_count += await self.flush_tag(tag)
        return total_count
        
    async def flush(self) -> bool:
        """Clear all cached query results."""
        self._tag_mappings.clear()
        return await self.cache.flush()
        
    async def has(self, key: str) -> bool:
        """Check if query result is cached."""
        return await self.cache.has(key)


# Enhanced QueryBuilder with caching (this would be integrated into the main QueryBuilder)
class CachedQueryBuilderMethods:
    """Methods to add to QueryBuilder for caching support."""
    
    def __init__(self):
        self._cache_manager: Optional[QueryCacheManager] = None
        
    def set_cache_manager(self, cache_manager: QueryCacheManager) -> None:
        """Set the cache manager for this query builder."""
        self._cache_manager = cache_manager
        
    async def get_with_cache(self) -> List[Dict[str, Any]]:
        """Execute query with caching support."""
        if not self._cache_enabled or not self._cache_manager:
            return await self.get()
            
        cache_key = self._generate_cache_key()
        
        # Try to get from cache
        cached_result = await self._cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result
            
        # Execute query
        result = await self.get()
        
        # Cache result
        await self._cache_manager.put(
            cache_key, 
            result, 
            self._cache_ttl,
            self._cache_tags
        )
        
        return result
        
    async def first_with_cache(self) -> Optional[Dict[str, Any]]:
        """Execute first() query with caching support."""
        if not self._cache_enabled or not self._cache_manager:
            return await self.first()
            
        cache_key = self._generate_cache_key() + ':first'
        
        # Try to get from cache
        cached_result = await self._cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result
            
        # Execute query
        result = await self.first()
        
        # Cache result
        await self._cache_manager.put(
            cache_key,
            result,
            self._cache_ttl,
            self._cache_tags
        )
        
        return result


# Example usage and configuration
"""
# Configure caching
memory_cache = MemoryQueryCache(default_ttl=3600)
cache_manager = QueryCacheManager(memory_cache)

# Set cache manager on query builder
query_builder.set_cache_manager(cache_manager)

# Use caching in queries
users = await User.query().cache(ttl=1800).get()
user = await User.query().where('id', 1).remember(3600).first()
posts = await Post.query().cache(ttl=900, tags=['posts']).get()

# Invalidate cache by tags
await cache_manager.flush_tag('posts')
await cache_manager.flush_tags(['users', 'posts'])
"""