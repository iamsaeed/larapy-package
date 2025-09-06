"""
Environment Manager

This module provides the main interface for environment management.
"""

from typing import Dict, List, Any, Optional
from .detector import EnvironmentDetector, EnvironmentInfo
from .providers import EnvironmentServiceProvider
from .feature_flags import FeatureFlags
from .validator import EnvironmentValidator
from .setup import EnvironmentSetup, EnvironmentManager as SetupManager


class EnvironmentManager:
    """Main environment management interface."""
    
    def __init__(self, app=None):
        self.app = app
        self.detector = EnvironmentDetector()
        self.validator = EnvironmentValidator()
        self.feature_flags = FeatureFlags(self.detector)
        self.setup_manager = SetupManager()
        self.current_environment: Optional[EnvironmentInfo] = None
        
        # Detect current environment
        self._detect_environment()
    
    def get_current_environment(self) -> EnvironmentInfo:
        """
        Get current environment information.
        
        Returns:
            EnvironmentInfo object
        """
        if self.current_environment is None:
            self._detect_environment()
        return self.current_environment
    
    def is_environment(self, environment_name: str) -> bool:
        """
        Check if current environment matches the given name.
        
        Args:
            environment_name: Environment name to check
            
        Returns:
            True if current environment matches
        """
        current_env = self.get_current_environment()
        return current_env.name.lower() == environment_name.lower()
    
    def is_development(self) -> bool:
        """Check if current environment is development."""
        return self.is_environment('development') or self.is_environment('local')
    
    def is_testing(self) -> bool:
        """Check if current environment is testing."""
        return self.is_environment('testing') or self.is_environment('test')
    
    def is_staging(self) -> bool:
        """Check if current environment is staging."""
        return self.is_environment('staging') or self.is_environment('stage')
    
    def is_production(self) -> bool:
        """Check if current environment is production."""
        return self.is_environment('production') or self.is_environment('prod')
    
    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        current_env = self.get_current_environment()
        return current_env.is_debug
    
    def get_feature_flags(self) -> FeatureFlags:
        """
        Get feature flags manager.
        
        Returns:
            FeatureFlags instance
        """
        return self.feature_flags
    
    def is_feature_enabled(self, feature_name: str, user_context: Dict[str, Any] = None) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            feature_name: Name of the feature flag
            user_context: Optional user context
            
        Returns:
            True if feature is enabled
        """
        return self.feature_flags.is_enabled(feature_name, user_context)
    
    def validate_environment(self) -> Dict[str, Any]:
        """
        Validate current environment configuration.
        
        Returns:
            Validation summary
        """
        current_env = self.get_current_environment()
        return self.validator.get_validation_summary(current_env.name)
    
    def get_environment_config(self) -> Dict[str, Any]:
        """
        Get current environment configuration.
        
        Returns:
            Environment configuration dictionary
        """
        current_env = self.get_current_environment()
        return self.detector.get_environment_config(current_env.name)
    
    def register_environment_provider(self, app) -> None:
        """
        Register environment-specific service provider.
        
        Args:
            app: Application instance
        """
        env_provider = EnvironmentServiceProvider(app)
        app.register(env_provider)
    
    def setup_environment(self, environment_name: str, config: Dict[str, Any] = None) -> bool:
        """
        Set up an environment.
        
        Args:
            environment_name: Environment name
            config: Setup configuration
            
        Returns:
            True if setup was successful
        """
        return self.setup_manager.setup.setup_environment(environment_name, config)
    
    def switch_environment(self, environment_name: str) -> bool:
        """
        Switch to a different environment.
        
        Args:
            environment_name: Target environment name
            
        Returns:
            True if switch was successful
        """
        success = self.setup_manager.setup.switch_environment(environment_name)
        if success:
            self._detect_environment()  # Re-detect after switch
        return success
    
    def list_environments(self) -> List[str]:
        """
        List available environments.
        
        Returns:
            List of environment names
        """
        return self.setup_manager.setup.list_environments()
    
    def get_environment_info(self, environment_name: str = None) -> Dict[str, Any]:
        """
        Get detailed information about an environment.
        
        Args:
            environment_name: Environment name (current if not provided)
            
        Returns:
            Environment information dictionary
        """
        if environment_name is None:
            return self._get_current_environment_info()
        else:
            return self.setup_manager.setup.get_environment_info(environment_name)
    
    def export_environment(self, environment_name: str, export_path: str, 
                          include_secrets: bool = False) -> bool:
        """
        Export environment configuration.
        
        Args:
            environment_name: Environment to export
            export_path: Export file path
            include_secrets: Whether to include sensitive values
            
        Returns:
            True if export was successful
        """
        return self.setup_manager.setup.export_environment(
            environment_name, export_path, include_secrets
        )
    
    def import_environment(self, environment_name: str, import_path: str) -> bool:
        """
        Import environment configuration.
        
        Args:
            environment_name: Target environment name
            import_path: Import file path
            
        Returns:
            True if import was successful
        """
        return self.setup_manager.setup.import_environment(environment_name, import_path)
    
    def add_feature_flag(self, flag_name: str, enabled: bool = True, 
                        environments: List[str] = None) -> None:
        """
        Add or update a feature flag.
        
        Args:
            flag_name: Feature flag name
            enabled: Whether the flag is enabled
            environments: Environments where flag applies
        """
        if enabled:
            self.feature_flags.enable(flag_name, environments)
        else:
            self.feature_flags.disable(flag_name)
    
    def get_environment_status(self) -> Dict[str, Any]:
        """
        Get comprehensive environment status.
        
        Returns:
            Status dictionary with all environment information
        """
        current_env = self.get_current_environment()
        validation = self.validate_environment()
        available_envs = self.list_environments()
        enabled_features = self.feature_flags.get_enabled_flags()
        
        return {
            'environment': {
                'name': current_env.name,
                'type': current_env.type.value,
                'is_debug': current_env.is_debug,
                'is_testing': current_env.is_testing,
                'is_production': current_env.is_production,
                'hostname': current_env.hostname,
                'platform': current_env.platform,
                'python_version': current_env.python_version,
                'working_directory': current_env.working_directory
            },
            'validation': validation,
            'features': {
                'enabled_count': len(enabled_features),
                'enabled_flags': enabled_features,
                'available_features': list(current_env.features.keys())
            },
            'available_environments': available_envs,
            'metadata': current_env.metadata
        }
    
    def _detect_environment(self) -> None:
        """Detect and cache current environment."""
        self.current_environment = self.detector.detect()
    
    def _get_current_environment_info(self) -> Dict[str, Any]:
        """Get current environment information."""
        env = self.get_current_environment()
        validation = self.validate_environment()
        
        return {
            'name': env.name,
            'type': env.type.value,
            'is_debug': env.is_debug,
            'is_testing': env.is_testing,
            'is_production': env.is_production,
            'hostname': env.hostname,
            'platform': env.platform,
            'python_version': env.python_version,
            'working_directory': env.working_directory,
            'config_path': env.config_path,
            'features': env.features,
            'metadata': env.metadata,
            'validation': validation
        }


# Global environment manager instance
_environment_manager: Optional[EnvironmentManager] = None


def get_environment_manager(app=None) -> EnvironmentManager:
    """
    Get the global environment manager instance.
    
    Args:
        app: Application instance (for initialization)
        
    Returns:
        EnvironmentManager instance
    """
    global _environment_manager
    
    if _environment_manager is None:
        _environment_manager = EnvironmentManager(app)
    
    return _environment_manager


# Convenience functions
def current_environment() -> str:
    """Get current environment name."""
    manager = get_environment_manager()
    return manager.get_current_environment().name


def is_development() -> bool:
    """Check if current environment is development."""
    manager = get_environment_manager()
    return manager.is_development()


def is_testing() -> bool:
    """Check if current environment is testing."""
    manager = get_environment_manager()
    return manager.is_testing()


def is_staging() -> bool:
    """Check if current environment is staging."""
    manager = get_environment_manager()
    return manager.is_staging()


def is_production() -> bool:
    """Check if current environment is production."""
    manager = get_environment_manager()
    return manager.is_production()


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    manager = get_environment_manager()
    return manager.is_debug_enabled()


def feature_enabled(feature_name: str, user_context: Dict[str, Any] = None) -> bool:
    """Check if a feature is enabled."""
    manager = get_environment_manager()
    return manager.is_feature_enabled(feature_name, user_context)