"""
Environment Management CLI Commands

Provides CLI commands for environment management and setup.
"""

import json
import sys
from typing import Dict, Any
from ..command import Command
from ...environment.manager import get_environment_manager
from ...environment.setup import EnvironmentSetup
from ...environment.validator import EnvironmentValidator


class EnvironmentStatusCommand(Command):
    """Show environment status and configuration."""
    
    name = "env:status"
    description = "Display current environment status and configuration"
    
    def __init__(self):
        super().__init__()
        self.add_argument('--json', action='store_true', 
                         help='Output in JSON format')
        self.add_argument('--validation', action='store_true',
                         help='Include validation details')
    
    def handle(self, **options):
        """Handle the env:status command."""
        try:
            manager = get_environment_manager()
            status = manager.get_environment_status()
            
            if options.get('json', False):
                print(json.dumps(status, indent=2, default=str))
                return
            
            # Display formatted status
            env = status['environment']
            validation = status['validation']
            features = status['features']
            
            self.info("Environment Status")
            print("=" * 50)
            print(f"Environment: {env['name']} ({env['type']})")
            print(f"Debug Mode: {'Enabled' if env['is_debug'] else 'Disabled'}")
            print(f"Hostname: {env['hostname']}")
            print(f"Platform: {env['platform']}")
            print(f"Python: {env['python_version']}")
            print(f"Working Dir: {env['working_directory']}")
            print()
            
            # Validation status
            if validation['is_valid']:
                self.success("✅ Environment configuration is valid")
            else:
                self.error(f"❌ Environment has {validation['errors']} errors")
                if validation['warnings'] > 0:
                    self.warning(f"⚠️  Environment has {validation['warnings']} warnings")
            
            if options.get('validation', False) and not validation['is_valid']:
                print("\nValidation Issues:")
                for error in validation['error_details']:
                    print(f"  ❌ {error['variable']}: {error['message']}")
                for warning in validation['warning_details']:
                    print(f"  ⚠️  {warning['variable']}: {warning['message']}")
            
            print()
            
            # Features
            print(f"Features: {features['enabled_count']} enabled")
            if features['enabled_flags']:
                print("Enabled features:", ", ".join(features['enabled_flags']))
            
            print()
            
            # Available environments
            available = status['available_environments']
            if available:
                print(f"Available environments: {', '.join(available)}")
            
        except Exception as e:
            self.error(f"Error getting environment status: {e}")


class EnvironmentInitCommand(Command):
    """Initialize a new environment."""
    
    name = "env:init"
    description = "Initialize a new environment configuration"
    
    def __init__(self):
        super().__init__()
        self.add_argument('environment', help='Environment name to initialize')
        self.add_argument('--force', action='store_true',
                         help='Overwrite existing configuration')
        self.add_argument('--no-deps', action='store_true',
                         help='Skip dependency installation')
        self.add_argument('--no-db', action='store_true',
                         help='Skip database initialization')
        self.add_argument('--template-vars', nargs='*',
                         help='Template variables in key=value format')
    
    def handle(self, **options):
        """Handle the env:init command."""
        environment_name = options['environment']
        force = options.get('force', False)
        
        try:
            setup = EnvironmentSetup()
            
            # Check if environment already exists
            if not force and environment_name in setup.list_environments():
                self.error(f"Environment '{environment_name}' already exists. Use --force to overwrite.")
                return
            
            # Parse template variables
            template_vars = {}
            if options.get('template_vars'):
                for var in options['template_vars']:
                    if '=' in var:
                        key, value = var.split('=', 1)
                        template_vars[key.strip()] = value.strip()
            
            # Setup configuration
            config = {
                'template_vars': template_vars,
                'install_dependencies': not options.get('no_deps', False),
                'initialize_database': not options.get('no_db', False)
            }
            
            self.info(f"Initializing {environment_name} environment...")
            
            success = setup.setup_environment(environment_name, config)
            
            if success:
                self.success(f"Environment '{environment_name}' initialized successfully")
                
                # Validate the new environment
                validator = EnvironmentValidator()
                validation = validator.get_validation_summary(environment_name)
                
                if not validation['is_valid']:
                    self.warning(f"Environment has {validation['errors']} validation errors")
                    self.info("Run 'larapy env:validate' to see details")
            else:
                self.error(f"Failed to initialize environment '{environment_name}'")
                
        except Exception as e:
            self.error(f"Error initializing environment: {e}")


class EnvironmentSwitchCommand(Command):
    """Switch to a different environment."""
    
    name = "env:switch"
    description = "Switch to a different environment"
    
    def __init__(self):
        super().__init__()
        self.add_argument('environment', help='Environment name to switch to')
        self.add_argument('--backup', action='store_true',
                         help='Backup current environment before switching')
    
    def handle(self, **options):
        """Handle the env:switch command."""
        environment_name = options['environment']
        
        try:
            setup = EnvironmentSetup()
            
            # Check if target environment exists
            if environment_name not in setup.list_environments():
                self.error(f"Environment '{environment_name}' not found")
                self.info("Available environments:", ", ".join(setup.list_environments()))
                return
            
            # Get current environment for backup
            if options.get('backup', False):
                manager = get_environment_manager()
                current_env = manager.get_current_environment()
                backup_name = f"{current_env.name}_backup"
                
                self.info(f"Creating backup as '{backup_name}'...")
                setup.export_environment(current_env.name, f".env.{backup_name}")
            
            # Switch environment
            self.info(f"Switching to {environment_name} environment...")
            
            success = setup.switch_environment(environment_name)
            
            if success:
                self.success(f"Switched to '{environment_name}' environment")
                
                # Validate new environment
                validator = EnvironmentValidator()
                validation = validator.get_validation_summary(environment_name)
                
                if validation['is_valid']:
                    self.success("Environment configuration is valid")
                else:
                    self.warning(f"Environment has {validation['errors']} validation errors")
            else:
                self.error(f"Failed to switch to environment '{environment_name}'")
                
        except Exception as e:
            self.error(f"Error switching environment: {e}")


class EnvironmentListCommand(Command):
    """List available environments."""
    
    name = "env:list"
    description = "List all available environments"
    
    def __init__(self):
        super().__init__()
        self.add_argument('--details', action='store_true',
                         help='Show detailed information for each environment')
    
    def handle(self, **options):
        """Handle the env:list command."""
        try:
            setup = EnvironmentSetup()
            manager = get_environment_manager()
            
            environments = setup.list_environments()
            current_env = manager.get_current_environment()
            
            if not environments:
                self.warning("No environments found")
                return
            
            self.info("Available Environments:")
            print("-" * 40)
            
            for env_name in environments:
                indicator = " (current)" if env_name == current_env.name else ""
                print(f"  {env_name}{indicator}")
                
                if options.get('details', False):
                    try:
                        env_info = setup.get_environment_info(env_name)
                        validation = env_info['validation']
                        
                        status = "✅ Valid" if validation['is_valid'] else f"❌ {validation['errors']} errors"
                        print(f"    Status: {status}")
                        print(f"    Type: {env_info['type']}")
                        print(f"    Debug: {'Yes' if env_info['is_debug'] else 'No'}")
                        print()
                    except:
                        print("    Status: Unknown")
                        print()
                        
        except Exception as e:
            self.error(f"Error listing environments: {e}")


class EnvironmentValidateCommand(Command):
    """Validate environment configuration."""
    
    name = "env:validate"
    description = "Validate environment variable configuration"
    
    def __init__(self):
        super().__init__()
        self.add_argument('environment', nargs='?', 
                         help='Environment to validate (current if not specified)')
        self.add_argument('--fix', action='store_true',
                         help='Attempt to fix validation issues')
    
    def handle(self, **options):
        """Handle the env:validate command."""
        environment_name = options.get('environment')
        
        try:
            validator = EnvironmentValidator()
            
            if environment_name is None:
                manager = get_environment_manager()
                environment_name = manager.get_current_environment().name
            
            self.info(f"Validating {environment_name} environment...")
            
            validation_results = validator.validate(environment_name)
            summary = validator.get_validation_summary(environment_name)
            
            # Display summary
            if summary['is_valid']:
                self.success("✅ Environment configuration is valid")
            else:
                self.error(f"❌ Found {summary['errors']} errors and {summary['warnings']} warnings")
            
            # Display details
            errors = [r for r in validation_results if not r.is_valid and r.level.name == 'ERROR']
            warnings = [r for r in validation_results if not r.is_valid and r.level.name == 'WARNING']
            
            if errors:
                print("\nErrors:")
                for result in errors:
                    print(f"  ❌ {result.variable_name}: {result.message}")
            
            if warnings:
                print("\nWarnings:")
                for result in warnings:
                    print(f"  ⚠️  {result.variable_name}: {result.message}")
            
            # Suggest fixes if requested
            if options.get('fix', False) and not summary['is_valid']:
                self._suggest_fixes(errors, warnings)
            
            # Exit with error code if validation failed
            if not summary['is_valid']:
                sys.exit(1)
                
        except Exception as e:
            self.error(f"Error validating environment: {e}")
            sys.exit(1)
    
    def _suggest_fixes(self, errors, warnings):
        """Suggest fixes for validation issues."""
        print("\nSuggested fixes:")
        
        for result in errors + warnings:
            var_name = result.variable_name
            
            if 'required' in result.message.lower():
                print(f"  Add {var_name} to your .env file")
            elif 'type' in result.message.lower():
                print(f"  Check the format of {var_name} value")
            elif 'pattern' in result.message.lower():
                print(f"  Verify {var_name} follows the expected format")
            elif 'choices' in result.message.lower():
                print(f"  Set {var_name} to one of the valid options")


class EnvironmentExportCommand(Command):
    """Export environment configuration."""
    
    name = "env:export"
    description = "Export environment configuration to a file"
    
    def __init__(self):
        super().__init__()
        self.add_argument('environment', help='Environment to export')
        self.add_argument('output_file', help='Output file path')
        self.add_argument('--include-secrets', action='store_true',
                         help='Include sensitive values in export')
    
    def handle(self, **options):
        """Handle the env:export command."""
        environment_name = options['environment']
        output_file = options['output_file']
        include_secrets = options.get('include_secrets', False)
        
        try:
            setup = EnvironmentSetup()
            
            success = setup.export_environment(
                environment_name, output_file, include_secrets
            )
            
            if success:
                self.success(f"Environment '{environment_name}' exported to {output_file}")
                if not include_secrets:
                    self.info("Sensitive values were redacted. Use --include-secrets to include them.")
            else:
                self.error(f"Failed to export environment '{environment_name}'")
                
        except Exception as e:
            self.error(f"Error exporting environment: {e}")


class EnvironmentImportCommand(Command):
    """Import environment configuration."""
    
    name = "env:import"
    description = "Import environment configuration from a file"
    
    def __init__(self):
        super().__init__()
        self.add_argument('environment', help='Target environment name')
        self.add_argument('input_file', help='Input file path')
        self.add_argument('--force', action='store_true',
                         help='Overwrite existing environment')
    
    def handle(self, **options):
        """Handle the env:import command."""
        environment_name = options['environment']
        input_file = options['input_file']
        force = options.get('force', False)
        
        try:
            setup = EnvironmentSetup()
            
            # Check if environment exists
            if not force and environment_name in setup.list_environments():
                self.error(f"Environment '{environment_name}' already exists. Use --force to overwrite.")
                return
            
            success = setup.import_environment(environment_name, input_file)
            
            if success:
                self.success(f"Environment '{environment_name}' imported from {input_file}")
                
                # Validate imported environment
                validator = EnvironmentValidator()
                validation = validator.get_validation_summary(environment_name)
                
                if validation['is_valid']:
                    self.success("Imported environment is valid")
                else:
                    self.warning(f"Imported environment has {validation['errors']} validation errors")
            else:
                self.error(f"Failed to import environment '{environment_name}'")
                
        except Exception as e:
            self.error(f"Error importing environment: {e}")


class EnvironmentCloneCommand(Command):
    """Clone an environment configuration."""
    
    name = "env:clone"
    description = "Clone an environment configuration to create a new one"
    
    def __init__(self):
        super().__init__()
        self.add_argument('source', help='Source environment name')
        self.add_argument('target', help='Target environment name')
        self.add_argument('--modifications', nargs='*',
                         help='Modifications in key=value format')
    
    def handle(self, **options):
        """Handle the env:clone command."""
        source_env = options['source']
        target_env = options['target']
        
        try:
            setup = EnvironmentSetup()
            
            # Check if source exists
            if source_env not in setup.list_environments():
                self.error(f"Source environment '{source_env}' not found")
                return
            
            # Check if target already exists
            if target_env in setup.list_environments():
                self.error(f"Target environment '{target_env}' already exists")
                return
            
            # Parse modifications
            modifications = {}
            if options.get('modifications'):
                for mod in options['modifications']:
                    if '=' in mod:
                        key, value = mod.split('=', 1)
                        modifications[key.strip()] = value.strip()
            
            success = setup.clone_environment(source_env, target_env, modifications)
            
            if success:
                self.success(f"Environment '{target_env}' cloned from '{source_env}'")
                if modifications:
                    self.info(f"Applied {len(modifications)} modifications")
                    
                # Validate cloned environment
                validator = EnvironmentValidator()
                validation = validator.get_validation_summary(target_env)
                
                if validation['is_valid']:
                    self.success("Cloned environment is valid")
                else:
                    self.warning(f"Cloned environment has {validation['errors']} validation errors")
            else:
                self.error(f"Failed to clone environment")
                
        except Exception as e:
            self.error(f"Error cloning environment: {e}")