"""
View service provider for Larapy.

Registers view system components and sets up default configuration.
"""

import os
from pathlib import Path
from typing import Dict, Any
from ..providers.service_provider import ServiceProvider
from .view import ViewManager, view_manager
from .engines import Jinja2Engine, SimpleEngine
from .composer import setup_default_composers


class ViewServiceProvider(ServiceProvider):
    """Service provider for the view system."""
    
    def register(self):
        """Register view services."""
        # Register the view manager as singleton
        self.app.singleton('view', lambda app: view_manager)
        
        # Register template engines
        self._register_engines()
        
        # Set up view paths
        self._setup_view_paths()
        
        # Register view helpers
        self._register_helpers()
    
    def boot(self):
        """Boot the view system."""
        # Set up default composers
        setup_default_composers()
        
        # Configure template engines
        self._configure_engines()
        
        # Share global view data
        self._share_global_data()
    
    def _register_engines(self):
        """Register template engines."""
        # Register Jinja2 engine as default
        jinja_options = self.app.config.get('view.jinja2', {})
        jinja_engine = Jinja2Engine(**jinja_options)
        view_manager.add_engine('jinja2', jinja_engine)
        
        # Register simple engine as fallback
        simple_engine = SimpleEngine()
        view_manager.add_engine('simple', simple_engine)
        
        # Set default engine
        default_engine = self.app.config.get('view.default_engine', 'jinja2')
        view_manager.default_engine = default_engine
    
    def _setup_view_paths(self):
        """Set up view template paths."""
        # Get base paths from config
        view_paths = self.app.config.get('view.paths', [])
        
        # Add default paths if none configured
        if not view_paths:
            app_path = getattr(self.app, 'base_path', os.getcwd())
            view_paths = [
                os.path.join(app_path, 'resources', 'views'),
                os.path.join(app_path, 'templates'),
                os.path.join(app_path, 'views')
            ]
        
        # Add paths to view manager
        for path in view_paths:
            view_manager.add_path(Path(path))
    
    def _configure_engines(self):
        """Configure template engines with app-specific settings."""
        # Configure Jinja2 with app context
        if 'jinja2' in view_manager.engines:
            jinja_env = view_manager.engines['jinja2']._get_env()
            
            # Add app-specific globals
            jinja_env.globals.update({
                'app': self.app,
                'config': lambda key, default=None: self.app.config.get(key, default),
                'env': lambda key, default=None: os.environ.get(key, default)
            })
    
    def _register_helpers(self):
        """Register view helper functions."""
        from .helpers import ViewHelpers, FormHelpers, AssetHelpers
        
        # Register as singletons
        self.app.singleton('view.helpers', lambda app: ViewHelpers)
        self.app.singleton('form.helpers', lambda app: FormHelpers) 
        self.app.singleton('asset.helpers', lambda app: AssetHelpers)
    
    def _share_global_data(self):
        """Share global data across all views."""
        # Share application info
        view_manager.share({
            'app_name': self.app.config.get('app.name', 'Larapy Application'),
            'app_env': self.app.config.get('app.env', 'production'),
            'app_debug': self.app.config.get('app.debug', False),
            'app_version': self.app.config.get('app.version', '1.0.0')
        })
        
        # Share current year for copyright notices
        from datetime import datetime
        view_manager.share('current_year', datetime.now().year)


def create_view_config() -> Dict[str, Any]:
    """Create default view configuration."""
    return {
        'view': {
            'default_engine': 'jinja2',
            'paths': [],  # Will use default paths if empty
            'jinja2': {
                'autoescape': True,
                'auto_reload': True,
                'cache_size': 400,
                'trim_blocks': True,
                'lstrip_blocks': True
            }
        }
    }