"""
Base Generator Class

Provides the foundation for all code generators in Larapy.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from datetime import datetime


class BaseGenerator(ABC):
    """Base class for all code generators."""
    
    def __init__(self):
        self.templates: Dict[str, str] = {}
        self.variables: Dict[str, Any] = {}
        self.created_files: List[str] = []
        
    @abstractmethod
    def generate(self, name: str, **options) -> bool:
        """
        Generate code with the given name and options.
        
        Args:
            name: Name of the component to generate
            **options: Additional options for generation
            
        Returns:
            True if generation was successful
        """
        pass
    
    def set_variable(self, key: str, value: Any) -> None:
        """
        Set a template variable.
        
        Args:
            key: Variable name
            value: Variable value
        """
        self.variables[key] = value
    
    def set_variables(self, variables: Dict[str, Any]) -> None:
        """
        Set multiple template variables.
        
        Args:
            variables: Dictionary of variables
        """
        self.variables.update(variables)
    
    def get_template(self, template_name: str) -> str:
        """
        Get a template by name.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template content
        """
        return self.templates.get(template_name, '')
    
    def render_template(self, template_content: str, variables: Dict[str, Any] = None) -> str:
        """
        Render a template with variables.
        
        Args:
            template_content: Template content
            variables: Variables to use for rendering
            
        Returns:
            Rendered template
        """
        if variables is None:
            variables = self.variables
        else:
            # Merge with instance variables
            merged_vars = self.variables.copy()
            merged_vars.update(variables)
            variables = merged_vars
        
        # Simple template rendering (replace {{variable}} with value)
        rendered = template_content
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))
        
        return rendered
    
    def write_file(self, file_path: str, content: str, force: bool = False) -> bool:
        """
        Write content to a file.
        
        Args:
            file_path: Path where to write the file
            content: Content to write
            force: Whether to overwrite existing files
            
        Returns:
            True if file was written successfully
        """
        path = Path(file_path)
        
        # Check if file exists and force is not enabled
        if path.exists() and not force:
            return False
        
        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.created_files.append(str(path))
            return True
            
        except Exception:
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists
        """
        return Path(file_path).exists()
    
    def ensure_directory(self, directory: str) -> None:
        """
        Ensure a directory exists.
        
        Args:
            directory: Directory path
        """
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get_class_name(self, name: str) -> str:
        """
        Convert a name to a proper class name (PascalCase).
        
        Args:
            name: Input name
            
        Returns:
            Class name in PascalCase
        """
        # Remove underscores and hyphens, then capitalize each word
        words = re.split(r'[-_\s]+', name)
        return ''.join(word.capitalize() for word in words if word)
    
    def get_snake_case(self, name: str) -> str:
        """
        Convert a name to snake_case.
        
        Args:
            name: Input name
            
        Returns:
            Name in snake_case
        """
        # Convert PascalCase/camelCase to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def get_kebab_case(self, name: str) -> str:
        """
        Convert a name to kebab-case.
        
        Args:
            name: Input name
            
        Returns:
            Name in kebab-case
        """
        return self.get_snake_case(name).replace('_', '-')
    
    def get_plural(self, name: str) -> str:
        """
        Get the plural form of a name (simple implementation).
        
        Args:
            name: Singular name
            
        Returns:
            Plural form
        """
        if name.endswith('y'):
            return name[:-1] + 'ies'
        elif name.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return name + 'es'
        elif name.endswith('f'):
            return name[:-1] + 'ves'
        elif name.endswith('fe'):
            return name[:-2] + 'ves'
        else:
            return name + 's'
    
    def get_table_name(self, model_name: str) -> str:
        """
        Get table name from model name.
        
        Args:
            model_name: Model name
            
        Returns:
            Table name (plural snake_case)
        """
        snake_name = self.get_snake_case(model_name)
        return self.get_plural(snake_name)
    
    def get_timestamp(self) -> str:
        """
        Get current timestamp for migrations.
        
        Returns:
            Timestamp string in format YYYY_MM_DD_HHMMSS
        """
        return datetime.now().strftime('%Y_%m_%d_%H%M%S')
    
    def get_migration_name(self, description: str) -> str:
        """
        Generate migration file name.
        
        Args:
            description: Migration description
            
        Returns:
            Migration file name
        """
        timestamp = self.get_timestamp()
        snake_description = self.get_snake_case(description)
        return f"{timestamp}_{snake_description}.py"
    
    def add_import(self, imports: List[str], new_import: str) -> List[str]:
        """
        Add an import to the imports list if it doesn't exist.
        
        Args:
            imports: Current imports list
            new_import: New import to add
            
        Returns:
            Updated imports list
        """
        if new_import not in imports:
            imports.append(new_import)
        return imports
    
    def format_docstring(self, description: str, args: List[tuple] = None, 
                        returns: str = None, indent: str = "    ") -> str:
        """
        Format a docstring with proper indentation.
        
        Args:
            description: Method description
            args: List of (name, description) tuples for arguments
            returns: Return value description
            indent: Indentation string
            
        Returns:
            Formatted docstring
        """
        lines = [f'{indent}"""', f'{indent}{description}']
        
        if args:
            lines.append(f'{indent}')
            lines.append(f'{indent}Args:')
            for arg_name, arg_desc in args:
                lines.append(f'{indent}    {arg_name}: {arg_desc}')
        
        if returns:
            lines.append(f'{indent}')
            lines.append(f'{indent}Returns:')
            lines.append(f'{indent}    {returns}')
        
        lines.append(f'{indent}"""')
        return '\n'.join(lines)
    
    def get_created_files(self) -> List[str]:
        """
        Get list of files created during generation.
        
        Returns:
            List of created file paths
        """
        return self.created_files.copy()
    
    def reset(self) -> None:
        """Reset the generator state."""
        self.variables.clear()
        self.created_files.clear()