"""
Migration Generator

Generates database migration files for Larapy applications.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from .base_generator import BaseGenerator


class MigrationGenerator(BaseGenerator):
    """Generates database migration files."""
    
    def __init__(self):
        super().__init__()
        self._load_templates()
    
    def generate(self, name: str, **options) -> bool:
        """
        Generate a migration file.
        
        Args:
            name: Migration name
            **options: Generation options
            
        Returns:
            True if generation was successful
        """
        # Determine migration type
        create = options.get('create', False)
        table = options.get('table', None)
        
        if create and table:
            return self._generate_create_migration(name, table, **options)
        elif table:
            return self._generate_table_migration(name, table, **options)
        else:
            return self._generate_blank_migration(name, **options)
    
    def _generate_create_migration(self, name: str, table: str, **options) -> bool:
        """Generate a create table migration."""
        class_name = self._get_migration_class_name(name)
        
        # Set template variables
        variables = {
            'class_name': class_name,
            'table_name': table,
            'fields': self._generate_fields(options.get('fields', [])),
            'indexes': self._generate_indexes(options.get('indexes', [])),
            'foreign_keys': self._generate_foreign_keys(options.get('foreign_keys', []))
        }
        
        # Render template
        template_content = self.get_template('create_migration')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_name = self.get_migration_name(name)
        file_path = f"database/migrations/{file_name}"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_table_migration(self, name: str, table: str, **options) -> bool:
        """Generate a table modification migration."""
        class_name = self._get_migration_class_name(name)
        
        # Set template variables
        variables = {
            'class_name': class_name,
            'table_name': table,
            'up_operations': self._generate_up_operations(options),
            'down_operations': self._generate_down_operations(options)
        }
        
        # Render template
        template_content = self.get_template('table_migration')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_name = self.get_migration_name(name)
        file_path = f"database/migrations/{file_name}"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_blank_migration(self, name: str, **options) -> bool:
        """Generate a blank migration."""
        class_name = self._get_migration_class_name(name)
        
        # Set template variables
        variables = {
            'class_name': class_name,
            'description': options.get('description', 'Custom migration operations')
        }
        
        # Render template
        template_content = self.get_template('blank_migration')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_name = self.get_migration_name(name)
        file_path = f"database/migrations/{file_name}"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _get_migration_class_name(self, name: str) -> str:
        """Get migration class name from migration name."""
        # Remove timestamp prefix if present
        clean_name = name.split('_', 4)[-1] if '_' in name else name
        return self.get_class_name(clean_name)
    
    def _generate_fields(self, fields: List[Dict[str, Any]]) -> str:
        """Generate field definitions."""
        if not fields:
            return self._get_default_fields()
        
        field_lines = []
        for field in fields:
            field_line = self._generate_field(field)
            if field_line:
                field_lines.append(f"            {field_line}")
        
        return '\n'.join(field_lines)
    
    def _get_default_fields(self) -> str:
        """Get default fields for a new table."""
        return """            table.id()
            table.timestamps()"""
    
    def _generate_field(self, field: Dict[str, Any]) -> str:
        """Generate a single field definition."""
        name = field.get('name')
        field_type = field.get('type', 'string')
        nullable = field.get('nullable', False)
        default = field.get('default')
        length = field.get('length')
        
        if not name:
            return ""
        
        # Start with field type
        if field_type == 'string' and length:
            field_def = f"table.string('{name}', {length})"
        elif field_type in ['integer', 'int']:
            field_def = f"table.integer('{name}')"
        elif field_type in ['bigint', 'big_integer']:
            field_def = f"table.big_integer('{name}')"
        elif field_type in ['text']:
            field_def = f"table.text('{name}')"
        elif field_type in ['boolean', 'bool']:
            field_def = f"table.boolean('{name}')"
        elif field_type in ['datetime', 'timestamp']:
            field_def = f"table.datetime('{name}')"
        elif field_type == 'date':
            field_def = f"table.date('{name}')"
        elif field_type == 'time':
            field_def = f"table.time('{name}')"
        elif field_type in ['decimal', 'numeric']:
            precision = field.get('precision', 8)
            scale = field.get('scale', 2)
            field_def = f"table.decimal('{name}', {precision}, {scale})"
        elif field_type in ['float', 'double']:
            field_def = f"table.{field_type}('{name}')"
        elif field_type == 'json':
            field_def = f"table.json('{name}')"
        else:
            field_def = f"table.string('{name}')"
        
        # Add nullable
        if nullable:
            field_def += ".nullable()"
        
        # Add default
        if default is not None:
            if isinstance(default, str):
                field_def += f".default('{default}')"
            elif isinstance(default, bool):
                field_def += f".default({str(default).lower()})"
            else:
                field_def += f".default({default})"
        
        return field_def
    
    def _generate_indexes(self, indexes: List[Dict[str, Any]]) -> str:
        """Generate index definitions."""
        if not indexes:
            return ""
        
        index_lines = []
        for index in indexes:
            index_line = self._generate_index(index)
            if index_line:
                index_lines.append(f"            {index_line}")
        
        return '\n' + '\n'.join(index_lines) if index_lines else ""
    
    def _generate_index(self, index: Dict[str, Any]) -> str:
        """Generate a single index definition."""
        columns = index.get('columns', [])
        index_type = index.get('type', 'index')
        name = index.get('name')
        
        if not columns:
            return ""
        
        if isinstance(columns, str):
            columns = [columns]
        
        columns_str = ', '.join(f"'{col}'" for col in columns)
        
        if index_type == 'unique':
            return f"table.unique([{columns_str}])"
        elif index_type == 'primary':
            return f"table.primary([{columns_str}])"
        else:
            if name:
                return f"table.index([{columns_str}], '{name}')"
            else:
                return f"table.index([{columns_str}])"
    
    def _generate_foreign_keys(self, foreign_keys: List[Dict[str, Any]]) -> str:
        """Generate foreign key constraints."""
        if not foreign_keys:
            return ""
        
        fk_lines = []
        for fk in foreign_keys:
            fk_line = self._generate_foreign_key(fk)
            if fk_line:
                fk_lines.append(f"            {fk_line}")
        
        return '\n' + '\n'.join(fk_lines) if fk_lines else ""
    
    def _generate_foreign_key(self, fk: Dict[str, Any]) -> str:
        """Generate a single foreign key constraint."""
        column = fk.get('column')
        references = fk.get('references', 'id')
        on_table = fk.get('on')
        on_delete = fk.get('on_delete', 'restrict')
        on_update = fk.get('on_update', 'restrict')
        
        if not column or not on_table:
            return ""
        
        fk_def = f"table.foreign('{column}').references('{references}').on('{on_table}')"
        
        if on_delete != 'restrict':
            fk_def += f".on_delete('{on_delete}')"
        
        if on_update != 'restrict':
            fk_def += f".on_update('{on_update}')"
        
        return fk_def
    
    def _generate_up_operations(self, options: Dict[str, Any]) -> str:
        """Generate up operations for table migration."""
        operations = []
        
        # Add columns
        if 'add_columns' in options:
            for field in options['add_columns']:
                field_def = self._generate_field(field)
                if field_def:
                    operations.append(f"            {field_def}")
        
        # Drop columns
        if 'drop_columns' in options:
            for column in options['drop_columns']:
                operations.append(f"            table.drop_column('{column}')")
        
        # Modify columns
        if 'modify_columns' in options:
            for field in options['modify_columns']:
                field_def = self._generate_field(field)
                if field_def:
                    operations.append(f"            {field_def}.change()")
        
        # Add indexes
        if 'add_indexes' in options:
            for index in options['add_indexes']:
                index_def = self._generate_index(index)
                if index_def:
                    operations.append(f"            {index_def}")
        
        return '\n'.join(operations) if operations else "            pass"
    
    def _generate_down_operations(self, options: Dict[str, Any]) -> str:
        """Generate down operations for table migration."""
        operations = []
        
        # Reverse add columns (drop them)
        if 'add_columns' in options:
            for field in options['add_columns']:
                operations.append(f"            table.drop_column('{field['name']}')")
        
        # Reverse drop columns (add them back)
        if 'drop_columns' in options:
            # This would need the original column definitions
            pass
        
        # Reverse modify columns
        if 'modify_columns' in options:
            # This would need the original column definitions
            pass
        
        return '\n'.join(operations) if operations else "            pass"
    
    def _load_templates(self):
        """Load migration templates."""
        self.templates['create_migration'] = '''"""
Create {{table_name}} table migration.
"""

from larapy.database.migrations.migration import Migration
from larapy.database.migrations.schema import Schema, Blueprint


class {{class_name}}(Migration):
    """
    Run the migrations.
    
    @return void
    """
    
    def up(self):
        """
        Run the migrations.
        
        @return void
        """
        def create_{{table_name}}_table(table: Blueprint):
{{fields}}{{indexes}}{{foreign_keys}}
        
        Schema.create('{{table_name}}', create_{{table_name}}_table)
    
    def down(self):
        """
        Reverse the migrations.
        
        @return void
        """
        Schema.drop_if_exists('{{table_name}}')
'''

        self.templates['table_migration'] = '''"""
{{class_name}} migration.
"""

from larapy.database.migrations.migration import Migration
from larapy.database.migrations.schema import Schema, Blueprint


class {{class_name}}(Migration):
    """
    Run the migrations.
    
    @return void
    """
    
    def up(self):
        """
        Run the migrations.
        
        @return void
        """
        def modify_{{table_name}}_table(table: Blueprint):
{{up_operations}}
        
        Schema.table('{{table_name}}', modify_{{table_name}}_table)
    
    def down(self):
        """
        Reverse the migrations.
        
        @return void
        """
        def reverse_{{table_name}}_table(table: Blueprint):
{{down_operations}}
        
        Schema.table('{{table_name}}', reverse_{{table_name}}_table)
'''

        self.templates['blank_migration'] = '''"""
{{class_name}} migration.
"""

from larapy.database.migrations.migration import Migration
from larapy.database.migrations.schema import Schema, Blueprint


class {{class_name}}(Migration):
    """
    Run the migrations.
    
    @return void
    """
    
    def up(self):
        """
        Run the migrations.
        
        @return void
        """
        # Add your migration logic here
        # Example:
        # def create_example_table(table: Blueprint):
        #     table.id()
        #     table.string('name')
        #     table.timestamps()
        # 
        # Schema.create('example', create_example_table)
        pass
    
    def down(self):
        """
        Reverse the migrations.
        
        @return void
        """
        # Add your rollback logic here
        # Example:
        # Schema.drop_if_exists('example')
        pass
'''