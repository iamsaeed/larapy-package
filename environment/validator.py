"""
Environment Variable Validation

This module provides comprehensive validation for environment variables.
"""

import os
import re
from typing import Dict, List, Any, Optional, Union, Callable, Type
from dataclasses import dataclass, field
from enum import Enum


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationType(Enum):
    """Types of validation."""
    REQUIRED = "required"
    TYPE = "type"
    PATTERN = "pattern"
    CHOICES = "choices"
    RANGE = "range"
    CUSTOM = "custom"


@dataclass
class ValidationRule:
    """Represents a validation rule for an environment variable."""
    name: str
    type: ValidationType
    level: ValidationLevel = ValidationLevel.ERROR
    message: str = ""
    value: Any = None
    validator: Optional[Callable] = None
    environments: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ValidationResult:
    """Result of environment variable validation."""
    variable_name: str
    is_valid: bool
    level: ValidationLevel
    message: str
    actual_value: Any = None
    expected_value: Any = None


class EnvironmentValidator:
    """Validates environment variables according to defined rules."""
    
    def __init__(self):
        self.rules: Dict[str, List[ValidationRule]] = {}
        self.type_converters: Dict[Type, Callable] = {
            str: str,
            int: int,
            float: float,
            bool: self._convert_bool,
            list: self._convert_list,
            dict: self._convert_dict
        }
        
        # Load default validation rules
        self._load_default_rules()
    
    def add_rule(self, variable_name: str, rule: ValidationRule) -> None:
        """
        Add a validation rule for an environment variable.
        
        Args:
            variable_name: Name of the environment variable
            rule: ValidationRule instance
        """
        if variable_name not in self.rules:
            self.rules[variable_name] = []
        self.rules[variable_name].append(rule)
    
    def required(self, variable_name: str, message: str = None, 
                environments: List[str] = None) -> 'EnvironmentValidator':
        """
        Add a required validation rule.
        
        Args:
            variable_name: Name of the environment variable
            message: Custom error message
            environments: Environments where this rule applies
            
        Returns:
            Self for method chaining
        """
        rule = ValidationRule(
            name=f"{variable_name}_required",
            type=ValidationType.REQUIRED,
            message=message or f"Environment variable '{variable_name}' is required",
            environments=environments or []
        )
        self.add_rule(variable_name, rule)
        return self
    
    def type_check(self, variable_name: str, expected_type: Type, 
                  message: str = None, environments: List[str] = None) -> 'EnvironmentValidator':
        """
        Add a type validation rule.
        
        Args:
            variable_name: Name of the environment variable
            expected_type: Expected type
            message: Custom error message
            environments: Environments where this rule applies
            
        Returns:
            Self for method chaining
        """
        rule = ValidationRule(
            name=f"{variable_name}_type",
            type=ValidationType.TYPE,
            value=expected_type,
            message=message or f"Environment variable '{variable_name}' must be of type {expected_type.__name__}",
            environments=environments or []
        )
        self.add_rule(variable_name, rule)
        return self
    
    def pattern(self, variable_name: str, pattern: str, message: str = None,
               environments: List[str] = None) -> 'EnvironmentValidator':
        """
        Add a pattern validation rule.
        
        Args:
            variable_name: Name of the environment variable
            pattern: Regular expression pattern
            message: Custom error message
            environments: Environments where this rule applies
            
        Returns:
            Self for method chaining
        """
        rule = ValidationRule(
            name=f"{variable_name}_pattern",
            type=ValidationType.PATTERN,
            value=pattern,
            message=message or f"Environment variable '{variable_name}' must match pattern: {pattern}",
            environments=environments or []
        )
        self.add_rule(variable_name, rule)
        return self
    
    def choices(self, variable_name: str, valid_choices: List[str], 
               message: str = None, environments: List[str] = None) -> 'EnvironmentValidator':
        """
        Add a choices validation rule.
        
        Args:
            variable_name: Name of the environment variable
            valid_choices: List of valid values
            message: Custom error message
            environments: Environments where this rule applies
            
        Returns:
            Self for method chaining
        """
        rule = ValidationRule(
            name=f"{variable_name}_choices",
            type=ValidationType.CHOICES,
            value=valid_choices,
            message=message or f"Environment variable '{variable_name}' must be one of: {', '.join(valid_choices)}",
            environments=environments or []
        )
        self.add_rule(variable_name, rule)
        return self
    
    def range_check(self, variable_name: str, min_val: Union[int, float] = None, 
                   max_val: Union[int, float] = None, message: str = None,
                   environments: List[str] = None) -> 'EnvironmentValidator':
        """
        Add a range validation rule.
        
        Args:
            variable_name: Name of the environment variable
            min_val: Minimum value
            max_val: Maximum value
            message: Custom error message
            environments: Environments where this rule applies
            
        Returns:
            Self for method chaining
        """
        rule = ValidationRule(
            name=f"{variable_name}_range",
            type=ValidationType.RANGE,
            value={'min': min_val, 'max': max_val},
            message=message or f"Environment variable '{variable_name}' must be between {min_val} and {max_val}",
            environments=environments or []
        )
        self.add_rule(variable_name, rule)
        return self
    
    def custom(self, variable_name: str, validator: Callable, message: str = None,
              environments: List[str] = None) -> 'EnvironmentValidator':
        """
        Add a custom validation rule.
        
        Args:
            variable_name: Name of the environment variable
            validator: Custom validator function
            message: Custom error message
            environments: Environments where this rule applies
            
        Returns:
            Self for method chaining
        """
        rule = ValidationRule(
            name=f"{variable_name}_custom",
            type=ValidationType.CUSTOM,
            validator=validator,
            message=message or f"Environment variable '{variable_name}' failed custom validation",
            environments=environments or []
        )
        self.add_rule(variable_name, rule)
        return self
    
    def validate(self, environment_name: str = None) -> List[ValidationResult]:
        """
        Validate all environment variables according to defined rules.
        
        Args:
            environment_name: Current environment name for environment-specific rules
            
        Returns:
            List of validation results
        """
        results = []
        
        for variable_name, rules in self.rules.items():
            for rule in rules:
                # Skip rule if it's environment-specific and doesn't match current environment
                if rule.environments and environment_name not in rule.environments:
                    continue
                
                result = self._validate_rule(variable_name, rule)
                results.append(result)
        
        return results
    
    def validate_variable(self, variable_name: str, environment_name: str = None) -> List[ValidationResult]:
        """
        Validate a specific environment variable.
        
        Args:
            variable_name: Name of the environment variable
            environment_name: Current environment name
            
        Returns:
            List of validation results for the variable
        """
        results = []
        
        if variable_name in self.rules:
            for rule in self.rules[variable_name]:
                if rule.environments and environment_name not in rule.environments:
                    continue
                
                result = self._validate_rule(variable_name, rule)
                results.append(result)
        
        return results
    
    def is_valid(self, environment_name: str = None) -> bool:
        """
        Check if all environment variables are valid.
        
        Args:
            environment_name: Current environment name
            
        Returns:
            True if all validations pass
        """
        results = self.validate(environment_name)
        return all(result.is_valid or result.level != ValidationLevel.ERROR for result in results)
    
    def get_validation_summary(self, environment_name: str = None) -> Dict[str, Any]:
        """
        Get a summary of validation results.
        
        Args:
            environment_name: Current environment name
            
        Returns:
            Validation summary dictionary
        """
        results = self.validate(environment_name)
        
        errors = [r for r in results if r.level == ValidationLevel.ERROR and not r.is_valid]
        warnings = [r for r in results if r.level == ValidationLevel.WARNING and not r.is_valid]
        info = [r for r in results if r.level == ValidationLevel.INFO and not r.is_valid]
        
        return {
            'total_variables': len(self.rules),
            'total_rules': sum(len(rules) for rules in self.rules.values()),
            'errors': len(errors),
            'warnings': len(warnings),
            'info': len(info),
            'is_valid': len(errors) == 0,
            'error_details': [{'variable': r.variable_name, 'message': r.message} for r in errors],
            'warning_details': [{'variable': r.variable_name, 'message': r.message} for r in warnings],
            'info_details': [{'variable': r.variable_name, 'message': r.message} for r in info]
        }
    
    def _validate_rule(self, variable_name: str, rule: ValidationRule) -> ValidationResult:
        """Validate a single rule against an environment variable."""
        actual_value = os.getenv(variable_name)
        
        if rule.type == ValidationType.REQUIRED:
            is_valid = actual_value is not None and actual_value.strip() != ""
            return ValidationResult(
                variable_name=variable_name,
                is_valid=is_valid,
                level=rule.level,
                message=rule.message if not is_valid else f"Required variable '{variable_name}' is present",
                actual_value=actual_value
            )
        
        # If variable is not set and not required, skip other validations
        if actual_value is None:
            return ValidationResult(
                variable_name=variable_name,
                is_valid=True,
                level=ValidationLevel.INFO,
                message=f"Optional variable '{variable_name}' is not set",
                actual_value=None
            )
        
        if rule.type == ValidationType.TYPE:
            is_valid, converted_value = self._validate_type(actual_value, rule.value)
            return ValidationResult(
                variable_name=variable_name,
                is_valid=is_valid,
                level=rule.level,
                message=rule.message if not is_valid else f"Variable '{variable_name}' has correct type",
                actual_value=converted_value if is_valid else actual_value,
                expected_value=rule.value
            )
        
        elif rule.type == ValidationType.PATTERN:
            is_valid = bool(re.match(rule.value, actual_value))
            return ValidationResult(
                variable_name=variable_name,
                is_valid=is_valid,
                level=rule.level,
                message=rule.message if not is_valid else f"Variable '{variable_name}' matches pattern",
                actual_value=actual_value,
                expected_value=rule.value
            )
        
        elif rule.type == ValidationType.CHOICES:
            is_valid = actual_value in rule.value
            return ValidationResult(
                variable_name=variable_name,
                is_valid=is_valid,
                level=rule.level,
                message=rule.message if not is_valid else f"Variable '{variable_name}' has valid value",
                actual_value=actual_value,
                expected_value=rule.value
            )
        
        elif rule.type == ValidationType.RANGE:
            is_valid, numeric_value = self._validate_numeric_range(actual_value, rule.value)
            return ValidationResult(
                variable_name=variable_name,
                is_valid=is_valid,
                level=rule.level,
                message=rule.message if not is_valid else f"Variable '{variable_name}' is in valid range",
                actual_value=numeric_value if is_valid else actual_value,
                expected_value=rule.value
            )
        
        elif rule.type == ValidationType.CUSTOM:
            try:
                is_valid = rule.validator(actual_value)
                return ValidationResult(
                    variable_name=variable_name,
                    is_valid=is_valid,
                    level=rule.level,
                    message=rule.message if not is_valid else f"Variable '{variable_name}' passed custom validation",
                    actual_value=actual_value
                )
            except Exception as e:
                return ValidationResult(
                    variable_name=variable_name,
                    is_valid=False,
                    level=rule.level,
                    message=f"Custom validation error for '{variable_name}': {str(e)}",
                    actual_value=actual_value
                )
        
        return ValidationResult(
            variable_name=variable_name,
            is_valid=True,
            level=ValidationLevel.INFO,
            message=f"No validation performed for '{variable_name}'",
            actual_value=actual_value
        )
    
    def _validate_type(self, value: str, expected_type: Type) -> tuple[bool, Any]:
        """Validate and convert value to expected type."""
        try:
            if expected_type in self.type_converters:
                converted_value = self.type_converters[expected_type](value)
                return True, converted_value
            else:
                return False, value
        except (ValueError, TypeError):
            return False, value
    
    def _validate_numeric_range(self, value: str, range_config: Dict[str, Union[int, float]]) -> tuple[bool, Any]:
        """Validate numeric value is within specified range."""
        try:
            # Try to convert to float first, then int if possible
            if '.' in value:
                numeric_value = float(value)
            else:
                numeric_value = int(value)
            
            min_val = range_config.get('min')
            max_val = range_config.get('max')
            
            if min_val is not None and numeric_value < min_val:
                return False, numeric_value
            if max_val is not None and numeric_value > max_val:
                return False, numeric_value
            
            return True, numeric_value
            
        except (ValueError, TypeError):
            return False, value
    
    def _convert_bool(self, value: str) -> bool:
        """Convert string to boolean."""
        return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
    
    def _convert_list(self, value: str) -> List[str]:
        """Convert comma-separated string to list."""
        return [item.strip() for item in value.split(',') if item.strip()]
    
    def _convert_dict(self, value: str) -> Dict[str, str]:
        """Convert key=value,key=value string to dictionary."""
        result = {}
        for pair in value.split(','):
            if '=' in pair:
                key, val = pair.split('=', 1)
                result[key.strip()] = val.strip()
        return result
    
    def _load_default_rules(self) -> None:
        """Load default validation rules for common environment variables."""
        
        # Application environment
        self.required('APP_ENV', 'Application environment must be specified')
        self.choices('APP_ENV', ['development', 'testing', 'staging', 'production'])
        
        # Debug mode
        self.type_check('APP_DEBUG', bool)
        
        # Database configuration
        self.required('DATABASE_URL', 'Database URL is required', ['production', 'staging'])
        self.pattern('DATABASE_URL', r'^(mysql|postgresql|sqlite)://.+', 'Invalid database URL format')
        
        # Redis configuration (optional but validated if present)
        self.pattern('REDIS_URL', r'^redis://.+', 'Invalid Redis URL format')
        self.range_check('REDIS_PORT', 1, 65535)
        
        # Security
        self.required('SECRET_KEY', 'Secret key is required for security')
        self.custom('SECRET_KEY', lambda x: len(x) >= 32, 'Secret key must be at least 32 characters long')
        
        # Server configuration
        self.range_check('PORT', 1, 65535)
        self.choices('LOG_LEVEL', ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
        
        # Email configuration (if present)
        self.pattern('SMTP_HOST', r'^[a-zA-Z0-9.-]+$', 'Invalid SMTP host format')
        self.range_check('SMTP_PORT', 1, 65535)
        self.choices('SMTP_SECURITY', ['none', 'ssl', 'tls'])
        
        # API keys (if present)
        self.custom('API_KEY', lambda x: len(x) >= 16, 'API key must be at least 16 characters long')
        
        # File upload limits
        self.type_check('MAX_UPLOAD_SIZE', int)
        self.range_check('MAX_UPLOAD_SIZE', 1, 1000000000)  # 1GB max