"""
Factory Generator

Generates model factory classes for Larapy applications.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from .base_generator import BaseGenerator


class FactoryGenerator(BaseGenerator):
    """Generates model factory classes."""
    
    def __init__(self):
        super().__init__()
        self._load_templates()
    
    def generate(self, name: str, **options) -> bool:
        """
        Generate a factory class.
        
        Args:
            name: Model name or factory name
            **options: Generation options
            
        Returns:
            True if generation was successful
        """
        # Determine model name and factory name
        if name.endswith('Factory'):
            factory_name = name
            model_name = name[:-7]  # Remove 'Factory' suffix
        else:
            model_name = name
            factory_name = f"{name}Factory"
        
        model_class = self.get_class_name(model_name)
        factory_class = self.get_class_name(factory_name)
        
        # Set template variables
        variables = {
            'factory_class': factory_class,
            'model_class': model_class,
            'model_import': f"from app.models.{self.get_snake_case(model_class)} import {model_class}",
            'factory_definition': self._generate_factory_definition(model_class, options),
            'states': self._generate_states(options.get('states', {})),
            'relationships': self._generate_factory_relationships(options.get('relationships', []))
        }
        
        # Render template
        template_content = self.get_template('factory')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"database/factories/{self.get_snake_case(factory_class)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_factory_definition(self, model_class: str, options: Dict[str, Any]) -> str:
        """Generate the factory definition method."""
        # Get custom definition if provided
        custom_definition = options.get('definition')
        if custom_definition:
            return self._format_custom_definition(custom_definition)
        
        # Generate definition based on model name patterns
        return self._generate_default_definition(model_class)
    
    def _generate_default_definition(self, model_class: str) -> str:
        """Generate default factory definition based on model name."""
        model_lower = model_class.lower()
        
        fields = []
        
        # Common patterns based on model type
        if 'user' in model_lower:
            fields.extend([
                "'name': fake.name()",
                "'email': fake.unique().email()",
                "'password': fake.password(length=12)",
                "'email_verified_at': fake.date_time_between(start_date='-1y', end_date='now')",
                "'created_at': fake.date_time_between(start_date='-1y', end_date='now')",
                "'updated_at': fake.date_time_between(start_date='-6m', end_date='now')"
            ])
        
        elif 'post' in model_lower or 'article' in model_lower:
            fields.extend([
                "'title': fake.sentence(nb_words=4)",
                "'slug': fake.slug()",
                "'content': fake.text(max_nb_chars=2000)",
                "'excerpt': fake.text(max_nb_chars=200)",
                "'status': fake.random_element(['draft', 'published', 'archived'])",
                "'published_at': fake.date_time_between(start_date='-1y', end_date='now')",
                "'created_at': fake.date_time_between(start_date='-1y', end_date='now')",
                "'updated_at': fake.date_time_between(start_date='-6m', end_date='now')"
            ])
        
        elif 'product' in model_lower:
            fields.extend([
                "'name': fake.word().capitalize() + ' ' + fake.word().capitalize()",
                "'description': fake.text(max_nb_chars=500)",
                "'sku': fake.unique().bothify(text='SKU-########')",
                "'price': fake.pydecimal(left_digits=3, right_digits=2, positive=True)",
                "'cost': fake.pydecimal(left_digits=2, right_digits=2, positive=True)",
                "'stock_quantity': fake.random_int(min=0, max=100)",
                "'in_stock': fake.boolean(chance_of_getting_true=80)",
                "'created_at': fake.date_time_between(start_date='-1y', end_date='now')",
                "'updated_at': fake.date_time_between(start_date='-6m', end_date='now')"
            ])
        
        elif 'category' in model_lower:
            fields.extend([
                "'name': fake.word().capitalize()",
                "'slug': fake.slug()",
                "'description': fake.text(max_nb_chars=300)",
                "'sort_order': fake.random_int(min=1, max=100)",
                "'is_active': fake.boolean(chance_of_getting_true=90)",
                "'created_at': fake.date_time_between(start_date='-1y', end_date='now')",
                "'updated_at': fake.date_time_between(start_date='-6m', end_date='now')"
            ])
        
        elif 'comment' in model_lower:
            fields.extend([
                "'content': fake.text(max_nb_chars=500)",
                "'author_name': fake.name()",
                "'author_email': fake.email()",
                "'is_approved': fake.boolean(chance_of_getting_true=75)",
                "'created_at': fake.date_time_between(start_date='-1y', end_date='now')",
                "'updated_at': fake.date_time_between(start_date='-6m', end_date='now')"
            ])
        
        elif 'order' in model_lower:
            fields.extend([
                "'order_number': fake.unique().bothify(text='ORD-########')",
                "'total_amount': fake.pydecimal(left_digits=4, right_digits=2, positive=True)",
                "'status': fake.random_element(['pending', 'processing', 'shipped', 'delivered', 'cancelled'])",
                "'currency': fake.currency_code()",
                "'notes': fake.text(max_nb_chars=200)",
                "'created_at': fake.date_time_between(start_date='-1y', end_date='now')",
                "'updated_at': fake.date_time_between(start_date='-6m', end_date='now')"
            ])
        
        else:
            # Generic fields
            fields.extend([
                "'name': fake.word().capitalize()",
                "'description': fake.text(max_nb_chars=300)",
                "'created_at': fake.date_time_between(start_date='-1y', end_date='now')",
                "'updated_at': fake.date_time_between(start_date='-6m', end_date='now')"
            ])
        
        # Format as dictionary
        formatted_fields = ',\n            '.join(fields)
        return f"""{{
            {formatted_fields}
        }}"""
    
    def _format_custom_definition(self, definition: Dict[str, str]) -> str:
        """Format custom factory definition."""
        fields = []
        for field_name, faker_expression in definition.items():
            fields.append(f"'{field_name}': {faker_expression}")
        
        formatted_fields = ',\n            '.join(fields)
        return f"""{{
            {formatted_fields}
        }}"""
    
    def _generate_states(self, states: Dict[str, Dict[str, str]]) -> str:
        """Generate factory states."""
        if not states:
            return ""
        
        state_methods = []
        for state_name, state_definition in states.items():
            state_method = self._generate_state_method(state_name, state_definition)
            state_methods.append(state_method)
        
        return '\n'.join(state_methods)
    
    def _generate_state_method(self, state_name: str, state_definition: Dict[str, str]) -> str:
        """Generate a single state method."""
        method_name = self.get_snake_case(state_name)
        
        # Format state fields
        fields = []
        for field_name, faker_expression in state_definition.items():
            fields.append(f"'{field_name}': {faker_expression}")
        
        formatted_fields = ',\n            '.join(fields)
        
        docstring = self.format_docstring(
            f"Create {state_name} state for the model.",
            returns="Factory instance with state applied"
        )
        
        return f"""
{docstring}
    def {method_name}(self):
        return self.state({{
            {formatted_fields}
        }})"""
    
    def _generate_factory_relationships(self, relationships: List[Dict[str, str]]) -> str:
        """Generate factory relationship methods."""
        if not relationships:
            return ""
        
        relationship_methods = []
        for rel in relationships:
            rel_method = self._generate_relationship_method(rel)
            if rel_method:
                relationship_methods.append(rel_method)
        
        return '\n'.join(relationship_methods)
    
    def _generate_relationship_method(self, relationship: Dict[str, str]) -> str:
        """Generate a factory relationship method."""
        rel_name = relationship.get('name')
        rel_factory = relationship.get('factory')
        rel_type = relationship.get('type', 'belongs_to')
        
        if not rel_name or not rel_factory:
            return ""
        
        method_name = f"with_{self.get_snake_case(rel_name)}"
        factory_class = self.get_class_name(rel_factory)
        
        if rel_type == 'belongs_to':
            docstring = self.format_docstring(
                f"Create factory with associated {rel_name}.",
                returns="Factory instance with relationship"
            )
            
            return f"""
{docstring}
    def {method_name}(self, {self.get_snake_case(rel_name)}=None):
        if {self.get_snake_case(rel_name)} is None:
            {self.get_snake_case(rel_name)} = {factory_class}.create()
        
        return self.state({{
            '{self.get_snake_case(rel_name)}_id': {self.get_snake_case(rel_name)}.id
        }})"""
        
        elif rel_type == 'has_many':
            docstring = self.format_docstring(
                f"Create factory that will have {rel_name} after creation.",
                args=[('count', 'Number of related records to create')],
                returns="Factory instance"
            )
            
            return f"""
{docstring}
    def with_{self.get_snake_case(rel_name)}(self, count=3):
        return self.after_creating(lambda model: 
            {factory_class}.count(count).create({{'{self.get_snake_case(rel_name.rstrip('s'))}_id': model.id}}))"""
        
        return ""
    
    def _load_templates(self):
        """Load factory templates."""
        self.templates['factory'] = '''"""
{{model_class}} Factory

Model factory for generating {{model_class}} instances.
"""

{{model_import}}
from larapy.database.factories.factory import Factory
from faker import Faker

fake = Faker()


class {{factory_class}}(Factory):
    """{{factory_class}} for creating {{model_class}} instances."""
    
    model = {{model_class}}
    
    def definition(self):
        """Define the model's default state."""
        return {{factory_definition}}{{states}}{{relationships}}
    
    def configure(self):
        """Configure the factory."""
        return self.after_making(self._after_making).after_creating(self._after_creating)
    
    def _after_making(self, model):
        """Callback after making a model instance."""
        # Add any logic that should run after making (but not persisting) a model
        pass
    
    def _after_creating(self, model):
        """Callback after creating a model instance."""
        # Add any logic that should run after creating (persisting) a model
        pass
'''