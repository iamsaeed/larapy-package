"""
Environment Setup Utilities

This module provides utilities for setting up and managing environments.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import tempfile
import subprocess
from .detector import EnvironmentDetector
from .validator import EnvironmentValidator


class EnvironmentSetup:
    """Utilities for environment setup and management."""
    
    def __init__(self):
        self.detector = EnvironmentDetector()
        self.validator = EnvironmentValidator()
        self.templates_dir = Path(__file__).parent / 'templates'
    
    def create_environment_file(self, environment_name: str, 
                               output_path: str = '.env',
                               template_vars: Dict[str, str] = None) -> bool:
        """
        Create an environment file for a specific environment.
        
        Args:
            environment_name: Name of the environment
            output_path: Path where to create the .env file
            template_vars: Template variables to substitute
            
        Returns:
            True if file was created successfully
        """
        try:
            template_vars = template_vars or {}
            
            # Get environment template
            template_content = self._get_environment_template(environment_name)
            
            # Substitute template variables
            for var_name, var_value in template_vars.items():
                template_content = template_content.replace(f"{{{var_name}}}", str(var_value))
            
            # Write to file
            with open(output_path, 'w') as f:
                f.write(template_content)
            
            return True
            
        except Exception as e:
            print(f"Error creating environment file: {e}")
            return False
    
    def validate_environment(self, environment_name: str = None) -> Dict[str, Any]:
        """
        Validate the current environment configuration.
        
        Args:
            environment_name: Environment name (auto-detected if not provided)
            
        Returns:
            Validation summary
        """
        if environment_name is None:
            env_info = self.detector.detect()
            environment_name = env_info.name
        
        return self.validator.get_validation_summary(environment_name)
    
    def setup_environment(self, environment_name: str, 
                         config: Dict[str, Any] = None) -> bool:
        """
        Set up an environment with all necessary configurations.
        
        Args:
            environment_name: Name of the environment to setup
            config: Environment-specific configuration
            
        Returns:
            True if setup was successful
        """
        config = config or {}
        
        try:
            # Create environment file
            env_file_created = self.create_environment_file(
                environment_name, 
                config.get('env_file', '.env'),
                config.get('template_vars', {})
            )
            
            if not env_file_created:
                return False
            
            # Create necessary directories
            self._create_directories(environment_name, config)
            
            # Install environment-specific dependencies
            if config.get('install_dependencies', True):
                self._install_dependencies(environment_name, config)
            
            # Run environment-specific setup commands
            setup_commands = config.get('setup_commands', [])
            for command in setup_commands:
                self._run_command(command)
            
            # Initialize database if needed
            if config.get('initialize_database', False):
                self._initialize_database(environment_name)
            
            # Create sample data if needed
            if config.get('create_sample_data', False):
                self._create_sample_data(environment_name)
            
            return True
            
        except Exception as e:
            print(f"Error setting up environment: {e}")
            return False
    
    def clone_environment(self, source_env: str, target_env: str, 
                         modifications: Dict[str, str] = None) -> bool:
        """
        Clone an environment configuration to create a new one.
        
        Args:
            source_env: Source environment name
            target_env: Target environment name
            modifications: Modifications to apply to cloned environment
            
        Returns:
            True if clone was successful
        """
        try:
            modifications = modifications or {}
            
            # Read source environment file
            source_file = f".env.{source_env}"
            if not os.path.exists(source_file):
                source_file = ".env"
            
            if not os.path.exists(source_file):
                print(f"Source environment file not found: {source_file}")
                return False
            
            with open(source_file, 'r') as f:
                content = f.read()
            
            # Apply modifications
            for key, value in modifications.items():
                # Replace existing value or add new one
                if f"{key}=" in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith(f"{key}="):
                            lines[i] = f"{key}={value}"
                            break
                    content = '\n'.join(lines)
                else:
                    content += f"\n{key}={value}"
            
            # Write to target file
            target_file = f".env.{target_env}"
            with open(target_file, 'w') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"Error cloning environment: {e}")
            return False
    
    def switch_environment(self, environment_name: str) -> bool:
        """
        Switch to a different environment.
        
        Args:
            environment_name: Name of the environment to switch to
            
        Returns:
            True if switch was successful
        """
        try:
            env_file = f".env.{environment_name}"
            
            if not os.path.exists(env_file):
                print(f"Environment file not found: {env_file}")
                return False
            
            # Backup current .env file
            if os.path.exists('.env'):
                shutil.copy('.env', '.env.backup')
            
            # Copy environment file to .env
            shutil.copy(env_file, '.env')
            
            print(f"Switched to {environment_name} environment")
            return True
            
        except Exception as e:
            print(f"Error switching environment: {e}")
            return False
    
    def list_environments(self) -> List[str]:
        """
        List available environments.
        
        Returns:
            List of environment names
        """
        environments = []
        
        # Look for .env.* files
        for file_path in Path('.').glob('.env.*'):
            if file_path.name != '.env.backup':
                env_name = file_path.name[5:]  # Remove '.env.' prefix
                environments.append(env_name)
        
        # Add current if .env exists but no specific environment files
        if os.path.exists('.env') and not environments:
            current_env = self.detector.detect()
            environments.append(current_env.name)
        
        return sorted(environments)
    
    def get_environment_info(self, environment_name: str = None) -> Dict[str, Any]:
        """
        Get information about an environment.
        
        Args:
            environment_name: Environment name (current if not provided)
            
        Returns:
            Environment information dictionary
        """
        if environment_name is None:
            env_info = self.detector.detect()
        else:
            # Temporarily switch to get info
            original_env = os.getenv('APP_ENV')
            os.environ['APP_ENV'] = environment_name
            env_info = self.detector.detect()
            if original_env:
                os.environ['APP_ENV'] = original_env
            else:
                os.environ.pop('APP_ENV', None)
        
        # Get validation info
        validation_info = self.validator.get_validation_summary(env_info.name)
        
        return {
            'name': env_info.name,
            'type': env_info.type.value,
            'is_debug': env_info.is_debug,
            'is_testing': env_info.is_testing,
            'is_production': env_info.is_production,
            'hostname': env_info.hostname,
            'platform': env_info.platform,
            'python_version': env_info.python_version,
            'working_directory': env_info.working_directory,
            'features': env_info.features,
            'metadata': env_info.metadata,
            'validation': validation_info
        }
    
    def export_environment(self, environment_name: str, export_path: str, 
                          include_secrets: bool = False) -> bool:
        """
        Export environment configuration to a file.
        
        Args:
            environment_name: Environment name to export
            export_path: Path to export file
            include_secrets: Whether to include sensitive values
            
        Returns:
            True if export was successful
        """
        try:
            env_file = f".env.{environment_name}"
            if not os.path.exists(env_file):
                env_file = ".env"
            
            if not os.path.exists(env_file):
                print(f"Environment file not found for {environment_name}")
                return False
            
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Filter out secrets if requested
            if not include_secrets:
                secret_keys = ['SECRET_KEY', 'API_KEY', 'PASSWORD', 'TOKEN', 'PRIVATE']
                lines = content.split('\n')
                filtered_lines = []
                
                for line in lines:
                    if '=' in line:
                        key = line.split('=')[0].strip()
                        if any(secret in key.upper() for secret in secret_keys):
                            filtered_lines.append(f"{key}=***REDACTED***")
                        else:
                            filtered_lines.append(line)
                    else:
                        filtered_lines.append(line)
                
                content = '\n'.join(filtered_lines)
            
            # Write export file
            with open(export_path, 'w') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"Error exporting environment: {e}")
            return False
    
    def import_environment(self, environment_name: str, import_path: str) -> bool:
        """
        Import environment configuration from a file.
        
        Args:
            environment_name: Target environment name
            import_path: Path to import file
            
        Returns:
            True if import was successful
        """
        try:
            if not os.path.exists(import_path):
                print(f"Import file not found: {import_path}")
                return False
            
            target_file = f".env.{environment_name}"
            shutil.copy(import_path, target_file)
            
            return True
            
        except Exception as e:
            print(f"Error importing environment: {e}")
            return False
    
    def _get_environment_template(self, environment_name: str) -> str:
        """Get template content for an environment."""
        
        templates = {
            'development': """# Development Environment Configuration
APP_ENV=development
APP_DEBUG=true
APP_URL=http://localhost:8000

# Database
DATABASE_URL=sqlite:///database/database.sqlite
DB_ECHO=true

# Cache
CACHE_DRIVER=file
CACHE_PREFIX=dev_

# Session
SESSION_DRIVER=file
SESSION_LIFETIME=120

# Logging
LOG_LEVEL=DEBUG
LOG_CHANNEL=single

# Development Tools
HOT_RELOAD=true
DEBUG_TOOLBAR=true
QUERY_LOGGING=true
""",
            
            'testing': """# Testing Environment Configuration
APP_ENV=testing
APP_DEBUG=true
APP_URL=http://localhost:8000

# Database
DATABASE_URL=sqlite:///:memory:
DB_ECHO=false

# Cache
CACHE_DRIVER=array
CACHE_PREFIX=test_

# Session
SESSION_DRIVER=array

# Logging
LOG_LEVEL=INFO
LOG_CHANNEL=single

# Testing
TESTING=true
MOCK_EXTERNAL_APIS=true
""",
            
            'staging': """# Staging Environment Configuration
APP_ENV=staging
APP_DEBUG=false
APP_URL={APP_URL}

# Database
DATABASE_URL={DATABASE_URL}
DB_POOL_SIZE=5

# Cache
CACHE_DRIVER=redis
REDIS_URL={REDIS_URL}
CACHE_PREFIX=stage_

# Session
SESSION_DRIVER=redis
SESSION_LIFETIME=120

# Logging
LOG_LEVEL=WARNING
LOG_CHANNEL=stack

# Monitoring
ERROR_TRACKING_DSN={ERROR_TRACKING_DSN}
PERFORMANCE_MONITORING=true
""",
            
            'production': """# Production Environment Configuration
APP_ENV=production
APP_DEBUG=false
APP_URL={APP_URL}

# Security
SECRET_KEY={SECRET_KEY}
API_KEY={API_KEY}

# Database
DATABASE_URL={DATABASE_URL}
DB_POOL_SIZE=10
DB_SSL_MODE=require

# Cache
CACHE_DRIVER=redis
REDIS_URL={REDIS_URL}
CACHE_PREFIX=prod_

# Session
SESSION_DRIVER=redis
SESSION_LIFETIME=240
SESSION_SECURE=true

# Logging
LOG_LEVEL=ERROR
LOG_CHANNEL=stack

# Monitoring
ERROR_TRACKING_DSN={ERROR_TRACKING_DSN}
PERFORMANCE_MONITORING=true
HEALTH_CHECK_ENABLED=true

# Security
RATE_LIMITING=true
SECURITY_HEADERS=true
CSRF_PROTECTION=true
"""
        }
        
        return templates.get(environment_name, templates['development'])
    
    def _create_directories(self, environment_name: str, config: Dict[str, Any]) -> None:
        """Create necessary directories for the environment."""
        
        default_dirs = [
            'logs',
            'storage',
            'storage/cache',
            'storage/sessions',
            'storage/uploads',
            'database',
            'database/migrations',
            'database/seeders'
        ]
        
        directories = config.get('directories', default_dirs)
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _install_dependencies(self, environment_name: str, config: Dict[str, Any]) -> None:
        """Install environment-specific dependencies."""
        
        dependency_files = {
            'development': 'requirements-dev.txt',
            'testing': 'requirements-test.txt',
            'production': 'requirements.txt'
        }
        
        requirements_file = dependency_files.get(environment_name, 'requirements.txt')
        
        if os.path.exists(requirements_file):
            try:
                subprocess.run(['pip', 'install', '-r', requirements_file], check=True)
                print(f"Installed dependencies from {requirements_file}")
            except subprocess.CalledProcessError as e:
                print(f"Error installing dependencies: {e}")
    
    def _run_command(self, command: str) -> bool:
        """Run a setup command."""
        try:
            subprocess.run(command.split(), check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running command '{command}': {e}")
            return False
    
    def _initialize_database(self, environment_name: str) -> None:
        """Initialize database for the environment."""
        try:
            # Run migrations
            subprocess.run(['python', '-m', 'larapy.console.cli', 'db:migrate'], check=True)
            print("Database initialized successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error initializing database: {e}")
    
    def _create_sample_data(self, environment_name: str) -> None:
        """Create sample data for the environment."""
        try:
            # Run seeders
            subprocess.run(['python', '-m', 'larapy.console.cli', 'db:seed'], check=True)
            print("Sample data created successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error creating sample data: {e}")


class EnvironmentManager:
    """High-level environment management interface."""
    
    def __init__(self):
        self.setup = EnvironmentSetup()
        self.detector = EnvironmentDetector()
        self.validator = EnvironmentValidator()
    
    def init(self, environment_name: str = 'development', 
             interactive: bool = True) -> bool:
        """
        Initialize a new environment.
        
        Args:
            environment_name: Name of the environment to initialize
            interactive: Whether to prompt for configuration values
            
        Returns:
            True if initialization was successful
        """
        print(f"Initializing {environment_name} environment...")
        
        template_vars = {}
        
        if interactive:
            template_vars = self._collect_configuration(environment_name)
        
        config = {
            'template_vars': template_vars,
            'install_dependencies': True,
            'initialize_database': environment_name != 'production'
        }
        
        return self.setup.setup_environment(environment_name, config)
    
    def status(self) -> Dict[str, Any]:
        """
        Get current environment status.
        
        Returns:
            Environment status information
        """
        current_env = self.detector.detect()
        validation = self.validator.get_validation_summary(current_env.name)
        available_envs = self.setup.list_environments()
        
        return {
            'current_environment': current_env.name,
            'environment_type': current_env.type.value,
            'is_valid': validation['is_valid'],
            'validation_errors': validation['errors'],
            'validation_warnings': validation['warnings'],
            'available_environments': available_envs,
            'debug_mode': current_env.is_debug,
            'features_enabled': sum(1 for enabled in current_env.features.values() if enabled)
        }
    
    def _collect_configuration(self, environment_name: str) -> Dict[str, str]:
        """Collect configuration values interactively."""
        config = {}
        
        if environment_name == 'production':
            config['APP_URL'] = input("Application URL: ")
            config['DATABASE_URL'] = input("Database URL: ")
            config['REDIS_URL'] = input("Redis URL: ")
            config['SECRET_KEY'] = input("Secret Key (32+ characters): ")
            config['API_KEY'] = input("API Key: ")
            config['ERROR_TRACKING_DSN'] = input("Error Tracking DSN (optional): ")
        elif environment_name == 'staging':
            config['APP_URL'] = input("Application URL: ")
            config['DATABASE_URL'] = input("Database URL: ")
            config['REDIS_URL'] = input("Redis URL: ")
            config['ERROR_TRACKING_DSN'] = input("Error Tracking DSN (optional): ")
        
        return config