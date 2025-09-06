"""
Environment Detection

Provides advanced environment detection capabilities for Larapy applications.
"""

import os
import socket
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum


class EnvironmentType(Enum):
    """Standard environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"


@dataclass
class EnvironmentInfo:
    """Information about the current environment."""
    name: str
    type: EnvironmentType
    is_debug: bool
    is_testing: bool
    is_production: bool
    hostname: str
    platform: str
    python_version: str
    working_directory: str
    config_path: Optional[str]
    features: Dict[str, bool]
    metadata: Dict[str, Any]


class EnvironmentDetector:
    """Advanced environment detection with multiple detection strategies."""
    
    def __init__(self):
        self.detectors: List[Callable[[], Optional[str]]] = []
        self.environment_configs: Dict[str, Dict[str, Any]] = {}
        self.custom_rules: List[Callable[[], Optional[EnvironmentInfo]]] = []
        
        # Register default detectors
        self._register_default_detectors()
        
        # Load default environment configurations
        self._load_default_configs()
    
    def detect(self) -> EnvironmentInfo:
        """
        Detect the current environment using all available strategies.
        
        Returns:
            EnvironmentInfo object with detected environment details
        """
        # Try custom rules first
        for rule in self.custom_rules:
            result = rule()
            if result:
                return result
        
        # Use standard detection
        environment_name = self._detect_environment_name()
        return self._build_environment_info(environment_name)
    
    def register_detector(self, detector: Callable[[], Optional[str]]) -> None:
        """
        Register a custom environment detector.
        
        Args:
            detector: Function that returns environment name or None
        """
        self.detectors.append(detector)
    
    def register_custom_rule(self, rule: Callable[[], Optional[EnvironmentInfo]]) -> None:
        """
        Register a custom detection rule that returns complete EnvironmentInfo.
        
        Args:
            rule: Function that returns EnvironmentInfo or None
        """
        self.custom_rules.append(rule)
    
    def add_environment_config(self, name: str, config: Dict[str, Any]) -> None:
        """
        Add configuration for a specific environment.
        
        Args:
            name: Environment name
            config: Environment configuration
        """
        self.environment_configs[name] = config
    
    def is_environment(self, environment_name: str) -> bool:
        """
        Check if current environment matches the given name.
        
        Args:
            environment_name: Environment name to check
            
        Returns:
            True if current environment matches
        """
        current_env = self.detect()
        return current_env.name.lower() == environment_name.lower()
    
    def get_environment_config(self, environment_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific environment.
        
        Args:
            environment_name: Environment name
            
        Returns:
            Environment configuration dictionary
        """
        return self.environment_configs.get(environment_name, {})
    
    def _detect_environment_name(self) -> str:
        """Detect environment name using registered detectors."""
        # Try each detector in order
        for detector in self.detectors:
            result = detector()
            if result:
                return result
        
        # Default fallback
        return "production"
    
    def _build_environment_info(self, environment_name: str) -> EnvironmentInfo:
        """Build EnvironmentInfo object from environment name."""
        # Get environment type
        env_type = self._get_environment_type(environment_name)
        
        # Get environment configuration
        config = self.get_environment_config(environment_name)
        
        # Build environment info
        return EnvironmentInfo(
            name=environment_name,
            type=env_type,
            is_debug=config.get('debug', env_type != EnvironmentType.PRODUCTION),
            is_testing=env_type == EnvironmentType.TESTING,
            is_production=env_type == EnvironmentType.PRODUCTION,
            hostname=socket.gethostname(),
            platform=platform.system(),
            python_version=platform.python_version(),
            working_directory=os.getcwd(),
            config_path=config.get('config_path'),
            features=config.get('features', {}),
            metadata=config.get('metadata', {})
        )
    
    def _get_environment_type(self, environment_name: str) -> EnvironmentType:
        """Get environment type from name."""
        name_lower = environment_name.lower()
        
        if name_lower in ['dev', 'development', 'local']:
            return EnvironmentType.DEVELOPMENT
        elif name_lower in ['test', 'testing']:
            return EnvironmentType.TESTING
        elif name_lower in ['stage', 'staging']:
            return EnvironmentType.STAGING
        elif name_lower in ['prod', 'production']:
            return EnvironmentType.PRODUCTION
        else:
            return EnvironmentType.DEVELOPMENT  # Default
    
    def _register_default_detectors(self) -> None:
        """Register default environment detectors."""
        
        # 1. Environment variable detector
        def env_var_detector():
            return os.getenv('APP_ENV') or os.getenv('ENVIRONMENT') or os.getenv('ENV')
        
        # 2. Configuration file detector
        def config_file_detector():
            config_files = [
                '.env',
                'config/app.py',
                'config/environment.py'
            ]
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    try:
                        with open(config_file, 'r') as f:
                            content = f.read()
                            # Look for environment settings
                            if 'APP_ENV' in content:
                                for line in content.split('\n'):
                                    if line.strip().startswith('APP_ENV'):
                                        return line.split('=')[1].strip().strip('"\'')
                    except:
                        continue
            return None
        
        # 3. Hostname-based detector
        def hostname_detector():
            hostname = socket.gethostname().lower()
            
            if any(keyword in hostname for keyword in ['dev', 'development']):
                return 'development'
            elif any(keyword in hostname for keyword in ['test', 'testing']):
                return 'testing'
            elif any(keyword in hostname for keyword in ['stage', 'staging']):
                return 'staging'
            elif any(keyword in hostname for keyword in ['prod', 'production']):
                return 'production'
            
            return None
        
        # 4. Directory-based detector
        def directory_detector():
            cwd = Path.cwd().name.lower()
            
            if any(keyword in cwd for keyword in ['dev', 'development']):
                return 'development'
            elif any(keyword in cwd for keyword in ['test', 'testing']):
                return 'testing'
            elif any(keyword in cwd for keyword in ['stage', 'staging']):
                return 'staging'
                
            return None
        
        # 5. Port-based detector (for development)
        def port_detector():
            # Check if common development ports are in use
            dev_ports = [3000, 8000, 8080, 5000]
            
            for port in dev_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('localhost', port))
                    sock.close()
                    if result == 0:  # Port is in use
                        return 'development'
                except:
                    continue
            
            return None
        
        # 6. File marker detector
        def marker_file_detector():
            markers = {
                '.development': 'development',
                '.testing': 'testing', 
                '.staging': 'staging',
                '.production': 'production',
                'development.marker': 'development',
                'testing.marker': 'testing'
            }
            
            for marker_file, env_name in markers.items():
                if os.path.exists(marker_file):
                    return env_name
            
            return None
        
        # 7. Docker/Container detector
        def container_detector():
            # Check for Docker environment
            if os.path.exists('/.dockerenv'):
                # Look for environment labels
                env_from_docker = os.getenv('DOCKER_ENV')
                if env_from_docker:
                    return env_from_docker
                return 'production'  # Docker usually means production
            
            # Check for Kubernetes
            if os.getenv('KUBERNETES_SERVICE_HOST'):
                return os.getenv('KUBE_ENV', 'production')
            
            return None
        
        # Register all detectors in priority order
        self.detectors.extend([
            env_var_detector,
            marker_file_detector,
            config_file_detector,
            container_detector,
            hostname_detector,
            directory_detector,
            port_detector
        ])
    
    def _load_default_configs(self) -> None:
        """Load default configurations for standard environments."""
        
        self.environment_configs = {
            'development': {
                'debug': True,
                'features': {
                    'debug_toolbar': True,
                    'hot_reload': True,
                    'detailed_errors': True,
                    'query_logging': True,
                    'cache_disable': True
                },
                'metadata': {
                    'description': 'Development environment',
                    'auto_reload': True,
                    'log_level': 'DEBUG'
                }
            },
            'testing': {
                'debug': True,
                'features': {
                    'debug_toolbar': False,
                    'hot_reload': False,
                    'detailed_errors': True,
                    'query_logging': False,
                    'cache_disable': True,
                    'database_transactions': True
                },
                'metadata': {
                    'description': 'Testing environment',
                    'auto_reload': False,
                    'log_level': 'INFO',
                    'database': 'testing'
                }
            },
            'staging': {
                'debug': False,
                'features': {
                    'debug_toolbar': False,
                    'hot_reload': False,
                    'detailed_errors': False,
                    'query_logging': False,
                    'cache_disable': False,
                    'performance_monitoring': True
                },
                'metadata': {
                    'description': 'Staging environment',
                    'auto_reload': False,
                    'log_level': 'WARNING'
                }
            },
            'production': {
                'debug': False,
                'features': {
                    'debug_toolbar': False,
                    'hot_reload': False,
                    'detailed_errors': False,
                    'query_logging': False,
                    'cache_disable': False,
                    'performance_monitoring': True,
                    'error_tracking': True,
                    'security_headers': True
                },
                'metadata': {
                    'description': 'Production environment',
                    'auto_reload': False,
                    'log_level': 'ERROR',
                    'secure': True
                }
            },
            'local': {
                'debug': True,
                'features': {
                    'debug_toolbar': True,
                    'hot_reload': True,
                    'detailed_errors': True,
                    'query_logging': True,
                    'cache_disable': True
                },
                'metadata': {
                    'description': 'Local development environment',
                    'auto_reload': True,
                    'log_level': 'DEBUG'
                }
            }
        }