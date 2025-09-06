"""
Configuration management with dot notation access.

This module provides Laravel-like configuration management with
dot notation access, environment integration, and caching.
"""

import os
from typing import Any, Dict, Optional, Union
from pathlib import Path


class Config:
    """
    Configuration manager with dot notation access.
    
    Provides Laravel-like configuration access using dot notation
    with environment variable integration and default value support.
    """
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_data: Initial configuration data
        """
        self._config: Dict[str, Any] = config_data or {}
        self._cached_values: Dict[str, Any] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: The configuration key (supports dot notation)
            default: Default value if key is not found
            
        Returns:
            The configuration value or default
        """
        # Check cache first
        if key in self._cached_values:
            return self._cached_values[key]
        
        # Navigate through the configuration using dot notation
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    # Key not found, return default
                    return default
            
            # Cache the value
            self._cached_values[key] = value
            return value
            
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: The configuration key (supports dot notation)
            value: The value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent dictionary, creating intermediate dicts as needed
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                # Overwrite non-dict values with dict
                config[k] = {}
            config = config[k]
        
        # Set the final value
        config[keys[-1]] = value
        
        # Clear cache for this key
        if key in self._cached_values:
            del self._cached_values[key]
    
    def has(self, key: str) -> bool:
        """
        Check if a configuration key exists.
        
        Args:
            key: The configuration key
            
        Returns:
            True if key exists, False otherwise
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return False
            return True
        except (KeyError, TypeError):
            return False
    
    def all(self) -> Dict[str, Any]:
        """
        Get all configuration data.
        
        Returns:
            All configuration data as a dictionary
        """
        return self._config.copy()
    
    def forget(self, key: str) -> None:
        """
        Remove a configuration key.
        
        Args:
            key: The configuration key to remove
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to parent
        try:
            for k in keys[:-1]:
                config = config[k]
            
            # Remove the key
            if keys[-1] in config:
                del config[keys[-1]]
                
                # Clear from cache
                if key in self._cached_values:
                    del self._cached_values[key]
                    
        except (KeyError, TypeError):
            # Key doesn't exist, ignore
            pass
    
    def merge(self, config_data: Dict[str, Any]) -> None:
        """
        Merge configuration data.
        
        Args:
            config_data: Configuration data to merge
        """
        self._merge_recursive(self._config, config_data)
        # Clear cache after merge
        self._cached_values.clear()
    
    def _merge_recursive(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively merge configuration dictionaries.
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if (key in target and 
                isinstance(target[key], dict) and 
                isinstance(value, dict)):
                self._merge_recursive(target[key], value)
            else:
                target[key] = value
    
    def load_from_dict(self, config_data: Dict[str, Any]) -> None:
        """
        Load configuration from a dictionary.
        
        Args:
            config_data: Configuration data dictionary
        """
        self._config = config_data
        self._cached_values.clear()
    
    def load_from_file(self, file_path: Union[str, Path]) -> None:
        """
        Load configuration from a Python file.
        
        Args:
            file_path: Path to the configuration file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Import the config module
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            file_path.stem, file_path
        )
        
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Extract configuration variables (excluding private/magic methods)
            config_vars = {
                key: value for key, value in vars(module).items()
                if not key.startswith('_')
            }
            
            self.merge(config_vars)
    
    def load_from_directory(self, directory_path: Union[str, Path]) -> None:
        """
        Load configuration from all Python files in a directory.
        
        Args:
            directory_path: Path to the configuration directory
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            return
        
        for config_file in directory_path.glob('*.py'):
            if config_file.name.startswith('__'):
                continue
            
            # Load config and merge under the filename (without .py)
            file_config = Config()
            file_config.load_from_file(config_file)
            
            # Merge under the filename as a namespace
            self.set(config_file.stem, file_config.all())
    
    def env(self, key: str, default: Any = None, cast_type: Optional[type] = None) -> Any:
        """
        Get an environment variable with optional type casting.
        
        Args:
            key: The environment variable name
            default: Default value if not found
            cast_type: Type to cast the value to
            
        Returns:
            The environment variable value or default
        """
        value = os.getenv(key, default)
        
        if value is None or value == default:
            return default
        
        # Type casting
        if cast_type:
            try:
                if cast_type == bool:
                    # Handle boolean string conversion
                    return str(value).lower() in ('true', '1', 'yes', 'on')
                elif cast_type == int:
                    return int(value)
                elif cast_type == float:
                    return float(value)
                elif cast_type == str:
                    return str(value)
                else:
                    return cast_type(value)
            except (ValueError, TypeError):
                return default
        
        return value
    
    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cached_values.clear()
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dictionary-style setting."""
        self.set(key, value)
    
    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator."""
        return self.has(key)
    
    def __delitem__(self, key: str) -> None:
        """Allow del statement."""
        self.forget(key)