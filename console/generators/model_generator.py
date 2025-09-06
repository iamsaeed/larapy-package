"""
Model Generator

Generates Larapy model classes for Larapy applications.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from .base_generator import BaseGenerator


class ModelGenerator(BaseGenerator):
    """Generates Larapy model classes."""
    
    def __init__(self):
        super().__init__()
        self._load_templates()
    
    def generate(self, name: str, **options) -> bool:
        """
        Generate a model class.
        
        Args:
            name: Model name
            **options: Generation options
            
        Returns:
            True if generation was successful
        """
        # Parse options
        migration = options.get('migration', False)
        factory = options.get('factory', False)
        seeder = options.get('seeder', False)
        controller = options.get('controller', False)
        resource = options.get('resource', False)
        api = options.get('api', False)
        pivot = options.get('pivot', False)
        
        # Generate model
        success = self._generate_model(name, **options)
        
        if success and migration:
            success &= self._generate_migration(name, **options)
        
        if success and factory:
            success &= self._generate_factory(name, **options)
        
        if success and seeder:
            success &= self._generate_seeder(name, **options)
        
        if success and controller:
            success &= self._generate_controller(name, resource, api, **options)
        
        return success
    
    def _generate_model(self, name: str, **options) -> bool:
        """Generate the model file."""
        class_name = self.get_class_name(name)
        table_name = options.get('table', self.get_table_name(class_name))
        
        # Set template variables
        variables = {
            'class_name': class_name,
            'table_name': table_name,
            'fillable': self._format_fillable(options.get('fillable', [])),
            'hidden': self._format_hidden(options.get('hidden', [])),
            'casts': self._format_casts(options.get('casts', {})),
            'relationships': self._generate_relationships(options.get('relationships', [])),
            'timestamps': str(options.get('timestamps', True)).lower(),
            'pivot': options.get('pivot', False)
        }
        
        # Choose template based on model type
        template_name = 'pivot_model' if options.get('pivot', False) else 'model'
        template_content = self.get_template(template_name)
        
        # Render template
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/models/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_migration(self, name: str, **options) -> bool:
        """Generate migration for the model."""
        from .migration_generator import MigrationGenerator
        
        migration_gen = MigrationGenerator()
        table_name = options.get('table', self.get_table_name(self.get_class_name(name)))
        
        migration_options = {
            'create': True,
            'table': table_name,
            'fields': options.get('fields', []),
            'force': options.get('force', False)
        }
        
        migration_name = f"create_{table_name}_table"
        return migration_gen.generate(migration_name, **migration_options)
    
    def _generate_factory(self, name: str, **options) -> bool:
        """Generate factory for the model."""
        from .factory_generator import FactoryGenerator
        
        factory_gen = FactoryGenerator()
        return factory_gen.generate(name, **options)
    
    def _generate_seeder(self, name: str, **options) -> bool:
        """Generate seeder for the model."""
        from .seeder_generator import SeederGenerator
        
        seeder_gen = SeederGenerator()
        return seeder_gen.generate(f"{name}Seeder", model=name, **options)
    
    def _generate_controller(self, name: str, resource: bool, api: bool, **options) -> bool:
        """Generate controller for the model."""
        from .controller_generator import ControllerGenerator
        
        controller_gen = ControllerGenerator()
        controller_name = f"{name}Controller"
        
        controller_options = {
            'resource': resource,
            'api': api,
            'model': name,
            'force': options.get('force', False)
        }
        
        return controller_gen.generate(controller_name, **controller_options)
    
    def _format_fillable(self, fillable: List[str]) -> str:
        """Format fillable array for template."""
        if not fillable:
            return "[]"
        
        formatted_items = [f"'{item}'" for item in fillable]
        return f"[{', '.join(formatted_items)}]"
    
    def _format_hidden(self, hidden: List[str]) -> str:
        """Format hidden array for template."""
        if not hidden:
            return "[]"
        
        formatted_items = [f"'{item}'" for item in hidden]
        return f"[{', '.join(formatted_items)}]"
    
    def _format_casts(self, casts: Dict[str, str]) -> str:
        """Format casts dictionary for template."""
        if not casts:
            return "{}"
        
        formatted_items = [f"'{key}': '{value}'" for key, value in casts.items()]
        return f"{{{', '.join(formatted_items)}}}"
    
    def _generate_relationships(self, relationships: List[Dict[str, str]]) -> str:
        """Generate relationship methods."""
        if not relationships:
            return ""
        
        methods = []
        for rel in relationships:
            method = self._generate_relationship_method(rel)
            if method:
                methods.append(method)
        
        return '\n'.join(methods)
    
    def _generate_relationship_method(self, relationship: Dict[str, str]) -> str:
        """Generate a single relationship method."""
        rel_type = relationship.get('type', 'belongs_to')
        model = relationship.get('model')
        method_name = relationship.get('name', self.get_snake_case(model))
        
        if not model:
            return ""
        
        docstring = self.format_docstring(
            f"Get the associated {model}.",
            returns=f"{rel_type.replace('_', ' ').title()} relationship"
        )
        
        if rel_type == 'belongs_to':
            return f"""
{docstring}
    def {method_name}(self):
        return self.belongs_to('{model}')"""
        
        elif rel_type == 'has_one':
            return f"""
{docstring}
    def {method_name}(self):
        return self.has_one('{model}')"""
        
        elif rel_type == 'has_many':
            return f"""
{docstring}
    def {method_name}(self):
        return self.has_many('{model}')"""
        
        elif rel_type == 'belongs_to_many':
            return f"""
{docstring}
    def {method_name}(self):
        return self.belongs_to_many('{model}')"""
        
        return ""
    
    def _load_templates(self):
        """Load model templates."""
        self.templates['model'] = '''"""
{{class_name}} Model

Larapy model for {{table_name}} table.
"""

from larapy.database.larapy.model import Model
from typing import List, Dict, Any, Optional


class {{class_name}}(Model):
    """
    {{class_name}} model for database operations.
    
    This model represents the {{class_name.lower()}} entity in the database.
    """
    
    # Table name
    table = '{{table_name}}'
    
    # Enable/disable timestamps
    timestamps = {{timestamps}}
    
    # Mass assignment protection
    fillable = {{fillable}}
    
    # Hidden attributes for serialization
    hidden = {{hidden}}
    
    # Attribute casting
    casts = {{casts}}{{relationships}}
    
    def __str__(self):
        """String representation of the model."""
        return f"{{class_name}}({{self.get_key()}})"
    
    def __repr__(self):
        """Detailed string representation."""
        return f"{{class_name}}({{dict(self.attributes)}})"
'''

        self.templates['pivot_model'] = '''"""
{{class_name}} Pivot Model

Pivot model for many-to-many relationships.
"""

from larapy.database.larapy.model import Model
from larapy.database.larapy.relations.pivot import Pivot


class {{class_name}}(Pivot):
    """
    {{class_name}} pivot model.
    
    This model represents the pivot table for many-to-many relationships.
    """
    
    # Table name
    table = '{{table_name}}'
    
    # Enable/disable timestamps
    timestamps = {{timestamps}}
    
    # Mass assignment protection
    fillable = {{fillable}}
    
    # Hidden attributes for serialization
    hidden = {{hidden}}
    
    # Attribute casting
    casts = {{casts}}
    
    def __str__(self):
        """String representation of the pivot model."""
        return f"{{class_name}}({{self.get_key()}})"
'''