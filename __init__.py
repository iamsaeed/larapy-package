"""
Larapy - A Python framework inspired by Laravel

This package provides Laravel-like functionality for Python web development,
including dependency injection, routing, HTTP handling, database ORM, 
authentication, middleware, and more.
"""

# Core Phase 1 components
from larapy.core.application import Application
from larapy.routing.route import Route
from larapy.http.request import Request
from larapy.http.response import Response

# Phase 2 Database components
from larapy.database import DatabaseManager, Schema
from larapy.orm import Model

# Phase 2 Auth components (when implemented)
# from larapy.auth import AuthManager

__version__ = "0.2.0"
__author__ = "Larapy Team"
__email__ = "team@larapy.dev"

__all__ = [
    # Core framework
    "Application",
    "Route", 
    "Request",
    "Response",
    # Database ORM
    "DatabaseManager",
    "Schema",
    "Model",
]