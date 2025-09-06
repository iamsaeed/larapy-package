"""
Policy Generator

Generates authorization policy classes for Larapy applications.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from .base_generator import BaseGenerator


class PolicyGenerator(BaseGenerator):
    """Generates authorization policy classes."""
    
    def __init__(self):
        super().__init__()
        self._load_templates()
    
    def generate(self, name: str, **options) -> bool:
        """
        Generate a policy class.
        
        Args:
            name: Policy name or model name
            **options: Generation options
            
        Returns:
            True if generation was successful
        """
        # Determine policy name and model name
        if name.endswith('Policy'):
            policy_name = name
            model_name = name[:-6]  # Remove 'Policy' suffix
        else:
            model_name = name
            policy_name = f"{name}Policy"
        
        model_class = self.get_class_name(model_name)
        policy_class = self.get_class_name(policy_name)
        
        # Determine template type
        if options.get('model', True):
            return self._generate_model_policy(policy_class, model_class, **options)
        else:
            return self._generate_blank_policy(policy_class, **options)
    
    def _generate_model_policy(self, policy_class: str, model_class: str, **options) -> bool:
        """Generate a model-based policy."""
        # Set template variables
        variables = {
            'policy_class': policy_class,
            'model_class': model_class,
            'model_import': f"from app.models.{self.get_snake_case(model_class)} import {model_class}",
            'model_variable': self.get_snake_case(model_class),
            'policy_methods': self._generate_policy_methods(model_class, options),
            'custom_methods': self._generate_custom_methods(options.get('methods', []))
        }
        
        # Render template
        template_content = self.get_template('model_policy')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/policies/{self.get_snake_case(policy_class)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_blank_policy(self, policy_class: str, **options) -> bool:
        """Generate a blank policy."""
        # Set template variables
        variables = {
            'policy_class': policy_class,
            'description': options.get('description', f"{policy_class} for custom authorization logic")
        }
        
        # Render template
        template_content = self.get_template('blank_policy')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/policies/{self.get_snake_case(policy_class)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_policy_methods(self, model_class: str, options: Dict[str, Any]) -> str:
        """Generate standard policy methods for a model."""
        model_variable = self.get_snake_case(model_class)
        
        # Standard CRUD methods
        methods = []
        
        # View any
        methods.append(f"""
    def view_any(self, user):
        \"\"\"
        Determine whether the user can view any {model_class.lower()} models.
        
        Args:
            user: The authenticated user
            
        Returns:
            True if user can view any models
        \"\"\"
        # Allow all authenticated users to view the index
        return True""")
        
        # View
        methods.append(f"""
    def view(self, user, {model_variable}):
        \"\"\"
        Determine whether the user can view the {model_class.lower()} model.
        
        Args:
            user: The authenticated user
            {model_variable}: The {model_class} instance
            
        Returns:
            True if user can view this model
        \"\"\"
        # Users can view their own {model_class.lower()}s or if they're admin
        return user.id == {model_variable}.user_id or user.is_admin()""")
        
        # Create
        methods.append(f"""
    def create(self, user):
        \"\"\"
        Determine whether the user can create {model_class.lower()} models.
        
        Args:
            user: The authenticated user
            
        Returns:
            True if user can create models
        \"\"\"
        # Allow all authenticated users to create
        return True""")
        
        # Update
        methods.append(f"""
    def update(self, user, {model_variable}):
        \"\"\"
        Determine whether the user can update the {model_class.lower()} model.
        
        Args:
            user: The authenticated user
            {model_variable}: The {model_class} instance
            
        Returns:
            True if user can update this model
        \"\"\"
        # Users can update their own {model_class.lower()}s or if they're admin
        return user.id == {model_variable}.user_id or user.is_admin()""")
        
        # Delete
        methods.append(f"""
    def delete(self, user, {model_variable}):
        \"\"\"
        Determine whether the user can delete the {model_class.lower()} model.
        
        Args:
            user: The authenticated user
            {model_variable}: The {model_class} instance
            
        Returns:
            True if user can delete this model
        \"\"\"
        # Users can delete their own {model_class.lower()}s or if they're admin
        return user.id == {model_variable}.user_id or user.is_admin()""")
        
        # Restore (for soft deletes)
        methods.append(f"""
    def restore(self, user, {model_variable}):
        \"\"\"
        Determine whether the user can restore the {model_class.lower()} model.
        
        Args:
            user: The authenticated user
            {model_variable}: The {model_class} instance
            
        Returns:
            True if user can restore this model
        \"\"\"
        # Only admins can restore
        return user.is_admin()""")
        
        # Force delete
        methods.append(f"""
    def force_delete(self, user, {model_variable}):
        \"\"\"
        Determine whether the user can permanently delete the {model_class.lower()} model.
        
        Args:
            user: The authenticated user
            {model_variable}: The {model_class} instance
            
        Returns:
            True if user can permanently delete this model
        \"\"\"
        # Only admins can force delete
        return user.is_admin()""")
        
        return ''.join(methods)
    
    def _generate_custom_methods(self, methods: List[Dict[str, str]]) -> str:
        """Generate custom policy methods."""
        if not methods:
            return ""
        
        custom_methods = []
        for method_config in methods:
            method = self._generate_custom_method(method_config)
            if method:
                custom_methods.append(method)
        
        return ''.join(custom_methods)
    
    def _generate_custom_method(self, method_config: Dict[str, str]) -> str:
        """Generate a single custom policy method."""
        method_name = method_config.get('name')
        description = method_config.get('description', f"Custom authorization for {method_name}")
        parameters = method_config.get('parameters', 'user')
        logic = method_config.get('logic', 'return False')
        
        if not method_name:
            return ""
        
        # Parse parameters
        if parameters == 'user':
            params = 'user'
            param_docs = [('user', 'The authenticated user')]
        else:
            params = parameters
            param_docs = [('user', 'The authenticated user'), ('model', 'Model instance')]
        
        docstring = self.format_docstring(
            description,
            args=param_docs,
            returns="True if user is authorized"
        )
        
        return f"""
{docstring}
    def {method_name}(self, {params}):
        {logic}"""
    
    def _load_templates(self):
        """Load policy templates."""
        self.templates['model_policy'] = '''"""
{{model_class}} Policy

Authorization policy for {{model_class}} model operations.
"""

{{model_import}}
from larapy.auth.user import User
from larapy.auth.access.gate import Gate


class {{policy_class}}:
    """{{policy_class}} for authorizing {{model_class}} operations."""
    
    def before(self, user, ability):
        """
        Perform pre-authorization checks.
        
        This method runs before any other authorization methods.
        If it returns True, authorization passes immediately.
        If it returns False, authorization fails immediately.
        If it returns None, other methods will run.
        
        Args:
            user: The authenticated user
            ability: The ability being checked
            
        Returns:
            True, False, or None
        """
        # Super admins can do everything
        if user.has_role('super_admin'):
            return True
        
        return None{{policy_methods}}{{custom_methods}}
'''

        self.templates['blank_policy'] = '''"""
{{policy_class}} Authorization Policy

{{description}}
"""

from larapy.auth.user import User
from larapy.auth.access.gate import Gate


class {{policy_class}}:
    """{{policy_class}} for custom authorization logic."""
    
    def before(self, user, ability):
        """
        Perform pre-authorization checks.
        
        Args:
            user: The authenticated user
            ability: The ability being checked
            
        Returns:
            True, False, or None
        """
        # Super admins can do everything
        if user.has_role('super_admin'):
            return True
        
        return None
    
    def authorize(self, user, ability, *args):
        """
        General authorization method.
        
        Args:
            user: The authenticated user
            ability: The ability being checked
            *args: Additional arguments
            
        Returns:
            True if user is authorized
        """
        # Add your authorization logic here
        return False
'''