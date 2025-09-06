"""
Environment-Specific Service Providers

This module provides environment-specific service provider management.
"""

import os
from typing import Dict, List, Type, Any, Optional
from abc import ABC, abstractmethod
from ..core.service_provider import ServiceProvider
from .detector import EnvironmentDetector, EnvironmentInfo


class EnvironmentAwareServiceProvider(ServiceProvider, ABC):
    """Base class for environment-aware service providers."""
    
    def __init__(self, app):
        super().__init__(app)
        self.environment_detector = EnvironmentDetector()
        self.environment = self.environment_detector.detect()
    
    @abstractmethod
    def get_supported_environments(self) -> List[str]:
        """
        Get list of environments this provider supports.
        
        Returns:
            List of environment names
        """
        pass
    
    def should_register(self) -> bool:
        """
        Determine if this provider should be registered in current environment.
        
        Returns:
            True if provider should be registered
        """
        supported_envs = self.get_supported_environments()
        return self.environment.name in supported_envs
    
    def register_for_environment(self, environment_name: str) -> None:
        """
        Register services specific to an environment.
        
        Args:
            environment_name: Name of the environment
        """
        method_name = f"register_for_{environment_name}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            method()
    
    def register(self) -> None:
        """Register services if environment is supported."""
        if self.should_register():
            super().register()
            self.register_for_environment(self.environment.name)


class DevelopmentServiceProvider(EnvironmentAwareServiceProvider):
    """Service provider for development environment."""
    
    def get_supported_environments(self) -> List[str]:
        return ['development', 'local']
    
    def register(self) -> None:
        """Register development-specific services."""
        if not self.should_register():
            return
        
        # Register debug services
        self._register_debug_services()
        
        # Register development tools
        self._register_dev_tools()
        
        # Register hot reload services
        self._register_hot_reload()
    
    def _register_debug_services(self) -> None:
        """Register debugging services."""
        from ..debug.debugger import Debugger
        from ..debug.profiler import Profiler
        from ..debug.query_logger import QueryLogger
        
        # Register debugger
        debugger = Debugger(enabled=True)
        self.app.instance('debugger', debugger)
        
        # Register profiler
        profiler = Profiler(enabled=True)
        self.app.instance('profiler', profiler)
        
        # Register query logger
        query_logger = QueryLogger(enabled=True)
        self.app.instance('query_logger', query_logger)
    
    def _register_dev_tools(self) -> None:
        """Register development tools."""
        # Register code generators
        from ..console.generators import ModelGenerator, ControllerGenerator
        
        self.app.instance('model_generator', ModelGenerator())
        self.app.instance('controller_generator', ControllerGenerator())
        
        # Register development middleware
        from ..middleware.development import DevelopmentMiddleware
        
        middleware_stack = self.app.resolve('middleware_stack', [])
        middleware_stack.append(DevelopmentMiddleware)
        self.app.instance('middleware_stack', middleware_stack)
    
    def _register_hot_reload(self) -> None:
        """Register hot reload services."""
        from ..dev.hot_reload import HotReloadService
        
        hot_reload = HotReloadService(
            watch_paths=['app/', 'config/', 'routes/'],
            ignore_patterns=['*.pyc', '__pycache__']
        )
        self.app.instance('hot_reload', hot_reload)


class TestingServiceProvider(EnvironmentAwareServiceProvider):
    """Service provider for testing environment."""
    
    def get_supported_environments(self) -> List[str]:
        return ['testing', 'test']
    
    def register(self) -> None:
        """Register testing-specific services."""
        if not self.should_register():
            return
        
        # Register test services
        self._register_test_services()
        
        # Register test database
        self._register_test_database()
        
        # Register test utilities
        self._register_test_utilities()
    
    def _register_test_services(self) -> None:
        """Register testing services."""
        from ..testing.test_client import TestClient
        from ..testing.database_cleaner import DatabaseCleaner
        from ..testing.factory_registry import FactoryRegistry
        
        # Register test client
        test_client = TestClient(self.app)
        self.app.instance('test_client', test_client)
        
        # Register database cleaner
        db_cleaner = DatabaseCleaner(self.app.resolve('db'))
        self.app.instance('database_cleaner', db_cleaner)
        
        # Register factory registry
        factory_registry = FactoryRegistry()
        self.app.instance('factory_registry', factory_registry)
    
    def _register_test_database(self) -> None:
        """Register test database configuration."""
        # Override database configuration for testing
        db_manager = self.app.resolve('db')
        
        # Use in-memory SQLite for tests
        test_config = {
            'driver': 'sqlite',
            'database': ':memory:',
            'foreign_key_checks': True
        }
        
        db_manager.add_connection('testing', test_config)
        db_manager.set_default_connection('testing')
    
    def _register_test_utilities(self) -> None:
        """Register testing utilities."""
        from ..testing.assertions import AssertionMixin
        from ..testing.mock_registry import MockRegistry
        
        # Register assertion utilities
        self.app.instance('assertions', AssertionMixin())
        
        # Register mock registry
        mock_registry = MockRegistry()
        self.app.instance('mock_registry', mock_registry)


class ProductionServiceProvider(EnvironmentAwareServiceProvider):
    """Service provider for production environment."""
    
    def get_supported_environments(self) -> List[str]:
        return ['production', 'prod']
    
    def register(self) -> None:
        """Register production-specific services."""
        if not self.should_register():
            return
        
        # Register production services
        self._register_production_services()
        
        # Register monitoring
        self._register_monitoring()
        
        # Register security services
        self._register_security()
    
    def _register_production_services(self) -> None:
        """Register production services."""
        from ..cache.redis_cache import RedisCache
        from ..session.redis_session import RedisSessionStore
        from ..queue.redis_queue import RedisQueue
        
        # Register Redis cache
        redis_cache = RedisCache(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_CACHE_DB', 0))
        )
        self.app.instance('cache', redis_cache)
        
        # Register Redis session store
        session_store = RedisSessionStore(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_SESSION_DB', 1))
        )
        self.app.instance('session_store', session_store)
        
        # Register queue system
        queue = RedisQueue(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_QUEUE_DB', 2))
        )
        self.app.instance('queue', queue)
    
    def _register_monitoring(self) -> None:
        """Register monitoring services."""
        from ..monitoring.performance_monitor import PerformanceMonitor
        from ..monitoring.error_tracker import ErrorTracker
        from ..monitoring.health_checker import HealthChecker
        
        # Register performance monitor
        perf_monitor = PerformanceMonitor(
            enabled=True,
            sample_rate=float(os.getenv('PERFORMANCE_SAMPLE_RATE', '0.1'))
        )
        self.app.instance('performance_monitor', perf_monitor)
        
        # Register error tracker
        error_tracker = ErrorTracker(
            dsn=os.getenv('ERROR_TRACKING_DSN'),
            environment='production'
        )
        self.app.instance('error_tracker', error_tracker)
        
        # Register health checker
        health_checker = HealthChecker()
        self.app.instance('health_checker', health_checker)
    
    def _register_security(self) -> None:
        """Register security services."""
        from ..security.rate_limiter import RateLimiter
        from ..security.security_headers import SecurityHeadersMiddleware
        from ..security.csrf_protection import CsrfProtection
        
        # Register rate limiter
        rate_limiter = RateLimiter(
            redis_host=os.getenv('REDIS_HOST', 'localhost'),
            redis_port=int(os.getenv('REDIS_PORT', 6379))
        )
        self.app.instance('rate_limiter', rate_limiter)
        
        # Register security middleware
        middleware_stack = self.app.resolve('middleware_stack', [])
        middleware_stack.extend([
            SecurityHeadersMiddleware,
            CsrfProtection
        ])
        self.app.instance('middleware_stack', middleware_stack)


class StagingServiceProvider(EnvironmentAwareServiceProvider):
    """Service provider for staging environment."""
    
    def get_supported_environments(self) -> List[str]:
        return ['staging', 'stage']
    
    def register(self) -> None:
        """Register staging-specific services."""
        if not self.should_register():
            return
        
        # Register staging services (similar to production but with some debug features)
        self._register_staging_services()
        
        # Register limited monitoring
        self._register_limited_monitoring()
    
    def _register_staging_services(self) -> None:
        """Register staging services."""
        # Similar to production but potentially with some debug features
        from ..cache.redis_cache import RedisCache
        
        # Use Redis cache but with shorter TTL
        redis_cache = RedisCache(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_CACHE_DB', 0)),
            default_ttl=300  # 5 minutes instead of longer production TTL
        )
        self.app.instance('cache', redis_cache)
    
    def _register_limited_monitoring(self) -> None:
        """Register limited monitoring for staging."""
        from ..monitoring.error_tracker import ErrorTracker
        
        # Register error tracker with staging config
        error_tracker = ErrorTracker(
            dsn=os.getenv('ERROR_TRACKING_DSN'),
            environment='staging',
            sample_rate=1.0  # Capture all errors in staging
        )
        self.app.instance('error_tracker', error_tracker)


class EnvironmentServiceProvider(ServiceProvider):
    """Main service provider that manages environment-specific providers."""
    
    def __init__(self, app):
        super().__init__(app)
        self.environment_detector = EnvironmentDetector()
        self.environment = self.environment_detector.detect()
        self.env_providers: Dict[str, Type[EnvironmentAwareServiceProvider]] = {}
        
        # Register default environment providers
        self._register_default_providers()
    
    def register(self) -> None:
        """Register environment-specific service providers."""
        # Register the environment detector
        self.app.instance('environment_detector', self.environment_detector)
        self.app.instance('environment', self.environment)
        
        # Register appropriate environment provider
        self._register_environment_provider()
    
    def boot(self) -> None:
        """Boot environment-specific services."""
        # Boot any environment-specific services
        env_provider_key = f"{self.environment.name}_provider"
        if self.app.has_instance(env_provider_key):
            provider = self.app.resolve(env_provider_key)
            if hasattr(provider, 'boot'):
                provider.boot()
    
    def add_environment_provider(self, environment: str, 
                                provider_class: Type[EnvironmentAwareServiceProvider]) -> None:
        """
        Add a custom environment provider.
        
        Args:
            environment: Environment name
            provider_class: Provider class
        """
        self.env_providers[environment] = provider_class
    
    def _register_default_providers(self) -> None:
        """Register default environment providers."""
        self.env_providers = {
            'development': DevelopmentServiceProvider,
            'local': DevelopmentServiceProvider,
            'testing': TestingServiceProvider,
            'test': TestingServiceProvider,
            'staging': StagingServiceProvider,
            'stage': StagingServiceProvider,
            'production': ProductionServiceProvider,
            'prod': ProductionServiceProvider
        }
    
    def _register_environment_provider(self) -> None:
        """Register the appropriate environment provider."""
        env_name = self.environment.name
        
        if env_name in self.env_providers:
            provider_class = self.env_providers[env_name]
            provider = provider_class(self.app)
            
            # Register the provider
            provider.register()
            
            # Store provider instance for later use
            self.app.instance(f"{env_name}_provider", provider)