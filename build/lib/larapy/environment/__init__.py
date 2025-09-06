"""
Environment Management Module

This module provides comprehensive environment management capabilities including:
- Environment detection and management
- Environment-specific service providers
- Feature flags based on environment
- Environment variable validation
- Environment setup utilities
"""

from .manager import EnvironmentManager
from .detector import EnvironmentDetector
from .providers import EnvironmentServiceProvider
from .feature_flags import FeatureFlags
from .validator import EnvironmentValidator
from .setup import EnvironmentSetup

__all__ = [
    'EnvironmentManager',
    'EnvironmentDetector', 
    'EnvironmentServiceProvider',
    'FeatureFlags',
    'EnvironmentValidator',
    'EnvironmentSetup'
]