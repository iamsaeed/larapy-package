"""
Application class - the central hub for the Larapy framework.

The Application class serves as the IoC container for the framework and provides
the central entry point for configuring and running a Larapy application.
"""

import os
from typing import List, Dict, Any, Optional, Type
from pathlib import Path

from .container import Container
from .service_provider import ServiceProvider


class Application(Container):
    """
    The Larapy Application class.
    
    This class serves as the IoC container for the framework and handles
    service provider registration, configuration management, and application
    lifecycle.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the application.
        
        Args:
            base_path: The base path for the application
        """
        super().__init__()
        
        # Set up application paths
        self._base_path = Path(base_path or os.getcwd()).resolve()
        
        # Application state
        self._booted = False
        self._service_providers: List[ServiceProvider] = []
        self._loaded_providers: Dict[str, ServiceProvider] = {}
        self._deferred_services: Dict[str, str] = {}
        
        # Configuration
        self._config: Dict[str, Any] = {}
        self._environment = os.getenv('APP_ENV', 'production')
        
        # Register core bindings
        self._register_base_bindings()
        
        # Register core service providers
        self._register_core_providers()
    
    def _register_base_bindings(self) -> None:
        """Register the basic bindings in the container."""
        # Bind the application instance
        self.instance('app', self)
        self.alias('app', Application.__name__)
        
        # Bind common paths
        self.instance('path.base', str(self._base_path))
        self.instance('path.config', str(self._base_path / 'config'))
        self.instance('path.storage', str(self._base_path / 'storage'))
        self.instance('path.public', str(self._base_path / 'public'))
    
    def _register_core_providers(self) -> None:
        """Register core service providers."""
        # Core providers would be registered here
        # For now, we'll keep it simple
        pass
    
    @property 
    def base_path(self) -> str:
        """Get the base path of the application."""
        return str(self._base_path)
    
    @property
    def config_path(self) -> str:
        """Get the configuration path."""
        return str(self._base_path / 'config')
    
    @property
    def storage_path(self) -> str:
        """Get the storage path."""
        return str(self._base_path / 'storage')
    
    @property
    def public_path(self) -> str:
        """Get the public path.""" 
        return str(self._base_path / 'public')
    
    @property
    def environment(self) -> str:
        """Get the application environment."""
        return self._environment
    
    def is_local(self) -> bool:
        """Check if the application is in local environment."""
        return self._environment == 'local'
    
    def is_production(self) -> bool:
        """Check if the application is in production environment."""
        return self._environment == 'production'
    
    def register(self, provider: Type[ServiceProvider] or ServiceProvider) -> ServiceProvider:
        """
        Register a service provider.
        
        Args:
            provider: The service provider class or instance
            
        Returns:
            The registered service provider instance
        """
        # Create instance if class was passed
        if isinstance(provider, type):
            provider = provider(self)
        
        # Check if already registered
        provider_name = provider.__class__.__name__
        if provider_name in self._loaded_providers:
            return self._loaded_providers[provider_name]
        
        # Register the provider
        self._loaded_providers[provider_name] = provider
        
        # If deferred, register its services
        if hasattr(provider, 'defer') and provider.defer:
            for service in provider.provides():
                self._deferred_services[service] = provider_name
        else:
            # Register immediately
            provider.register()
            self._service_providers.append(provider)
        
        # Boot if application is already booted
        if self._booted and not provider.defer:
            provider.boot()
        
        return provider
    
    def boot(self) -> None:
        """
        Boot the application's service providers.
        """
        if self._booted:
            return
        
        # Boot all registered providers
        for provider in self._service_providers:
            provider.boot()
        
        self._booted = True
    
    def booted(self, callback: callable) -> None:
        """
        Register a callback to be called after the application is booted.
        
        Args:
            callback: The callback to register
        """
        if self._booted:
            callback(self)
        else:
            # For now, just call immediately after boot
            # In a full implementation, we'd store callbacks
            pass
    
    def make(self, abstract: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Resolve the given type from the container.
        
        Args:
            abstract: The abstract type or name to resolve
            parameters: Additional parameters for resolution
            
        Returns:
            The resolved instance
        """
        # Check if it's a deferred service
        if abstract in self._deferred_services:
            provider_name = self._deferred_services[abstract]
            provider = self._loaded_providers[provider_name]
            
            # Register and boot the deferred provider
            provider.register()
            self._service_providers.append(provider)
            
            if self._booted:
                provider.boot()
            
            # Remove from deferred services
            del self._deferred_services[abstract]
        
        return super().make(abstract, parameters)
    
    def configure_monolog(self, callback: callable) -> None:
        """
        Configure Monolog (placeholder for logging configuration).
        
        Args:
            callback: The configuration callback
        """
        # Placeholder for logging configuration
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key (supports dot notation)
            default: The default value if key is not found
            
        Returns:
            The configuration value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_config(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key (supports dot notation)
            value: The value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the final value
        config[keys[-1]] = value
    
    def load_config(self, config_path: Optional[str] = None) -> None:
        """
        Load configuration from files.
        
        Args:
            config_path: Path to configuration directory
        """
        if config_path is None:
            config_path = self.config_path
        
        config_dir = Path(config_path)
        if not config_dir.exists():
            return
        
        # Load .py configuration files
        for config_file in config_dir.glob('*.py'):
            if config_file.name.startswith('__'):
                continue
            
            # Import the config module
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                config_file.stem, config_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Extract configuration variables
                config_vars = {
                    key: value for key, value in vars(module).items()
                    if not key.startswith('_')
                }
                
                self._config[config_file.stem] = config_vars
    
    def load_environment_variables(self, env_file: str = '.env') -> None:
        """
        Load environment variables from .env file.
        
        Args:
            env_file: Path to the .env file
        """
        env_path = self._base_path / env_file
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)
    
    def run(self, host: str = '127.0.0.1', port: int = 8000, **kwargs) -> None:
        """
        Run the application (development server).
        
        Args:
            host: The host to bind to
            port: The port to bind to
            **kwargs: Additional arguments for Flask development server
        """
        # Boot the application
        self.boot()
        
        # Create Flask app if not already done
        if not hasattr(self, '_flask_app'):
            self._flask_app = self._create_flask_app()
        
        # Run Flask development server
        debug = kwargs.get('debug', self.is_local())
        use_reloader = kwargs.get('reload', self.is_local())
        
        print(f"Larapy application starting on {host}:{port}")
        print(f"Environment: {self.environment}")
        print(f"Debug mode: {'enabled' if debug else 'disabled'}")
        
        self._flask_app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=use_reloader,
            **kwargs
        )
    
    def _create_flask_app(self):
        """
        Create and configure a Flask application instance.
        
        Returns:
            Flask application instance
        """
        try:
            from flask import Flask, render_template
            
            # Create Flask app
            flask_app = Flask(
                __name__,
                template_folder=str(self._base_path / 'resources' / 'views'),
                static_folder=str(self._base_path / 'public')
            )
            
            # Configure Flask app
            flask_app.config.update({
                'SECRET_KEY': self.get_config('app.APP_KEY', 'larapy-default-key'),
                'DEBUG': self.is_local()
            })
            
            # Set up basic routes (placeholder)
            @flask_app.route('/')
            def home():
                try:
                    return render_template('home.html', 
                        title='Welcome to Larapy',
                        message="Laravel's elegant syntax meets Python's simplicity"
                    )
                except:
                    return """
                    <h1>Welcome to Larapy!</h1>
                    <p>Laravel's elegant syntax meets Python's simplicity</p>
                    <p>Your Larapy application is running successfully.</p>
                    """
            
            @flask_app.route('/health')
            def health():
                return {'status': 'healthy', 'version': self.version()}
            
            return flask_app
            
        except ImportError:
            raise RuntimeError("Flask not installed. Install with: pip install flask")
        
    def get_flask_app(self):
        """
        Get the Flask application instance.
        
        Returns:
            Flask application instance
        """
        if not hasattr(self, '_flask_app'):
            self._flask_app = self._create_flask_app()
        return self._flask_app
    
    def version(self) -> str:
        """
        Get the version number of the application.
        
        Returns:
            The application version
        """
        return "0.1.0"
    
    def is_down_for_maintenance(self) -> bool:
        """
        Determine if the application is currently down for maintenance.
        
        Returns:
            True if in maintenance mode, False otherwise
        """
        # Placeholder - would check for maintenance file
        return False
    
    def terminate(self) -> None:
        """
        Terminate the application.
        """
        # Placeholder for cleanup operations
        pass