"""
Advanced Configuration Features

This module provides advanced configuration capabilities including:
- Configuration publishing system
- Configuration validation
- Configuration merging for packages
- Encrypted configuration values
- Configuration hot-reloading
- Configuration backup and restore
"""

import os
import json
import shutil
import hashlib
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from cryptography.fernet import Fernet
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ConfigurationValidator:
    """Validates configuration values against schemas."""
    
    def __init__(self):
        self.schemas: Dict[str, Dict] = {}
    
    def register_schema(self, key: str, schema: Dict[str, Any]) -> None:
        """
        Register a validation schema for a configuration key.
        
        Args:
            key: Configuration key
            schema: Validation schema
        """
        self.schemas[key] = schema
    
    def validate(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration against registered schemas.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for key, schema in self.schemas.items():
            if key in config:
                value = config[key]
                error = self._validate_value(key, value, schema)
                if error:
                    errors.append(error)
            elif schema.get('required', False):
                errors.append(f"Required configuration key '{key}' is missing")
        
        return errors
    
    def _validate_value(self, key: str, value: Any, schema: Dict[str, Any]) -> Optional[str]:
        """Validate a single value against its schema."""
        # Type validation
        expected_type = schema.get('type')
        if expected_type and not isinstance(value, expected_type):
            return f"Configuration key '{key}' must be of type {expected_type.__name__}"
        
        # Range validation for numbers
        if isinstance(value, (int, float)):
            min_val = schema.get('min')
            max_val = schema.get('max')
            if min_val is not None and value < min_val:
                return f"Configuration key '{key}' must be >= {min_val}"
            if max_val is not None and value > max_val:
                return f"Configuration key '{key}' must be <= {max_val}"
        
        # Choice validation
        choices = schema.get('choices')
        if choices and value not in choices:
            return f"Configuration key '{key}' must be one of {choices}"
        
        # Custom validator
        validator = schema.get('validator')
        if validator and callable(validator):
            try:
                if not validator(value):
                    return f"Configuration key '{key}' failed custom validation"
            except Exception as e:
                return f"Configuration key '{key}' validation error: {str(e)}"
        
        return None


class ConfigurationEncryption:
    """Handles encryption and decryption of sensitive configuration values."""
    
    def __init__(self, key_file: str = None):
        self.key_file = key_file or '.config_key'
        self.cipher_suite = self._get_cipher_suite()
    
    def _get_cipher_suite(self) -> Fernet:
        """Get or create encryption cipher suite."""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Secure the key file
            os.chmod(self.key_file, 0o600)
        
        return Fernet(key)
    
    def encrypt(self, value: str) -> str:
        """Encrypt a configuration value."""
        if isinstance(value, str):
            encrypted = self.cipher_suite.encrypt(value.encode())
            return f"encrypted:{encrypted.decode()}"
        return value
    
    def decrypt(self, value: str) -> str:
        """Decrypt a configuration value."""
        if isinstance(value, str) and value.startswith('encrypted:'):
            encrypted_data = value[10:].encode()  # Remove 'encrypted:' prefix
            decrypted = self.cipher_suite.decrypt(encrypted_data)
            return decrypted.decode()
        return value
    
    def encrypt_config(self, config: Dict[str, Any], keys_to_encrypt: List[str]) -> Dict[str, Any]:
        """Encrypt specified keys in a configuration dictionary."""
        encrypted_config = config.copy()
        
        for key in keys_to_encrypt:
            if key in encrypted_config:
                encrypted_config[key] = self.encrypt(str(encrypted_config[key]))
        
        return encrypted_config
    
    def decrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt all encrypted values in a configuration dictionary."""
        decrypted_config = {}
        
        for key, value in config.items():
            if isinstance(value, str) and value.startswith('encrypted:'):
                decrypted_config[key] = self.decrypt(value)
            elif isinstance(value, dict):
                decrypted_config[key] = self.decrypt_config(value)
            else:
                decrypted_config[key] = value
        
        return decrypted_config


class ConfigurationWatcher(FileSystemEventHandler):
    """Watches configuration files for changes and triggers reloading."""
    
    def __init__(self, config_manager, config_paths: List[str]):
        self.config_manager = config_manager
        self.config_paths = set(str(Path(p).resolve()) for p in config_paths)
        self.last_reload = {}
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            file_path = str(Path(event.src_path).resolve())
            if file_path in self.config_paths:
                # Debounce rapid file changes
                current_time = datetime.now().timestamp()
                last_time = self.last_reload.get(file_path, 0)
                
                if current_time - last_time > 1.0:  # 1 second debounce
                    self.last_reload[file_path] = current_time
                    self.config_manager._reload_config()


class ConfigurationPublisher:
    """Publishes default configuration files for packages."""
    
    @staticmethod
    def publish_config(package_name: str, source_path: str, target_path: str, 
                      force: bool = False) -> bool:
        """
        Publish configuration files from a package.
        
        Args:
            package_name: Name of the package
            source_path: Source configuration file path
            target_path: Target configuration file path
            force: Whether to overwrite existing files
            
        Returns:
            True if published successfully
        """
        source = Path(source_path)
        target = Path(target_path)
        
        if not source.exists():
            raise FileNotFoundError(f"Source configuration not found: {source}")
        
        if target.exists() and not force:
            return False  # Don't overwrite existing config
        
        # Create target directory if it doesn't exist
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the configuration file
        shutil.copy2(source, target)
        
        print(f"Published configuration for {package_name}: {target}")
        return True
    
    @staticmethod
    def get_published_configs() -> Dict[str, Dict[str, Any]]:
        """Get list of published configuration files."""
        config_registry = Path('.config_registry.json')
        
        if config_registry.exists():
            with open(config_registry, 'r') as f:
                return json.load(f)
        
        return {}
    
    @staticmethod
    def register_published_config(package_name: str, config_file: str, 
                                 metadata: Dict[str, Any] = None) -> None:
        """Register a published configuration file."""
        registry = ConfigurationPublisher.get_published_configs()
        
        if package_name not in registry:
            registry[package_name] = {}
        
        registry[package_name][config_file] = {
            'published_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        with open('.config_registry.json', 'w') as f:
            json.dump(registry, f, indent=2)


class ConfigurationMerger:
    """Merges configuration from multiple sources including packages."""
    
    @staticmethod
    def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple configuration dictionaries.
        Later configs override earlier ones.
        """
        result = {}
        
        for config in configs:
            result = ConfigurationMerger._deep_merge(result, config)
        
        return result
    
    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigurationMerger._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def merge_package_configs(base_config: Dict[str, Any], 
                            package_configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Merge package-specific configurations with base configuration."""
        configs_to_merge = [base_config]
        
        # Add package configs in dependency order (if available)
        for package_name, package_config in package_configs.items():
            if package_config:
                configs_to_merge.append(package_config)
        
        return ConfigurationMerger.merge_configs(*configs_to_merge)


class ConfigurationBackup:
    """Handles configuration backup and restore operations."""
    
    def __init__(self, backup_dir: str = '.config_backups'):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, config_files: List[str], backup_name: str = None) -> str:
        """
        Create a backup of configuration files.
        
        Args:
            config_files: List of configuration file paths
            backup_name: Optional backup name (defaults to timestamp)
            
        Returns:
            Backup directory path
        """
        if backup_name is None:
            backup_name = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        # Create manifest
        manifest = {
            'created_at': datetime.now().isoformat(),
            'files': []
        }
        
        # Backup each file
        for config_file in config_files:
            source = Path(config_file)
            if source.exists():
                # Preserve directory structure
                relative_path = source.name
                target = backup_path / relative_path
                
                shutil.copy2(source, target)
                
                manifest['files'].append({
                    'source': str(source),
                    'target': str(target),
                    'checksum': self._calculate_checksum(source)
                })
        
        # Save manifest
        with open(backup_path / 'manifest.json', 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return str(backup_path)
    
    def restore_backup(self, backup_name: str, verify_checksums: bool = True) -> bool:
        """
        Restore configuration from backup.
        
        Args:
            backup_name: Name of the backup to restore
            verify_checksums: Whether to verify file checksums
            
        Returns:
            True if restore was successful
        """
        backup_path = self.backup_dir / backup_name
        manifest_path = backup_path / 'manifest.json'
        
        if not manifest_path.exists():
            raise FileNotFoundError(f"Backup manifest not found: {manifest_path}")
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Restore each file
        for file_info in manifest['files']:
            source_path = Path(file_info['target'])
            target_path = Path(file_info['source'])
            
            if not source_path.exists():
                print(f"Warning: Backup file not found: {source_path}")
                continue
            
            # Verify checksum if requested
            if verify_checksums:
                current_checksum = self._calculate_checksum(source_path)
                if current_checksum != file_info['checksum']:
                    print(f"Warning: Checksum mismatch for {source_path}")
            
            # Create target directory if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Restore file
            shutil.copy2(source_path, target_path)
        
        return True
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                manifest_path = backup_dir / 'manifest.json'
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    
                    backups.append({
                        'name': backup_dir.name,
                        'path': str(backup_dir),
                        'created_at': manifest.get('created_at'),
                        'file_count': len(manifest.get('files', []))
                    })
        
        return sorted(backups, key=lambda x: x['created_at'], reverse=True)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        hasher = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        
        return hasher.hexdigest()


class AdvancedConfigManager:
    """Advanced configuration manager with all enhanced features."""
    
    def __init__(self, config_dir: str = 'config'):
        self.config_dir = Path(config_dir)
        self.config_cache: Dict[str, Any] = {}
        self.validator = ConfigurationValidator()
        self.encryption = ConfigurationEncryption()
        self.backup_manager = ConfigurationBackup()
        self.observer = None
        self.reload_callbacks: List[Callable] = []
        self._lock = threading.RLock()
    
    def load_config(self, config_name: str, encrypted_keys: List[str] = None) -> Dict[str, Any]:
        """
        Load configuration with decryption support.
        
        Args:
            config_name: Name of configuration file (without .py extension)
            encrypted_keys: List of keys that should be decrypted
            
        Returns:
            Configuration dictionary
        """
        with self._lock:
            if config_name in self.config_cache:
                return self.config_cache[config_name]
            
            config_file = self.config_dir / f"{config_name}.py"
            
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_file}")
            
            # Load configuration
            config = self._load_python_config(config_file)
            
            # Decrypt encrypted values
            if encrypted_keys:
                for key in encrypted_keys:
                    if key in config:
                        config[key] = self.encryption.decrypt(config[key])
            else:
                # Decrypt all encrypted values
                config = self.encryption.decrypt_config(config)
            
            # Validate configuration
            errors = self.validator.validate(config)
            if errors:
                raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
            
            # Cache configuration
            self.config_cache[config_name] = config
            
            return config
    
    def save_config(self, config_name: str, config: Dict[str, Any], 
                   keys_to_encrypt: List[str] = None) -> None:
        """
        Save configuration with encryption support.
        
        Args:
            config_name: Name of configuration file
            config: Configuration dictionary
            keys_to_encrypt: List of keys to encrypt before saving
        """
        with self._lock:
            config_file = self.config_dir / f"{config_name}.py"
            
            # Encrypt sensitive values
            if keys_to_encrypt:
                config = self.encryption.encrypt_config(config, keys_to_encrypt)
            
            # Save configuration
            self._save_python_config(config_file, config)
            
            # Update cache
            self.config_cache[config_name] = config
    
    def merge_package_configs(self, base_config_name: str, 
                            package_configs: Dict[str, str]) -> Dict[str, Any]:
        """
        Merge base configuration with package configurations.
        
        Args:
            base_config_name: Name of base configuration
            package_configs: Dict of package_name -> config_name mappings
            
        Returns:
            Merged configuration
        """
        base_config = self.load_config(base_config_name)
        
        package_config_dicts = {}
        for package_name, config_name in package_configs.items():
            try:
                package_config_dicts[package_name] = self.load_config(config_name)
            except FileNotFoundError:
                print(f"Warning: Package config not found: {config_name}")
                package_config_dicts[package_name] = {}
        
        return ConfigurationMerger.merge_package_configs(base_config, package_config_dicts)
    
    def enable_hot_reload(self, config_names: List[str]) -> None:
        """Enable hot-reloading for specified configuration files."""
        if self.observer is not None:
            return  # Already watching
        
        config_paths = [str(self.config_dir / f"{name}.py") for name in config_names]
        
        event_handler = ConfigurationWatcher(self, config_paths)
        
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.config_dir), recursive=False)
        self.observer.start()
    
    def disable_hot_reload(self) -> None:
        """Disable hot-reloading."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
    
    def add_reload_callback(self, callback: Callable) -> None:
        """Add a callback to be called when configuration is reloaded."""
        self.reload_callbacks.append(callback)
    
    def create_backup(self, config_names: List[str], backup_name: str = None) -> str:
        """Create a backup of specified configuration files."""
        config_files = [str(self.config_dir / f"{name}.py") for name in config_names]
        return self.backup_manager.create_backup(config_files, backup_name)
    
    def restore_backup(self, backup_name: str) -> None:
        """Restore configuration from backup."""
        self.backup_manager.restore_backup(backup_name)
        # Clear cache to force reload
        self.config_cache.clear()
    
    def _load_python_config(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration from Python file."""
        import importlib.util
        
        spec = importlib.util.spec_from_file_location("config", config_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Extract configuration variables (uppercase only)
        config = {}
        for name in dir(module):
            if name.isupper() and not name.startswith('_'):
                config[name.lower()] = getattr(module, name)
        
        return config
    
    def _save_python_config(self, config_file: Path, config: Dict[str, Any]) -> None:
        """Save configuration to Python file."""
        lines = [
            '"""',
            f'Configuration file: {config_file.name}',
            f'Generated at: {datetime.now().isoformat()}',
            '"""',
            ''
        ]
        
        for key, value in config.items():
            lines.append(f"{key.upper()} = {repr(value)}")
        
        lines.append('')  # Final newline
        
        with open(config_file, 'w') as f:
            f.write('\n'.join(lines))
    
    def _reload_config(self) -> None:
        """Reload all cached configurations."""
        with self._lock:
            # Clear cache
            old_cache = self.config_cache.copy()
            self.config_cache.clear()
            
            # Reload configurations
            for config_name in old_cache.keys():
                try:
                    self.load_config(config_name)
                except Exception as e:
                    print(f"Error reloading config {config_name}: {e}")
                    # Restore old config on error
                    self.config_cache[config_name] = old_cache[config_name]
            
            # Call reload callbacks
            for callback in self.reload_callbacks:
                try:
                    callback()
                except Exception as e:
                    print(f"Error in reload callback: {e}")
    
    def register_validation_schema(self, config_name: str, key: str, 
                                 schema: Dict[str, Any]) -> None:
        """Register validation schema for a configuration key."""
        schema_key = f"{config_name}.{key}"
        self.validator.register_schema(schema_key, schema)
    
    def __del__(self):
        """Cleanup resources."""
        self.disable_hot_reload()