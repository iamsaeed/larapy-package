"""
Component Generator

Generates view components for Larapy applications.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from .base_generator import BaseGenerator


class ComponentGenerator(BaseGenerator):
    """Generates view component classes."""
    
    def __init__(self):
        super().__init__()
        self._load_templates()
    
    def generate(self, name: str, **options) -> bool:
        """
        Generate a component class.
        
        Args:
            name: Component name
            **options: Generation options
            
        Returns:
            True if generation was successful
        """
        class_name = self.get_class_name(name)
        
        # Generate component class
        success = self._generate_component_class(class_name, **options)
        
        # Generate component template if requested
        if success and options.get('template', True):
            success &= self._generate_component_template(class_name, **options)
        
        return success
    
    def _generate_component_class(self, class_name: str, **options) -> bool:
        """Generate the component class."""
        component_type = options.get('type', 'basic')
        
        if component_type == 'form':
            return self._generate_form_component(class_name, **options)
        elif component_type == 'data':
            return self._generate_data_component(class_name, **options)
        elif component_type == 'layout':
            return self._generate_layout_component(class_name, **options)
        else:
            return self._generate_basic_component(class_name, **options)
    
    def _generate_basic_component(self, class_name: str, **options) -> bool:
        """Generate a basic component."""
        # Set template variables
        variables = {
            'class_name': class_name,
            'component_name': self.get_kebab_case(class_name),
            'properties': self._generate_properties(options.get('props', [])),
            'data_method': self._generate_data_method(options.get('data', {})),
            'methods': self._generate_component_methods(options.get('methods', []))
        }
        
        # Render template
        template_content = self.get_template('basic_component')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/view/components/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_form_component(self, class_name: str, **options) -> bool:
        """Generate a form component."""
        # Set template variables
        variables = {
            'class_name': class_name,
            'component_name': self.get_kebab_case(class_name),
            'form_method': options.get('method', 'POST'),
            'form_action': options.get('action', ''),
            'fields': self._generate_form_fields(options.get('fields', [])),
            'validation_rules': self._generate_validation_rules(options.get('validation', {}))
        }
        
        # Render template
        template_content = self.get_template('form_component')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/view/components/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_data_component(self, class_name: str, **options) -> bool:
        """Generate a data component."""
        # Set template variables
        variables = {
            'class_name': class_name,
            'component_name': self.get_kebab_case(class_name),
            'data_source': options.get('data_source', 'database'),
            'model': options.get('model', ''),
            'query_method': self._generate_query_method(options),
            'pagination': options.get('pagination', False),
            'per_page': options.get('per_page', 15)
        }
        
        # Render template
        template_content = self.get_template('data_component')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/view/components/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_layout_component(self, class_name: str, **options) -> bool:
        """Generate a layout component."""
        # Set template variables
        variables = {
            'class_name': class_name,
            'component_name': self.get_kebab_case(class_name),
            'slots': self._generate_slots(options.get('slots', ['default'])),
            'layout_data': self._generate_layout_data(options)
        }
        
        # Render template
        template_content = self.get_template('layout_component')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/view/components/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_component_template(self, class_name: str, **options) -> bool:
        """Generate the component template."""
        component_type = options.get('type', 'basic')
        
        # Set template variables
        variables = {
            'class_name': class_name,
            'component_name': self.get_kebab_case(class_name),
            'template_content': self._get_template_content(component_type, **options)
        }
        
        # Render template
        if component_type == 'form':
            template_content = self.get_template('form_template')
        elif component_type == 'data':
            template_content = self.get_template('data_template')
        elif component_type == 'layout':
            template_content = self.get_template('layout_template')
        else:
            template_content = self.get_template('basic_template')
        
        content = self.render_template(template_content, variables)
        
        # Write file
        component_dir = f"resources/views/components"
        file_path = f"{component_dir}/{self.get_kebab_case(class_name)}.html"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_properties(self, props: List[Dict[str, Any]]) -> str:
        """Generate component properties."""
        if not props:
            return ""
        
        prop_lines = []
        for prop in props:
            prop_line = self._generate_property(prop)
            if prop_line:
                prop_lines.append(prop_line)
        
        return '\n    '.join(prop_lines)
    
    def _generate_property(self, prop: Dict[str, Any]) -> str:
        """Generate a single property."""
        name = prop.get('name')
        prop_type = prop.get('type', 'str')
        default = prop.get('default')
        required = prop.get('required', False)
        
        if not name:
            return ""
        
        type_annotation = f": {prop_type}"
        
        if default is not None:
            if isinstance(default, str):
                default_value = f" = '{default}'"
            else:
                default_value = f" = {default}"
        elif not required:
            default_value = f" = None"
        else:
            default_value = ""
        
        return f"{name}{type_annotation}{default_value}"
    
    def _generate_data_method(self, data: Dict[str, Any]) -> str:
        """Generate data method content."""
        if not data:
            return "return {}"
        
        data_items = []
        for key, value in data.items():
            if isinstance(value, str):
                data_items.append(f"'{key}': '{value}'")
            else:
                data_items.append(f"'{key}': {value}")
        
        return f"return {{\n            {',\n            '.join(data_items)}\n        }}"
    
    def _generate_component_methods(self, methods: List[Dict[str, str]]) -> str:
        """Generate component methods."""
        if not methods:
            return ""
        
        method_lines = []
        for method_config in methods:
            method = self._generate_method(method_config)
            if method:
                method_lines.append(method)
        
        return '\n'.join(method_lines)
    
    def _generate_method(self, method_config: Dict[str, str]) -> str:
        """Generate a single method."""
        method_name = method_config.get('name')
        description = method_config.get('description', f"Custom method {method_name}")
        parameters = method_config.get('parameters', 'self')
        body = method_config.get('body', 'pass')
        
        if not method_name:
            return ""
        
        docstring = self.format_docstring(description)
        
        return f"""
{docstring}
    def {method_name}({parameters}):
        {body}"""
    
    def _generate_form_fields(self, fields: List[Dict[str, str]]) -> str:
        """Generate form fields for form component."""
        if not fields:
            return "[]"
        
        field_definitions = []
        for field in fields:
            field_def = self._generate_form_field(field)
            if field_def:
                field_definitions.append(field_def)
        
        return f"[{', '.join(field_definitions)}]"
    
    def _generate_form_field(self, field: Dict[str, str]) -> str:
        """Generate a single form field definition."""
        name = field.get('name')
        field_type = field.get('type', 'text')
        label = field.get('label', name.replace('_', ' ').title() if name else '')
        required = field.get('required', False)
        
        if not name:
            return ""
        
        return f"{{'name': '{name}', 'type': '{field_type}', 'label': '{label}', 'required': {str(required).lower()}}}"
    
    def _generate_validation_rules(self, validation: Dict[str, str]) -> str:
        """Generate validation rules."""
        if not validation:
            return "{}"
        
        rules = []
        for field, rule in validation.items():
            rules.append(f"'{field}': '{rule}'")
        
        return f"{{{', '.join(rules)}}}"
    
    def _generate_query_method(self, options: Dict[str, Any]) -> str:
        """Generate query method for data component."""
        model = options.get('model', 'Model')
        filters = options.get('filters', {})
        order_by = options.get('order_by')
        
        query_parts = [f"{model}.query()"]
        
        # Add filters
        for field, value in filters.items():
            query_parts.append(f".where('{field}', '{value}')")
        
        # Add ordering
        if order_by:
            query_parts.append(f".order_by('{order_by}')")
        
        if options.get('pagination', False):
            per_page = options.get('per_page', 15)
            query_parts.append(f".paginate({per_page})")
        else:
            query_parts.append(".get()")
        
        return ''.join(query_parts)
    
    def _generate_slots(self, slots: List[str]) -> str:
        """Generate slot definitions."""
        slot_definitions = []
        for slot in slots:
            slot_definitions.append(f"'{slot}'")
        
        return f"[{', '.join(slot_definitions)}]"
    
    def _generate_layout_data(self, options: Dict[str, Any]) -> str:
        """Generate layout-specific data."""
        layout_data = options.get('layout_data', {})
        
        if not layout_data:
            return "return {}"
        
        data_items = []
        for key, value in layout_data.items():
            if isinstance(value, str):
                data_items.append(f"'{key}': '{value}'")
            else:
                data_items.append(f"'{key}': {value}")
        
        return f"return {{\n            {',\n            '.join(data_items)}\n        }}"
    
    def _get_template_content(self, component_type: str, **options) -> str:
        """Get template content based on component type."""
        if component_type == 'form':
            return self._get_form_template_content(**options)
        elif component_type == 'data':
            return self._get_data_template_content(**options)
        elif component_type == 'layout':
            return self._get_layout_template_content(**options)
        else:
            return '<div class="component">\n    <!-- Component content goes here -->\n    <p>{{component_name}} component</p>\n</div>'
    
    def _get_form_template_content(self, **options) -> str:
        """Get form template content."""
        return '''<form method="{{form_method}}" action="{{form_action}}" class="component-form">
    {% for field in fields %}
    <div class="form-group">
        <label for="{{field.name}}">{{field.label}}</label>
        <input type="{{field.type}}" 
               id="{{field.name}}" 
               name="{{field.name}}" 
               {% if field.required %}required{% endif %}
               class="form-control">
    </div>
    {% endfor %}
    
    <button type="submit" class="btn btn-primary">Submit</button>
</form>'''
    
    def _get_data_template_content(self, **options) -> str:
        """Get data template content."""
        return '''<div class="data-component">
    {% if items %}
        <div class="items">
            {% for item in items %}
            <div class="item">
                <!-- Customize item display -->
                {{item}}
            </div>
            {% endfor %}
        </div>
        
        {% if pagination %}
        <div class="pagination">
            {{pagination.render()}}
        </div>
        {% endif %}
    {% else %}
        <p class="no-data">No items found.</p>
    {% endif %}
</div>'''
    
    def _get_layout_template_content(self, **options) -> str:
        """Get layout template content."""
        return '''<div class="layout-component">
    <header class="component-header">
        {% block header %}
        <h1>{{title|default('Page Title')}}</h1>
        {% endblock %}
    </header>
    
    <main class="component-main">
        {% block content %}
        {{slot}}
        {% endblock %}
    </main>
    
    <footer class="component-footer">
        {% block footer %}
        <!-- Footer content -->
        {% endblock %}
    </footer>
</div>'''
    
    def _load_templates(self):
        """Load component templates."""
        self.templates['basic_component'] = '''"""
{{class_name}} View Component

Basic view component for {{component_name}}.
"""

from larapy.view.component import Component
from typing import Dict, Any


class {{class_name}}(Component):
    """{{class_name}} view component."""
    
    def __init__(self{{properties and ', ' + properties or ''}}):
        """
        Initialize the component.
        
        Args:{{properties and '\n            ' + properties.replace('\n    ', '\n            ') or ''}}
        """{{properties and '\n        ' + '\n        '.join(f'self.{prop.split(":")[0].strip()} = {prop.split(":")[0].strip()}' for prop in properties.split('\n') if prop.strip()) or ''}}
        super().__init__()
    
    def render(self):
        """Render the component."""
        return self.view('components.{{component_name}}', self.data())
    
    def data(self):
        """Get component data."""
        {{data_method}}{{methods}}
'''

        self.templates['form_component'] = '''"""
{{class_name}} Form Component

Form component for {{component_name}}.
"""

from larapy.view.component import Component
from larapy.http.request import Request
from typing import Dict, Any, List


class {{class_name}}(Component):
    """{{class_name}} form component."""
    
    def __init__(self, method='{{form_method}}', action='{{form_action}}'):
        """
        Initialize the form component.
        
        Args:
            method: HTTP method for the form
            action: Form action URL
        """
        self.method = method
        self.action = action
        self.fields = {{fields}}
        self.validation_rules = {{validation_rules}}
        super().__init__()
    
    def render(self):
        """Render the component."""
        return self.view('components.{{component_name}}', self.data())
    
    def data(self):
        """Get component data."""
        return {
            'form_method': self.method,
            'form_action': self.action,
            'fields': self.fields,
            'validation_rules': self.validation_rules
        }
    
    def validate(self, request: Request) -> Dict[str, List[str]]:
        """
        Validate form data.
        
        Args:
            request: HTTP request with form data
            
        Returns:
            Dictionary of validation errors
        """
        errors = {}
        
        for field_name, rules in self.validation_rules.items():
            value = request.input(field_name)
            field_errors = self._validate_field(field_name, value, rules)
            if field_errors:
                errors[field_name] = field_errors
        
        return errors
    
    def _validate_field(self, field_name: str, value: Any, rules: str) -> List[str]:
        """Validate a single field."""
        errors = []
        rule_list = [rule.strip() for rule in rules.split('|')]
        
        for rule in rule_list:
            if rule == 'required' and not value:
                errors.append(f"{field_name} is required")
            elif rule.startswith('min:') and value:
                min_length = int(rule.split(':')[1])
                if len(str(value)) < min_length:
                    errors.append(f"{field_name} must be at least {min_length} characters")
            elif rule.startswith('max:') and value:
                max_length = int(rule.split(':')[1])
                if len(str(value)) > max_length:
                    errors.append(f"{field_name} must not exceed {max_length} characters")
        
        return errors
'''

        self.templates['data_component'] = '''"""
{{class_name}} Data Component

Data component for {{component_name}}.
"""

from larapy.view.component import Component
from typing import Dict, Any


class {{class_name}}(Component):
    """{{class_name}} data component."""
    
    def __init__(self, per_page={{per_page}}):
        """
        Initialize the data component.
        
        Args:
            per_page: Number of items per page for pagination
        """
        self.per_page = per_page
        super().__init__()
    
    def render(self):
        """Render the component."""
        return self.view('components.{{component_name}}', self.data())
    
    def data(self):
        """Get component data."""
        return {
            'items': self.get_items(),
            'pagination': {{pagination}}
        }
    
    def get_items(self):
        """Get data items."""
        # {{query_method}}
        
        # Placeholder implementation
        return []
'''

        self.templates['layout_component'] = '''"""
{{class_name}} Layout Component

Layout component for {{component_name}}.
"""

from larapy.view.component import Component
from typing import Dict, Any, List


class {{class_name}}(Component):
    """{{class_name}} layout component."""
    
    def __init__(self, title=None):
        """
        Initialize the layout component.
        
        Args:
            title: Page title for the layout
        """
        self.title = title
        self.slots = {{slots}}
        super().__init__()
    
    def render(self):
        """Render the component."""
        return self.view('components.{{component_name}}', self.data())
    
    def data(self):
        """Get component data."""
        {{layout_data}}
'''

        # Template files
        self.templates['basic_template'] = '''<!-- {{class_name}} Component Template -->
{{template_content}}'''

        self.templates['form_template'] = '''<!-- {{class_name}} Form Component Template -->
{{template_content}}'''

        self.templates['data_template'] = '''<!-- {{class_name}} Data Component Template -->
{{template_content}}'''

        self.templates['layout_template'] = '''<!-- {{class_name}} Layout Component Template -->
{{template_content}}'''