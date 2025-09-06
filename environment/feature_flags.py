"""
Environment-Based Feature Flags

This module provides feature flag management based on environment configuration.
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from .detector import EnvironmentDetector


class FeatureState(Enum):
    """Feature flag states."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    CONDITIONAL = "conditional"


@dataclass
class FeatureFlag:
    """Represents a feature flag with its configuration."""
    name: str
    state: FeatureState
    environments: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    rollout_percentage: Optional[float] = None
    user_segments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


class FeatureFlags:
    """Environment-based feature flag management."""
    
    def __init__(self, environment_detector: EnvironmentDetector = None):
        self.environment_detector = environment_detector or EnvironmentDetector()
        self.environment = self.environment_detector.detect()
        self.flags: Dict[str, FeatureFlag] = {}
        self.conditions: Dict[str, Callable] = {}
        self.user_context: Dict[str, Any] = {}
        
        # Load default flags
        self._load_default_flags()
        
        # Load environment-specific flags
        self._load_environment_flags()
    
    def is_enabled(self, flag_name: str, user_context: Dict[str, Any] = None) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag
            user_context: Optional user context for conditional evaluation
            
        Returns:
            True if flag is enabled
        """
        if flag_name not in self.flags:
            return False
        
        flag = self.flags[flag_name]
        
        # Check environment-specific enabling
        if flag.environments and self.environment.name not in flag.environments:
            return False
        
        # Check basic state
        if flag.state == FeatureState.DISABLED:
            return False
        elif flag.state == FeatureState.ENABLED:
            return True
        
        # Handle conditional flags
        if flag.state == FeatureState.CONDITIONAL:
            return self._evaluate_conditions(flag, user_context)
        
        return False
    
    def enable(self, flag_name: str, environments: List[str] = None) -> None:
        """
        Enable a feature flag.
        
        Args:
            flag_name: Name of the feature flag
            environments: Specific environments to enable in (optional)
        """
        if flag_name not in self.flags:
            self.flags[flag_name] = FeatureFlag(
                name=flag_name,
                state=FeatureState.ENABLED,
                environments=environments or []
            )
        else:
            self.flags[flag_name].state = FeatureState.ENABLED
            if environments:
                self.flags[flag_name].environments = environments
    
    def disable(self, flag_name: str) -> None:
        """
        Disable a feature flag.
        
        Args:
            flag_name: Name of the feature flag
        """
        if flag_name not in self.flags:
            self.flags[flag_name] = FeatureFlag(
                name=flag_name,
                state=FeatureState.DISABLED
            )
        else:
            self.flags[flag_name].state = FeatureState.DISABLED
    
    def add_flag(self, flag: FeatureFlag) -> None:
        """
        Add a feature flag.
        
        Args:
            flag: FeatureFlag instance
        """
        self.flags[flag.name] = flag
    
    def add_condition(self, name: str, condition: Callable) -> None:
        """
        Add a custom condition evaluator.
        
        Args:
            name: Condition name
            condition: Callable that takes user_context and returns bool
        """
        self.conditions[name] = condition
    
    def set_user_context(self, context: Dict[str, Any]) -> None:
        """
        Set global user context for flag evaluation.
        
        Args:
            context: User context dictionary
        """
        self.user_context = context
    
    def get_enabled_flags(self, user_context: Dict[str, Any] = None) -> List[str]:
        """
        Get list of enabled flag names.
        
        Args:
            user_context: Optional user context
            
        Returns:
            List of enabled flag names
        """
        enabled = []
        for flag_name in self.flags:
            if self.is_enabled(flag_name, user_context):
                enabled.append(flag_name)
        return enabled
    
    def get_flag_info(self, flag_name: str) -> Optional[FeatureFlag]:
        """
        Get information about a feature flag.
        
        Args:
            flag_name: Name of the feature flag
            
        Returns:
            FeatureFlag instance or None
        """
        return self.flags.get(flag_name)
    
    def load_flags_from_config(self, config_path: str) -> None:
        """
        Load feature flags from a configuration file.
        
        Args:
            config_path: Path to configuration file (JSON)
        """
        config_file = Path(config_path)
        if not config_file.exists():
            return
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            for flag_name, flag_config in config.get('flags', {}).items():
                flag = FeatureFlag(
                    name=flag_name,
                    state=FeatureState(flag_config.get('state', 'disabled')),
                    environments=flag_config.get('environments', []),
                    conditions=flag_config.get('conditions', {}),
                    rollout_percentage=flag_config.get('rollout_percentage'),
                    user_segments=flag_config.get('user_segments', []),
                    metadata=flag_config.get('metadata', {}),
                    description=flag_config.get('description', '')
                )
                self.flags[flag_name] = flag
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error loading feature flags from {config_path}: {e}")
    
    def save_flags_to_config(self, config_path: str) -> None:
        """
        Save feature flags to a configuration file.
        
        Args:
            config_path: Path to save configuration file
        """
        config = {
            'flags': {}
        }
        
        for flag_name, flag in self.flags.items():
            config['flags'][flag_name] = {
                'state': flag.state.value,
                'environments': flag.environments,
                'conditions': flag.conditions,
                'rollout_percentage': flag.rollout_percentage,
                'user_segments': flag.user_segments,
                'metadata': flag.metadata,
                'description': flag.description
            }
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving feature flags to {config_path}: {e}")
    
    def _evaluate_conditions(self, flag: FeatureFlag, user_context: Dict[str, Any] = None) -> bool:
        """Evaluate conditional flag requirements."""
        context = user_context or self.user_context
        
        # Check rollout percentage
        if flag.rollout_percentage is not None:
            user_id = context.get('user_id', 0)
            # Simple hash-based rollout
            rollout_hash = hash(f"{flag.name}:{user_id}") % 100
            if rollout_hash >= flag.rollout_percentage:
                return False
        
        # Check user segments
        if flag.user_segments:
            user_segment = context.get('segment')
            if user_segment not in flag.user_segments:
                return False
        
        # Check custom conditions
        for condition_name, condition_config in flag.conditions.items():
            if condition_name in self.conditions:
                condition_func = self.conditions[condition_name]
                if not condition_func(context, condition_config):
                    return False
            else:
                # Built-in condition evaluation
                if not self._evaluate_builtin_condition(condition_name, condition_config, context):
                    return False
        
        return True
    
    def _evaluate_builtin_condition(self, condition_name: str, condition_config: Any, 
                                  context: Dict[str, Any]) -> bool:
        """Evaluate built-in conditions."""
        if condition_name == 'user_role':
            user_role = context.get('role')
            return user_role in condition_config if isinstance(condition_config, list) else user_role == condition_config
        
        elif condition_name == 'user_id':
            user_id = context.get('user_id')
            if isinstance(condition_config, list):
                return user_id in condition_config
            elif isinstance(condition_config, dict):
                min_id = condition_config.get('min')
                max_id = condition_config.get('max')
                if min_id is not None and user_id < min_id:
                    return False
                if max_id is not None and user_id > max_id:
                    return False
                return True
            else:
                return user_id == condition_config
        
        elif condition_name == 'time_window':
            import datetime
            now = datetime.datetime.now()
            start_time = datetime.datetime.fromisoformat(condition_config.get('start'))
            end_time = datetime.datetime.fromisoformat(condition_config.get('end'))
            return start_time <= now <= end_time
        
        elif condition_name == 'environment_var':
            var_name = condition_config.get('name')
            expected_value = condition_config.get('value')
            actual_value = os.getenv(var_name)
            return actual_value == expected_value
        
        elif condition_name == 'request_header':
            # This would need request context
            header_name = condition_config.get('name')
            expected_value = condition_config.get('value')
            headers = context.get('headers', {})
            return headers.get(header_name) == expected_value
        
        return False
    
    def _load_default_flags(self) -> None:
        """Load default feature flags based on environment."""
        
        # Development environment flags
        if self.environment.name in ['development', 'local']:
            self.flags.update({
                'debug_toolbar': FeatureFlag(
                    name='debug_toolbar',
                    state=FeatureState.ENABLED,
                    environments=['development', 'local'],
                    description='Debug toolbar for development'
                ),
                'hot_reload': FeatureFlag(
                    name='hot_reload',
                    state=FeatureState.ENABLED,
                    environments=['development', 'local'],
                    description='Hot reload for development'
                ),
                'detailed_errors': FeatureFlag(
                    name='detailed_errors',
                    state=FeatureState.ENABLED,
                    environments=['development', 'local'],
                    description='Show detailed error messages'
                ),
                'query_logging': FeatureFlag(
                    name='query_logging',
                    state=FeatureState.ENABLED,
                    environments=['development', 'local'],
                    description='Log database queries'
                )
            })
        
        # Testing environment flags
        elif self.environment.name in ['testing', 'test']:
            self.flags.update({
                'database_transactions': FeatureFlag(
                    name='database_transactions',
                    state=FeatureState.ENABLED,
                    environments=['testing', 'test'],
                    description='Use database transactions in tests'
                ),
                'mock_external_apis': FeatureFlag(
                    name='mock_external_apis',
                    state=FeatureState.ENABLED,
                    environments=['testing', 'test'],
                    description='Mock external API calls'
                )
            })
        
        # Production environment flags
        elif self.environment.name in ['production', 'prod']:
            self.flags.update({
                'performance_monitoring': FeatureFlag(
                    name='performance_monitoring',
                    state=FeatureState.ENABLED,
                    environments=['production', 'staging'],
                    description='Performance monitoring'
                ),
                'error_tracking': FeatureFlag(
                    name='error_tracking',
                    state=FeatureState.ENABLED,
                    environments=['production', 'staging'],
                    description='Error tracking service'
                ),
                'security_headers': FeatureFlag(
                    name='security_headers',
                    state=FeatureState.ENABLED,
                    environments=['production', 'staging'],
                    description='Security headers middleware'
                )
            })
        
        # Universal flags with conditional logic
        self.flags.update({
            'maintenance_mode': FeatureFlag(
                name='maintenance_mode',
                state=FeatureState.CONDITIONAL,
                conditions={'environment_var': {'name': 'MAINTENANCE_MODE', 'value': 'true'}},
                description='Maintenance mode'
            ),
            'new_feature_rollout': FeatureFlag(
                name='new_feature_rollout',
                state=FeatureState.CONDITIONAL,
                rollout_percentage=10.0,  # 10% rollout
                description='New feature gradual rollout'
            ),
            'admin_features': FeatureFlag(
                name='admin_features',
                state=FeatureState.CONDITIONAL,
                conditions={'user_role': ['admin', 'super_admin']},
                description='Admin-only features'
            )
        })
    
    def _load_environment_flags(self) -> None:
        """Load environment-specific feature flags from configuration files."""
        # Try to load from environment-specific config file
        env_config_file = f"config/features/{self.environment.name}.json"
        if Path(env_config_file).exists():
            self.load_flags_from_config(env_config_file)
        
        # Try to load from general features config
        general_config_file = "config/features.json"
        if Path(general_config_file).exists():
            self.load_flags_from_config(general_config_file)


# Convenience functions
def is_feature_enabled(flag_name: str, user_context: Dict[str, Any] = None) -> bool:
    """
    Global function to check if a feature flag is enabled.
    
    Args:
        flag_name: Name of the feature flag
        user_context: Optional user context
        
    Returns:
        True if flag is enabled
    """
    # This would typically get the FeatureFlags instance from the application container
    feature_flags = FeatureFlags()
    return feature_flags.is_enabled(flag_name, user_context)


def feature_flag(flag_name: str, user_context: Dict[str, Any] = None):
    """
    Decorator for conditional feature execution.
    
    Args:
        flag_name: Name of the feature flag
        user_context: Optional user context
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if is_feature_enabled(flag_name, user_context):
                return func(*args, **kwargs)
            else:
                return None
        return wrapper
    return decorator


class FeatureFlagMiddleware:
    """Middleware to inject feature flags into request context."""
    
    def __init__(self, feature_flags: FeatureFlags):
        self.feature_flags = feature_flags
    
    def handle(self, request, next_handler):
        """Handle the middleware request."""
        # Extract user context from request
        user_context = self._extract_user_context(request)
        
        # Get enabled flags for this user
        enabled_flags = self.feature_flags.get_enabled_flags(user_context)
        
        # Add to request context
        request.feature_flags = enabled_flags
        request.is_feature_enabled = lambda flag: flag in enabled_flags
        
        return next_handler(request)
    
    def _extract_user_context(self, request) -> Dict[str, Any]:
        """Extract user context from request."""
        context = {}
        
        # Extract user information if available
        if hasattr(request, 'user') and request.user:
            context['user_id'] = getattr(request.user, 'id', None)
            context['role'] = getattr(request.user, 'role', None)
            context['segment'] = getattr(request.user, 'segment', None)
        
        # Extract headers
        context['headers'] = getattr(request, 'headers', {})
        
        # Extract IP address
        context['ip_address'] = getattr(request, 'ip', None)
        
        return context