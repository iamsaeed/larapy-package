"""
View composers and creators for Larapy.

Provides mechanisms to bind data to views when they are rendered.
"""

from typing import Dict, Any, Callable, List, Union
from .view import View


class ViewComposer:
    """Composes data for views before rendering."""
    
    def __init__(self, callback: Callable):
        """
        Initialize view composer.
        
        Args:
            callback: Function to call when composing view
        """
        self.callback = callback
    
    def compose(self, view: View):
        """
        Compose the view with additional data.
        
        Args:
            view: View instance to compose
        """
        self.callback(view)


class ViewCreator:
    """Creates views with predefined data and logic."""
    
    def __init__(self, callback: Callable):
        """
        Initialize view creator.
        
        Args:
            callback: Function to call when creating view
        """
        self.callback = callback
    
    def create(self, view: View):
        """
        Create/modify the view.
        
        Args:
            view: View instance to create/modify
        """
        self.callback(view)


class ComposerManager:
    """Manages view composers and creators."""
    
    def __init__(self):
        self.composers: Dict[str, List[ViewComposer]] = {}
        self.creators: Dict[str, List[ViewCreator]] = {}
    
    def composer(self, views: Union[str, List[str]], callback: Callable):
        """
        Register a view composer.
        
        Args:
            views: View names or patterns
            callback: Composer callback function
        """
        if isinstance(views, str):
            views = [views]
        
        composer = ViewComposer(callback)
        
        for view in views:
            if view not in self.composers:
                self.composers[view] = []
            self.composers[view].append(composer)
    
    def creator(self, views: Union[str, List[str]], callback: Callable):
        """
        Register a view creator.
        
        Args:
            views: View names or patterns
            callback: Creator callback function
        """
        if isinstance(views, str):
            views = [views]
        
        creator = ViewCreator(callback)
        
        for view in views:
            if view not in self.creators:
                self.creators[view] = []
            self.creators[view].append(creator)
    
    def compose(self, view_name: str, view: View):
        """
        Run composers for a view.
        
        Args:
            view_name: Name of the view
            view: View instance
        """
        # Run exact match composers
        if view_name in self.composers:
            for composer in self.composers[view_name]:
                composer.compose(view)
        
        # Run pattern match composers
        for pattern, composers in self.composers.items():
            if self._matches_pattern(view_name, pattern) and pattern != view_name:
                for composer in composers:
                    composer.compose(view)
    
    def create(self, view_name: str, view: View):
        """
        Run creators for a view.
        
        Args:
            view_name: Name of the view
            view: View instance
        """
        # Run exact match creators
        if view_name in self.creators:
            for creator in self.creators[view_name]:
                creator.create(view)
        
        # Run pattern match creators
        for pattern, creators in self.creators.items():
            if self._matches_pattern(view_name, pattern) and pattern != view_name:
                for creator in creators:
                    creator.create(view)
    
    def _matches_pattern(self, view_name: str, pattern: str) -> bool:
        """
        Check if view name matches pattern.
        
        Args:
            view_name: View name to check
            pattern: Pattern to match against
            
        Returns:
            True if matches, False otherwise
        """
        if '*' not in pattern:
            return view_name == pattern
        
        # Handle wildcard patterns
        if pattern.endswith('*'):
            # Prefix match
            prefix = pattern[:-1]
            return view_name.startswith(prefix)
        elif pattern.startswith('*'):
            # Suffix match
            suffix = pattern[1:]
            return view_name.endswith(suffix)
        elif '*' in pattern:
            # Contains match
            parts = pattern.split('*', 1)
            start, end = parts
            return view_name.startswith(start) and view_name.endswith(end)
        
        return False


# Global composer manager
composer_manager = ComposerManager()


def composer(views: Union[str, List[str]], callback: Callable):
    """
    Register a global view composer.
    
    Args:
        views: View names or patterns
        callback: Composer callback
    """
    composer_manager.composer(views, callback)


def creator(views: Union[str, List[str]], callback: Callable):
    """
    Register a global view creator.
    
    Args:
        views: View names or patterns  
        callback: Creator callback
    """
    composer_manager.creator(views, callback)


# Common composer utilities
class DataComposer:
    """Utility for composing common data to views."""
    
    @staticmethod
    def current_user(view: View):
        """Add current user to view data."""
        # This would integrate with authentication system
        view.with_data('user', None)  # Placeholder
    
    @staticmethod
    def app_config(view: View):
        """Add application config to view data."""
        view.with_data({
            'app_name': 'Larapy Application',
            'app_version': '1.0.0',
            'app_env': 'development'
        })
    
    @staticmethod
    def csrf_token(view: View):
        """Add CSRF token to view data."""
        # This would integrate with CSRF protection
        view.with_data('csrf_token', 'csrf_token_placeholder')


class NavigationComposer:
    """Composer for navigation-related data."""
    
    @staticmethod
    def breadcrumbs(view: View):
        """Add breadcrumbs to view."""
        # This would integrate with routing system
        view.with_data('breadcrumbs', [
            {'title': 'Home', 'url': '/'},
            {'title': 'Dashboard', 'url': '/dashboard'}
        ])
    
    @staticmethod
    def menu_items(view: View):
        """Add menu items to view."""
        view.with_data('menu_items', [
            {'title': 'Dashboard', 'url': '/', 'icon': 'dashboard'},
            {'title': 'Users', 'url': '/users', 'icon': 'users'},
            {'title': 'Settings', 'url': '/settings', 'icon': 'settings'}
        ])


class FormComposer:
    """Composer for form-related data."""
    
    @staticmethod
    def validation_errors(view: View):
        """Add validation errors to view."""
        # This would integrate with validation system
        view.with_data('errors', {})
    
    @staticmethod
    def old_input(view: View):
        """Add old input values for form repopulation."""
        # This would integrate with session/request handling
        view.with_data('old', {})


# Example composer registration
def setup_default_composers():
    """Set up default view composers."""
    # Global composers for all views
    composer('*', DataComposer.csrf_token)
    composer('*', DataComposer.app_config)
    
    # Auth-related views
    composer(['auth.*', 'profile.*'], DataComposer.current_user)
    
    # Layout views
    composer(['layouts.*', 'dashboard.*'], NavigationComposer.breadcrumbs)
    composer(['layouts.*'], NavigationComposer.menu_items)
    
    # Form views
    composer(['forms.*', '*.form'], FormComposer.validation_errors)
    composer(['forms.*', '*.form'], FormComposer.old_input)