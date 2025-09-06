"""
Cache Drivers

Implements various caching backends for the cache manager.
"""

import json
import time
import os
import pickle
import hashlib
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, Union
from threading import Lock
import threading


class CacheDriver(ABC):
    """
    Abstract base class for cache drivers.
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Put value in cache with optional TTL."""
        pass
    
    @abstractmethod
    def forget(self, key: str) -> bool:
        """Remove value from cache."""
        pass
    
    @abstractmethod
    def flush(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    def remember(self, key: str, callback, ttl: Optional[int] = None) -> Any:
        """Remember value from callback if not in cache."""
        value = self.get(key)
        if value is not None:
            return value
        
        value = callback()
        self.put(key, value, ttl)
        return value
    
    def increment(self, key: str, value: int = 1) -> int:
        """Increment numeric value in cache."""
        current = self.get(key) or 0
        new_value = current + value
        self.put(key, new_value)
        return new_value
    
    def decrement(self, key: str, value: int = 1) -> int:
        """Decrement numeric value in cache."""
        return self.increment(key, -value)


class MemoryDriver(CacheDriver):
    """
    In-memory cache driver using dictionaries.
    """
    
    def __init__(self):
        """Initialize memory cache."""
        self._cache: Dict[str, Dict] = {}
        self._lock = Lock()
    
    def _is_expired(self, entry: Dict) -> bool:
        """Check if cache entry is expired."""
        if 'expires_at' not in entry:
            return False
        return time.time() > entry['expires_at']
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            if self._is_expired(entry):
                del self._cache[key]
                return None
            
            return entry['value']
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Put value in memory cache."""
        with self._lock:
            entry = {
                'value': value,
                'created_at': time.time()
            }
            
            if ttl is not None:
                entry['expires_at'] = time.time() + ttl
            
            self._cache[key] = entry
            return True
    
    def forget(self, key: str) -> bool:
        """Remove value from memory cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def flush(self) -> bool:
        """Clear all memory cache entries."""
        with self._lock:
            self._cache.clear()
            return True
    
    def has(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        return self.get(key) is not None
    
    def size(self) -> int:
        """Get cache size."""
        with self._lock:
            return len(self._cache)


class FileDriver(CacheDriver):
    """
    File-based cache driver.
    """
    
    def __init__(self, cache_path: str = 'storage/framework/cache'):
        """
        Initialize file cache.
        
        Args:
            cache_path: Path to cache directory
        """
        self.cache_path = cache_path
        os.makedirs(cache_path, exist_ok=True)
        self._lock = Lock()
    
    def _get_file_path(self, key: str) -> str:
        """Get file path for cache key."""
        # Hash key to create safe filename
        hashed = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_path, f"{hashed}.cache")
    
    def _is_expired(self, file_path: str) -> bool:
        """Check if cache file is expired."""
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
                if 'expires_at' in data:
                    return time.time() > data['expires_at']
                return False
        except (FileNotFoundError, pickle.PickleError):
            return True
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from file cache."""
        file_path = self._get_file_path(key)
        
        with self._lock:
            try:
                if not os.path.exists(file_path):
                    return None
                
                if self._is_expired(file_path):
                    os.remove(file_path)
                    return None
                
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                    return data['value']
                    
            except (FileNotFoundError, pickle.PickleError, KeyError):
                return None
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Put value in file cache."""
        file_path = self._get_file_path(key)
        
        with self._lock:
            try:
                data = {
                    'value': value,
                    'created_at': time.time()
                }
                
                if ttl is not None:
                    data['expires_at'] = time.time() + ttl
                
                with open(file_path, 'wb') as f:
                    pickle.dump(data, f)
                
                return True
                
            except (pickle.PickleError, IOError):
                return False
    
    def forget(self, key: str) -> bool:
        """Remove value from file cache."""
        file_path = self._get_file_path(key)
        
        with self._lock:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
                return False
            except OSError:
                return False
    
    def flush(self) -> bool:
        """Clear all file cache entries."""
        with self._lock:
            try:
                for filename in os.listdir(self.cache_path):
                    if filename.endswith('.cache'):
                        os.remove(os.path.join(self.cache_path, filename))
                return True
            except OSError:
                return False
    
    def has(self, key: str) -> bool:
        """Check if key exists in file cache."""
        return self.get(key) is not None
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache files."""
        cleaned = 0
        try:
            for filename in os.listdir(self.cache_path):
                if filename.endswith('.cache'):
                    file_path = os.path.join(self.cache_path, filename)
                    if self._is_expired(file_path):
                        os.remove(file_path)
                        cleaned += 1
        except OSError:
            pass
        return cleaned


class RedisDriver(CacheDriver):
    """
    Redis cache driver.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, 
                 password: Optional[str] = None, prefix: str = 'larapy_cache:'):
        """
        Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            prefix: Key prefix
        """
        try:
            import redis
            self.redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False
            )
            self.prefix = prefix
            # Test connection
            self.redis.ping()
        except ImportError:
            raise ImportError("Redis driver requires 'redis' package. Install with: pip install redis")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def _make_key(self, key: str) -> str:
        """Add prefix to cache key."""
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            data = self.redis.get(self._make_key(key))
            if data is None:
                return None
            return pickle.loads(data)
        except Exception:
            return None
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Put value in Redis cache."""
        try:
            data = pickle.dumps(value)
            redis_key = self._make_key(key)
            
            if ttl is not None:
                return self.redis.setex(redis_key, ttl, data)
            else:
                return self.redis.set(redis_key, data)
        except Exception:
            return False
    
    def forget(self, key: str) -> bool:
        """Remove value from Redis cache."""
        try:
            return bool(self.redis.delete(self._make_key(key)))
        except Exception:
            return False
    
    def flush(self) -> bool:
        """Clear all Redis cache entries with prefix."""
        try:
            pattern = f"{self.prefix}*"
            keys = self.redis.keys(pattern)
            if keys:
                return bool(self.redis.delete(*keys))
            return True
        except Exception:
            return False
    
    def has(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        try:
            return bool(self.redis.exists(self._make_key(key)))
        except Exception:
            return False
    
    def increment(self, key: str, value: int = 1) -> int:
        """Increment numeric value in Redis."""
        try:
            return self.redis.incrby(self._make_key(key), value)
        except Exception:
            return super().increment(key, value)
    
    def decrement(self, key: str, value: int = 1) -> int:
        """Decrement numeric value in Redis."""
        try:
            return self.redis.decrby(self._make_key(key), value)
        except Exception:
            return super().decrement(key, value)


class DatabaseDriver(CacheDriver):
    """
    Database cache driver using SQLite.
    """
    
    def __init__(self, database_path: str = 'storage/framework/cache.db'):
        """
        Initialize database cache.
        
        Args:
            database_path: Path to SQLite database
        """
        import sqlite3
        
        self.database_path = database_path
        os.makedirs(os.path.dirname(database_path), exist_ok=True)
        
        # Initialize database
        with sqlite3.connect(database_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    expires_at INTEGER,
                    created_at INTEGER
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries (expires_at)')
        
        self._lock = Lock()
    
    def _get_connection(self):
        """Get database connection."""
        import sqlite3
        return sqlite3.connect(self.database_path)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from database cache."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        'SELECT value, expires_at FROM cache_entries WHERE key = ?',
                        (key,)
                    )
                    row = cursor.fetchone()
                    
                    if row is None:
                        return None
                    
                    value_blob, expires_at = row
                    
                    # Check expiration
                    if expires_at is not None and time.time() > expires_at:
                        conn.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                        conn.commit()
                        return None
                    
                    return pickle.loads(value_blob)
            except Exception:
                return None
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Put value in database cache."""
        with self._lock:
            try:
                value_blob = pickle.dumps(value)
                expires_at = time.time() + ttl if ttl is not None else None
                created_at = int(time.time())
                
                with self._get_connection() as conn:
                    conn.execute('''
                        INSERT OR REPLACE INTO cache_entries 
                        (key, value, expires_at, created_at) VALUES (?, ?, ?, ?)
                    ''', (key, value_blob, expires_at, created_at))
                    conn.commit()
                
                return True
            except Exception:
                return False
    
    def forget(self, key: str) -> bool:
        """Remove value from database cache."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                    conn.commit()
                    return cursor.rowcount > 0
            except Exception:
                return False
    
    def flush(self) -> bool:
        """Clear all database cache entries."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute('DELETE FROM cache_entries')
                    conn.commit()
                return True
            except Exception:
                return False
    
    def has(self, key: str) -> bool:
        """Check if key exists in database cache."""
        return self.get(key) is not None
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        'DELETE FROM cache_entries WHERE expires_at IS NOT NULL AND expires_at < ?',
                        (time.time(),)
                    )
                    conn.commit()
                    return cursor.rowcount
            except Exception:
                return 0


class NullDriver(CacheDriver):
    """
    Null cache driver that doesn't store anything.
    """
    
    def get(self, key: str) -> Optional[Any]:
        """Always returns None."""
        return None
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Always returns True but doesn't store."""
        return True
    
    def forget(self, key: str) -> bool:
        """Always returns True."""
        return True
    
    def flush(self) -> bool:
        """Always returns True."""
        return True
    
    def has(self, key: str) -> bool:
        """Always returns False."""
        return False