"""
Laravel-like helper functions for Larapy.

This module provides helper functions that mimic Laravel's global helpers,
including env(), config(), and other utility functions.
"""

import os
import inspect
import json
from pathlib import Path
from typing import Any, Optional, Dict, Union
from functools import lru_cache


# Global configuration storage
_config_cache: Optional[Dict[str, Any]] = None
_config_cached: bool = False
_app_root: Optional[Path] = None


def env(key: str, default: Any = None) -> Any:
    """
    Get an environment variable value.
    
    This function mimics Laravel's env() helper. It should only be called
    from within configuration files. Once configuration is cached, this
    function will only return system environment variables.
    
    Args:
        key: The environment variable name
        default: Default value if the variable doesn't exist
        
    Returns:
        The environment variable value or default
    """
    # Check if configuration is cached
    if _config_cached:
        # When cached, only return system environment variables
        # This mimics Laravel's behavior after config:cache
        return os.environ.get(key, default)
    
    # Get the value from environment
    value = os.getenv(key, default)
    
    # Handle special string values like Laravel does
    if isinstance(value, str):
        value_lower = value.lower()
        
        # Convert string booleans
        if value_lower == 'true':
            return True
        elif value_lower == 'false':
            return False
        elif value_lower == 'null' or value_lower == '(null)':
            return None
        elif value_lower == 'empty' or value_lower == '(empty)':
            return ''
        
        # Handle quoted strings
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
    
    return value


def config(key: Optional[str] = None, default: Any = None) -> Any:
    """
    Get or set configuration values.
    
    This function mimics Laravel's config() helper. It uses dot notation
    to access nested configuration values.
    
    Args:
        key: Configuration key using dot notation (e.g., 'database.default')
             If None, returns all configuration
             If dict, sets multiple configuration values
        default: Default value if the key doesn't exist
        
    Returns:
        Configuration value, all configuration, or None
    """
    global _config_cache
    
    # Load configuration if not already loaded
    if _config_cache is None:
        _load_configuration()
    
    # If key is a dict, set configuration values
    if isinstance(key, dict):
        for k, v in key.items():
            _set_config_value(k, v)
        return None
    
    # If no key provided, return all configuration
    if key is None:
        return _config_cache
    
    # Get configuration value using dot notation
    return _get_config_value(key, default)


def _get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value using dot notation.
    
    Args:
        key: Configuration key (e.g., 'database.connections.mysql.host')
        default: Default value if key doesn't exist
        
    Returns:
        Configuration value or default
    """
    if _config_cache is None:
        return default
    
    keys = key.split('.')
    value = _config_cache
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def _set_config_value(key: str, value: Any) -> None:
    """
    Set a configuration value using dot notation.
    
    Args:
        key: Configuration key (e.g., 'database.connections.mysql.host')
        value: Value to set
    """
    global _config_cache
    
    if _config_cache is None:
        _config_cache = {}
    
    keys = key.split('.')
    config = _config_cache
    
    # Navigate to the parent dictionary
    for k in keys[:-1]:
        if k not in config:
            config[k] = {}
        config = config[k]
    
    # Set the final value
    config[keys[-1]] = value


def _load_configuration() -> None:
    """
    Load all configuration files from the config directory.
    
    This mimics Laravel's configuration loading process.
    """
    global _config_cache, _app_root
    
    _config_cache = {}
    
    # Find application root
    if _app_root is None:
        _app_root = _find_app_root()
        
    if not _app_root:
        return
    
    config_dir = _app_root / 'config'
    if not config_dir.exists():
        return
    
    # Load .env file first
    _load_env_file(_app_root / '.env')
    
    # Load all Python configuration files
    for config_file in sorted(config_dir.glob('*.py')):
        if config_file.name.startswith('__'):
            continue
        
        config_name = config_file.stem
        config_data = _load_config_file(config_file)
        
        if config_data is not None:
            _config_cache[config_name] = config_data


def _load_env_file(env_path: Path) -> None:
    """
    Load environment variables from .env file.
    
    Args:
        env_path: Path to .env file
    """
    if not env_path.exists():
        return
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value
    except Exception:
        pass


def _load_config_file(config_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a configuration file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary or None
    """
    try:
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            f"config_{config_path.stem}", 
            config_path
        )
        
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # If module has a CONFIG variable, use that
            if hasattr(module, 'CONFIG'):
                return module.CONFIG
            
            # Otherwise, collect all uppercase variables (Laravel style)
            config = {}
            for name in dir(module):
                if name.isupper() and not name.startswith('_'):
                    config[name.lower()] = getattr(module, name)
            
            return config if config else None
            
    except Exception as e:
        print(f"Warning: Could not load config file {config_path}: {e}")
        return None


def _find_app_root() -> Optional[Path]:
    """
    Find the application root directory.
    
    Returns:
        Path to application root or None
    """
    # Try multiple strategies to find app root
    
    # Strategy 1: Look for config directory
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / 'config').is_dir():
            return parent
    
    # Strategy 2: Look for .env file
    for parent in [current] + list(current.parents):
        if (parent / '.env').is_file():
            return parent
    
    # Strategy 3: Look for common Laravel/Larapy directories
    for parent in [current] + list(current.parents):
        if (parent / 'database' / 'migrations').is_dir():
            return parent
    
    return None


def cache_config(config_path: Optional[Path] = None) -> None:
    """
    Cache the configuration for better performance.
    
    This mimics Laravel's config:cache command.
    
    Args:
        config_path: Path to save cached configuration
    """
    global _config_cached, _config_cache
    
    # Load configuration if not loaded
    if _config_cache is None:
        _load_configuration()
    
    # Determine cache path
    if config_path is None:
        if _app_root:
            config_path = _app_root / 'bootstrap' / 'cache' / 'config.json'
        else:
            return
    
    # Ensure cache directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save configuration to cache file
    try:
        with open(config_path, 'w') as f:
            json.dump(_config_cache, f, indent=2, default=str)
        
        _config_cached = True
        print(f"Configuration cached successfully at {config_path}")
    except Exception as e:
        print(f"Failed to cache configuration: {e}")


def clear_config_cache(cache_path: Optional[Path] = None) -> None:
    """
    Clear the cached configuration.
    
    This mimics Laravel's config:clear command.
    
    Args:
        cache_path: Path to cached configuration file
    """
    global _config_cached, _config_cache
    
    # Determine cache path
    if cache_path is None:
        if _app_root:
            cache_path = _app_root / 'bootstrap' / 'cache' / 'config.json'
        else:
            return
    
    # Remove cache file
    if cache_path.exists():
        cache_path.unlink()
        print(f"Configuration cache cleared")
    
    # Reset cache flags
    _config_cached = False
    _config_cache = None


def load_cached_config(cache_path: Optional[Path] = None) -> bool:
    """
    Load configuration from cache if it exists.
    
    Args:
        cache_path: Path to cached configuration file
        
    Returns:
        True if cache was loaded, False otherwise
    """
    global _config_cached, _config_cache
    
    # Determine cache path
    if cache_path is None:
        if not _app_root:
            _app_root = _find_app_root()
        
        if _app_root:
            cache_path = _app_root / 'bootstrap' / 'cache' / 'config.json'
        else:
            return False
    
    # Load cache if it exists
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                _config_cache = json.load(f)
            
            _config_cached = True
            return True
        except Exception:
            pass
    
    return False


def app_path(path: str = '') -> str:
    """
    Get the path to the application directory.
    
    Args:
        path: Additional path to append
        
    Returns:
        Full path as string
    """
    global _app_root
    if _app_root is None:
        _app_root = _find_app_root()
    
    if _app_root:
        return str(_app_root / 'app' / path) if path else str(_app_root / 'app')
    
    return path


def base_path(path: str = '') -> str:
    """
    Get the path to the application root directory.
    
    Args:
        path: Additional path to append
        
    Returns:
        Full path as string
    """
    global _app_root
    if _app_root is None:
        _app_root = _find_app_root()
    
    if _app_root:
        return str(_app_root / path) if path else str(_app_root)
    
    return path


def config_path(path: str = '') -> str:
    """
    Get the path to the configuration directory.
    
    Args:
        path: Additional path to append
        
    Returns:
        Full path as string
    """
    global _app_root
    if _app_root is None:
        _app_root = _find_app_root()
    
    if _app_root:
        return str(_app_root / 'config' / path) if path else str(_app_root / 'config')
    
    return path


def database_path(path: str = '') -> str:
    """
    Get the path to the database directory.
    
    Args:
        path: Additional path to append
        
    Returns:
        Full path as string
    """
    global _app_root
    if _app_root is None:
        _app_root = _find_app_root()
    
    if _app_root:
        return str(_app_root / 'database' / path) if path else str(_app_root / 'database')
    
    return path


def storage_path(path: str = '') -> str:
    """
    Get the path to the storage directory.
    
    Args:
        path: Additional path to append
        
    Returns:
        Full path as string
    """
    global _app_root
    if _app_root is None:
        _app_root = _find_app_root()
    
    if _app_root:
        return str(_app_root / 'storage' / path) if path else str(_app_root / 'storage')
    
    return path


def public_path(path: str = '') -> str:
    """
    Get the path to the public directory.
    
    Args:
        path: Additional path to append
        
    Returns:
        Full path as string
    """
    global _app_root
    if _app_root is None:
        _app_root = _find_app_root()
    
    if _app_root:
        return str(_app_root / 'public' / path) if path else str(_app_root / 'public')
    
    return path


def resource_path(path: str = '') -> str:
    """
    Get the path to the resources directory.
    
    Args:
        path: Additional path to append
        
    Returns:
        Full path as string
    """
    global _app_root
    if _app_root is None:
        _app_root = _find_app_root()
    
    if _app_root:
        return str(_app_root / 'resources' / path) if path else str(_app_root / 'resources')
    
    return path