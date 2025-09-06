"""
Configuration Management CLI Commands

Provides CLI commands for advanced configuration management including:
- Publishing configuration files
- Creating and restoring backups
- Validating configuration
- Managing encrypted values
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from ..command import Command
from ...config.advanced import (
    AdvancedConfigManager, 
    ConfigurationPublisher, 
    ConfigurationValidator,
    ConfigurationEncryption,
    ConfigurationBackup
)


class ConfigPublishCommand(Command):
    """Publish default configuration files from packages."""
    
    name = "config:publish"
    description = "Publish configuration files from packages"
    
    def __init__(self):
        super().__init__()
        self.add_argument('package', help='Package name to publish config from')
        self.add_argument('--force', action='store_true', 
                         help='Overwrite existing configuration files')
        self.add_argument('--tag', help='Specific configuration tag to publish')
    
    def handle(self, **options):
        """Handle the config:publish command."""
        package_name = options['package']
        force = options.get('force', False)
        tag = options.get('tag')
        
        try:
            # In a real implementation, this would scan the package for config files
            # For now, we'll simulate publishing a sample config
            source_configs = self._find_package_configs(package_name, tag)
            
            if not source_configs:
                self.error(f"No configuration files found for package: {package_name}")
                return
            
            published_count = 0
            for source_path, target_path in source_configs.items():
                try:
                    success = ConfigurationPublisher.publish_config(
                        package_name, source_path, target_path, force
                    )
                    if success:
                        published_count += 1
                        self.info(f"Published: {target_path}")
                    else:
                        self.warning(f"Skipped (already exists): {target_path}")
                        
                    # Register the published config
                    ConfigurationPublisher.register_published_config(
                        package_name, target_path, {'tag': tag}
                    )
                    
                except Exception as e:
                    self.error(f"Failed to publish {source_path}: {e}")
            
            self.info(f"Published {published_count} configuration files for {package_name}")
            
        except Exception as e:
            self.error(f"Error publishing configuration: {e}")
    
    def _find_package_configs(self, package_name: str, tag: str = None) -> Dict[str, str]:
        """Find configuration files in a package."""
        # This is a simplified implementation
        # In a real scenario, this would scan package directories
        
        configs = {}
        
        # Example: Look for config files in the package
        package_config_dir = Path(f"packages/{package_name}/config")
        if package_config_dir.exists():
            for config_file in package_config_dir.glob("*.py"):
                target_path = f"config/{config_file.name}"
                configs[str(config_file)] = target_path
        
        return configs


class ConfigBackupCommand(Command):
    """Create configuration backups."""
    
    name = "config:backup"
    description = "Create a backup of configuration files"
    
    def __init__(self):
        super().__init__()
        self.add_argument('--name', help='Backup name (defaults to timestamp)')
        self.add_argument('--configs', nargs='*', 
                         help='Specific configuration files to backup')
    
    def handle(self, **options):
        """Handle the config:backup command."""
        backup_name = options.get('name')
        config_names = options.get('configs', [])
        
        try:
            backup_manager = ConfigurationBackup()
            
            # If no specific configs specified, backup all config files
            if not config_names:
                config_dir = Path('config')
                if config_dir.exists():
                    config_files = [str(f) for f in config_dir.glob('*.py')]
                else:
                    config_files = []
            else:
                config_files = [f"config/{name}.py" for name in config_names]
            
            if not config_files:
                self.warning("No configuration files found to backup")
                return
            
            backup_path = backup_manager.create_backup(config_files, backup_name)
            
            self.info(f"Configuration backup created: {backup_path}")
            self.info(f"Backed up {len(config_files)} configuration files")
            
        except Exception as e:
            self.error(f"Error creating backup: {e}")


class ConfigRestoreCommand(Command):
    """Restore configuration from backup."""
    
    name = "config:restore"
    description = "Restore configuration files from backup"
    
    def __init__(self):
        super().__init__()
        self.add_argument('backup_name', help='Name of backup to restore')
        self.add_argument('--no-verify', action='store_true',
                         help='Skip checksum verification')
    
    def handle(self, **options):
        """Handle the config:restore command."""
        backup_name = options['backup_name']
        verify_checksums = not options.get('no_verify', False)
        
        try:
            backup_manager = ConfigurationBackup()
            
            # Confirm restore operation
            self.warning(f"This will overwrite existing configuration files!")
            if not self._confirm("Are you sure you want to continue?"):
                self.info("Restore cancelled")
                return
            
            success = backup_manager.restore_backup(backup_name, verify_checksums)
            
            if success:
                self.info(f"Configuration restored from backup: {backup_name}")
            else:
                self.error("Failed to restore configuration")
                
        except Exception as e:
            self.error(f"Error restoring backup: {e}")
    
    def _confirm(self, message: str) -> bool:
        """Get user confirmation."""
        try:
            response = input(f"{message} [y/N]: ").lower().strip()
            return response in ['y', 'yes']
        except (EOFError, KeyboardInterrupt):
            return False


class ConfigListBackupsCommand(Command):
    """List available configuration backups."""
    
    name = "config:list-backups"
    description = "List available configuration backups"
    
    def handle(self, **options):
        """Handle the config:list-backups command."""
        try:
            backup_manager = ConfigurationBackup()
            backups = backup_manager.list_backups()
            
            if not backups:
                self.info("No configuration backups found")
                return
            
            self.info("Available configuration backups:")
            self.info("")
            
            # Print table header
            print(f"{'Name':<20} {'Created At':<20} {'Files':<8}")
            print("-" * 50)
            
            for backup in backups:
                created_at = backup['created_at'][:19] if backup['created_at'] else 'Unknown'
                print(f"{backup['name']:<20} {created_at:<20} {backup['file_count']:<8}")
                
        except Exception as e:
            self.error(f"Error listing backups: {e}")


class ConfigValidateCommand(Command):
    """Validate configuration files."""
    
    name = "config:validate"
    description = "Validate configuration files against schemas"
    
    def __init__(self):
        super().__init__()
        self.add_argument('configs', nargs='*', 
                         help='Specific configuration files to validate')
    
    def handle(self, **options):
        """Handle the config:validate command."""
        config_names = options.get('configs', [])
        
        try:
            config_manager = AdvancedConfigManager()
            
            # If no specific configs specified, validate all
            if not config_names:
                config_dir = Path('config')
                if config_dir.exists():
                    config_names = [f.stem for f in config_dir.glob('*.py')]
                else:
                    config_names = []
            
            if not config_names:
                self.warning("No configuration files found to validate")
                return
            
            errors_found = False
            
            for config_name in config_names:
                try:
                    config = config_manager.load_config(config_name)
                    self.info(f"✓ {config_name}: Valid")
                except Exception as e:
                    self.error(f"✗ {config_name}: {e}")
                    errors_found = True
            
            if not errors_found:
                self.info("All configuration files are valid")
            else:
                sys.exit(1)  # Exit with error code
                
        except Exception as e:
            self.error(f"Error validating configuration: {e}")
            sys.exit(1)


class ConfigEncryptCommand(Command):
    """Encrypt configuration values."""
    
    name = "config:encrypt"
    description = "Encrypt sensitive configuration values"
    
    def __init__(self):
        super().__init__()
        self.add_argument('config', help='Configuration file name')
        self.add_argument('keys', nargs='+', help='Keys to encrypt')
    
    def handle(self, **options):
        """Handle the config:encrypt command."""
        config_name = options['config']
        keys_to_encrypt = options['keys']
        
        try:
            config_manager = AdvancedConfigManager()
            
            # Load current configuration
            config = config_manager.load_config(config_name)
            
            # Check which keys exist
            missing_keys = [key for key in keys_to_encrypt if key not in config]
            if missing_keys:
                self.warning(f"Keys not found in config: {', '.join(missing_keys)}")
            
            existing_keys = [key for key in keys_to_encrypt if key in config]
            if not existing_keys:
                self.error("No valid keys to encrypt")
                return
            
            # Create backup before encryption
            backup_path = config_manager.create_backup([config_name], 
                                                      f"{config_name}_pre_encrypt")
            self.info(f"Backup created: {backup_path}")
            
            # Save with encryption
            config_manager.save_config(config_name, config, existing_keys)
            
            self.info(f"Encrypted {len(existing_keys)} keys in {config_name}")
            for key in existing_keys:
                self.info(f"  - {key}")
                
        except Exception as e:
            self.error(f"Error encrypting configuration: {e}")


class ConfigDecryptCommand(Command):
    """Decrypt configuration values for viewing."""
    
    name = "config:decrypt"
    description = "Decrypt and display configuration values"
    
    def __init__(self):
        super().__init__()
        self.add_argument('config', help='Configuration file name')
        self.add_argument('keys', nargs='*', help='Specific keys to decrypt (all if none specified)')
    
    def handle(self, **options):
        """Handle the config:decrypt command."""
        config_name = options['config']
        keys_to_show = options.get('keys', [])
        
        try:
            config_manager = AdvancedConfigManager()
            
            # Load and decrypt configuration
            config = config_manager.load_config(config_name)
            
            self.info(f"Configuration: {config_name}")
            self.info("")
            
            # Show specific keys or all keys
            keys_to_display = keys_to_show if keys_to_show else config.keys()
            
            for key in keys_to_display:
                if key in config:
                    value = config[key]
                    # Mask sensitive-looking values
                    if any(sensitive in key.lower() for sensitive in 
                          ['password', 'secret', 'key', 'token']):
                        display_value = '*' * len(str(value)) if value else '(empty)'
                    else:
                        display_value = str(value)
                    
                    print(f"{key}: {display_value}")
                else:
                    self.warning(f"Key not found: {key}")
                    
        except Exception as e:
            self.error(f"Error decrypting configuration: {e}")


class ConfigHotReloadCommand(Command):
    """Enable/disable configuration hot-reloading."""
    
    name = "config:hot-reload"
    description = "Enable or disable configuration hot-reloading"
    
    def __init__(self):
        super().__init__()
        self.add_argument('action', choices=['enable', 'disable'], 
                         help='Action to perform')
        self.add_argument('--configs', nargs='*',
                         help='Configuration files to watch (all if none specified)')
    
    def handle(self, **options):
        """Handle the config:hot-reload command."""
        action = options['action']
        config_names = options.get('configs', [])
        
        try:
            config_manager = AdvancedConfigManager()
            
            if action == 'enable':
                # If no specific configs, watch all config files
                if not config_names:
                    config_dir = Path('config')
                    if config_dir.exists():
                        config_names = [f.stem for f in config_dir.glob('*.py')]
                
                if not config_names:
                    self.error("No configuration files found to watch")
                    return
                
                config_manager.enable_hot_reload(config_names)
                self.info(f"Hot-reload enabled for: {', '.join(config_names)}")
                self.info("Configuration will be reloaded automatically when files change")
                
                # Keep the process running
                try:
                    input("Press Enter to stop watching...")
                except KeyboardInterrupt:
                    pass
                
                config_manager.disable_hot_reload()
                self.info("Hot-reload disabled")
                
            else:  # disable
                config_manager.disable_hot_reload()
                self.info("Hot-reload disabled")
                
        except Exception as e:
            self.error(f"Error managing hot-reload: {e}")


class ConfigMergeCommand(Command):
    """Merge configuration files from packages."""
    
    name = "config:merge"
    description = "Merge configuration files with package overrides"
    
    def __init__(self):
        super().__init__()
        self.add_argument('base_config', help='Base configuration name')
        self.add_argument('--packages', nargs='*', 
                         help='Package configurations to merge')
        self.add_argument('--output', help='Output merged configuration to file')
        self.add_argument('--dry-run', action='store_true',
                         help='Show merge result without saving')
    
    def handle(self, **options):
        """Handle the config:merge command."""
        base_config = options['base_config']
        packages = options.get('packages', [])
        output_file = options.get('output')
        dry_run = options.get('dry_run', False)
        
        try:
            config_manager = AdvancedConfigManager()
            
            # Build package config mapping
            package_configs = {}
            for package in packages:
                package_configs[package] = f"{package}_config"
            
            # Merge configurations
            merged_config = config_manager.merge_package_configs(
                base_config, package_configs
            )
            
            if dry_run:
                self.info("Merged configuration (dry run):")
                import json
                print(json.dumps(merged_config, indent=2, default=str))
                return
            
            # Save merged configuration
            if output_file:
                config_manager.save_config(output_file, merged_config)
                self.info(f"Merged configuration saved to: {output_file}")
            else:
                # Display merged config
                self.info("Merged configuration:")
                import json
                print(json.dumps(merged_config, indent=2, default=str))
                
        except Exception as e:
            self.error(f"Error merging configuration: {e}")