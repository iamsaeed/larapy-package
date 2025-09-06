"""
Seeder Generator

Generates database seeder classes for Larapy applications.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from .base_generator import BaseGenerator


class SeederGenerator(BaseGenerator):
    """Generates database seeder classes."""
    
    def __init__(self):
        super().__init__()
        self._load_templates()
    
    def generate(self, name: str, **options) -> bool:
        """
        Generate a seeder class.
        
        Args:
            name: Seeder name
            **options: Generation options
            
        Returns:
            True if generation was successful
        """
        class_name = self.get_class_name(name)
        if not class_name.endswith('Seeder'):
            class_name += 'Seeder'
        
        # Determine seeder type
        model = options.get('model')
        if model:
            return self._generate_model_seeder(class_name, model, **options)
        else:
            return self._generate_blank_seeder(class_name, **options)
    
    def _generate_model_seeder(self, class_name: str, model: str, **options) -> bool:
        """Generate a model seeder."""
        model_class = self.get_class_name(model)
        table_name = options.get('table', self.get_table_name(model_class))
        
        # Set template variables
        variables = {
            'class_name': class_name,
            'model_class': model_class,
            'model_import': f"from app.models.{self.get_snake_case(model_class)} import {model_class}",
            'table_name': table_name,
            'sample_data': self._generate_sample_data(model_class, options),
            'count': options.get('count', 10),
            'use_factory': options.get('factory', False)
        }
        
        # Choose template based on whether to use factory
        template_name = 'model_factory_seeder' if options.get('factory', False) else 'model_seeder'
        template_content = self.get_template(template_name)
        
        # Render template
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"database/seeders/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_blank_seeder(self, class_name: str, **options) -> bool:
        """Generate a blank seeder."""
        # Set template variables
        variables = {
            'class_name': class_name,
            'description': options.get('description', f"{class_name} seeder for custom database seeding")
        }
        
        # Render template
        template_content = self.get_template('blank_seeder')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"database/seeders/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_sample_data(self, model_class: str, options: Dict[str, Any]) -> str:
        """Generate sample data for the model."""
        # Get custom data if provided
        custom_data = options.get('data', [])
        if custom_data:
            return self._format_custom_data(custom_data)
        
        # Generate basic sample data based on common patterns
        sample_records = []
        count = min(options.get('count', 3), 5)  # Limit sample data in template
        
        for i in range(1, count + 1):
            record = self._generate_sample_record(model_class, i)
            sample_records.append(record)
        
        return self._format_sample_records(sample_records)
    
    def _generate_sample_record(self, model_class: str, index: int) -> Dict[str, Any]:
        """Generate a sample record for the model."""
        # Basic patterns based on model name
        model_lower = model_class.lower()
        
        record = {}
        
        # Common fields based on model type
        if 'user' in model_lower:
            record.update({
                'name': f"User {index}",
                'email': f"user{index}@example.com",
                'password': "password123"
            })
        elif 'post' in model_lower or 'article' in model_lower:
            record.update({
                'title': f"Sample Post {index}",
                'content': f"This is the content for post {index}.",
                'status': 'published' if index % 2 == 1 else 'draft'
            })
        elif 'product' in model_lower:
            record.update({
                'name': f"Product {index}",
                'description': f"Description for product {index}",
                'price': 99.99 + index,
                'in_stock': True
            })
        elif 'category' in model_lower:
            record.update({
                'name': f"Category {index}",
                'description': f"Description for category {index}",
                'slug': f"category-{index}"
            })
        else:
            # Generic sample data
            record.update({
                'name': f"{model_class} {index}",
                'description': f"Sample description for {model_class} {index}"
            })
        
        return record
    
    def _format_custom_data(self, data: List[Dict[str, Any]]) -> str:
        """Format custom data for template."""
        formatted_records = []
        for record in data:
            formatted_record = self._format_record(record)
            formatted_records.append(formatted_record)
        
        return ',\n            '.join(formatted_records)
    
    def _format_sample_records(self, records: List[Dict[str, Any]]) -> str:
        """Format sample records for template."""
        formatted_records = []
        for record in records:
            formatted_record = self._format_record(record)
            formatted_records.append(formatted_record)
        
        return ',\n            '.join(formatted_records)
    
    def _format_record(self, record: Dict[str, Any]) -> str:
        """Format a single record for template."""
        items = []
        for key, value in record.items():
            if isinstance(value, str):
                items.append(f"'{key}': '{value}'")
            elif isinstance(value, bool):
                items.append(f"'{key}': {str(value).lower()}")
            elif isinstance(value, (int, float)):
                items.append(f"'{key}': {value}")
            else:
                items.append(f"'{key}': '{value}'")
        
        return f"{{{', '.join(items)}}}"
    
    def _load_templates(self):
        """Load seeder templates."""
        self.templates['model_seeder'] = '''"""
{{class_name}} Database Seeder

Seeds the {{table_name}} table with sample data.
"""

{{model_import}}
from larapy.database.seeder import Seeder


class {{class_name}}(Seeder):
    """{{class_name}} for seeding {{table_name}} table."""
    
    def run(self):
        """Run the database seeder."""
        # Sample data for {{model_class}}
        sample_data = [
            {{sample_data}}
        ]
        
        # Insert sample data
        for data in sample_data:
            {{model_class}}.create(data)
        
        self.command.info(f"Seeded {{{{len(sample_data)}}}} {{model_class.lower()}} records")
'''

        self.templates['model_factory_seeder'] = '''"""
{{class_name}} Database Seeder

Seeds the {{table_name}} table using model factory.
"""

{{model_import}}
from larapy.database.seeder import Seeder


class {{class_name}}(Seeder):
    """{{class_name}} for seeding {{table_name}} table using factory."""
    
    def run(self):
        """Run the database seeder."""
        # Create {{count}} {{model_class}} records using factory
        {{model_class}}.factory().count({{count}}).create()
        
        self.command.info(f"Seeded {{count}} {{model_class.lower()}} records using factory")
'''

        self.templates['blank_seeder'] = '''"""
{{class_name}} Database Seeder

{{description}}
"""

from larapy.database.seeder import Seeder


class {{class_name}}(Seeder):
    """{{class_name}} for custom database seeding."""
    
    def run(self):
        """Run the database seeder."""
        # Add your seeding logic here
        
        # Example: Insert data directly
        # self.db.table('your_table').insert([
        #     {'column1': 'value1', 'column2': 'value2'},
        #     {'column1': 'value3', 'column2': 'value4'},
        # ])
        
        # Example: Use raw SQL
        # self.db.statement(\"\"\"
        #     INSERT INTO your_table (column1, column2) VALUES
        #     ('value1', 'value2'),
        #     ('value3', 'value4')
        # \"\"\")
        
        self.command.info("{{class_name}} completed")
'''