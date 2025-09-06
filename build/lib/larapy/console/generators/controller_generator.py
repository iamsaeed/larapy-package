"""
Controller Generator

Generates controller classes for Larapy applications.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from .base_generator import BaseGenerator


class ControllerGenerator(BaseGenerator):
    """Generates controller classes."""
    
    def __init__(self):
        super().__init__()
        self._load_templates()
    
    def generate(self, name: str, **options) -> bool:
        """
        Generate a controller class.
        
        Args:
            name: Controller name
            **options: Generation options
            
        Returns:
            True if generation was successful
        """
        class_name = self.get_class_name(name)
        if not class_name.endswith('Controller'):
            class_name += 'Controller'
        
        # Determine controller type
        resource = options.get('resource', False)
        api = options.get('api', False)
        
        if resource:
            return self._generate_resource_controller(class_name, api, **options)
        else:
            return self._generate_basic_controller(class_name, **options)
    
    def _generate_basic_controller(self, class_name: str, **options) -> bool:
        """Generate a basic controller."""
        # Set template variables
        variables = {
            'class_name': class_name,
            'description': options.get('description', f"{class_name} for handling HTTP requests"),
            'model': options.get('model', ''),
            'methods': self._generate_custom_methods(options.get('methods', []))
        }
        
        # Render template
        template_content = self.get_template('basic_controller')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/http/controllers/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_resource_controller(self, class_name: str, api: bool, **options) -> bool:
        """Generate a resource controller."""
        model = options.get('model', '')
        model_class = self.get_class_name(model) if model else ''
        
        # Set template variables
        variables = {
            'class_name': class_name,
            'model_class': model_class,
            'model_import': f"from app.models.{self.get_snake_case(model_class)} import {model_class}" if model_class else "",
            'model_variable': self.get_snake_case(model_class) if model_class else 'item',
            'model_plural': self.get_plural(self.get_snake_case(model_class)) if model_class else 'items',
            'is_api': api,
            'resource_methods': self._generate_resource_methods(model_class, api, **options)
        }
        
        # Choose template
        template_name = 'api_resource_controller' if api else 'web_resource_controller'
        template_content = self.get_template(template_name)
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/http/controllers/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_resource_methods(self, model_class: str, api: bool, **options) -> str:
        """Generate resource controller methods."""
        model_variable = self.get_snake_case(model_class) if model_class else 'item'
        model_plural = self.get_plural(model_variable)
        
        methods = []
        
        # Index method
        if api:
            methods.append(f'''
    def index(self, request: Request) -> JsonResponse:
        """
        Display a listing of the resource.
        
        Args:
            request: The HTTP request
            
        Returns:
            JSON response with resource list
        """
        {model_plural} = {model_class}.all() if "{model_class}" else []
        
        return JsonResponse({{
            'data': [{model_variable}.to_dict() for {model_variable} in {model_plural}],
            'message': 'Resources retrieved successfully'
        }})''')
        else:
            methods.append(f'''
    def index(self, request: Request) -> Response:
        """
        Display a listing of the resource.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response with resource list view
        """
        {model_plural} = {model_class}.all() if "{model_class}" else []
        
        return view_response('{model_plural}.index', {{
            '{model_plural}': {model_plural}
        }})''')
        
        # Show method
        if api:
            methods.append(f'''
    def show(self, request: Request, id: str) -> JsonResponse:
        """
        Display the specified resource.
        
        Args:
            request: The HTTP request
            id: Resource ID
            
        Returns:
            JSON response with resource data
        """
        {model_variable} = {model_class}.find(id) if "{model_class}" else None
        
        if not {model_variable}:
            return JsonResponse({{
                'error': 'Resource not found'
            }}, status=404)
        
        return JsonResponse({{
            'data': {model_variable}.to_dict(),
            'message': 'Resource retrieved successfully'
        }})''')
        else:
            methods.append(f'''
    def show(self, request: Request, id: str) -> Response:
        """
        Display the specified resource.
        
        Args:
            request: The HTTP request
            id: Resource ID
            
        Returns:
            Response with resource view
        """
        {model_variable} = {model_class}.find(id) if "{model_class}" else None
        
        if not {model_variable}:
            return Response('Resource not found', status=404)
        
        return view_response('{model_plural}.show', {{
            '{model_variable}': {model_variable}
        }})''')
        
        # Create method (for web controllers)
        if not api:
            methods.append(f'''
    def create(self, request: Request) -> Response:
        """
        Show the form for creating a new resource.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response with create form
        """
        return view_response('{model_plural}.create')''')
        
        # Store method
        if api:
            methods.append(f'''
    def store(self, request: Request) -> JsonResponse:
        """
        Store a newly created resource.
        
        Args:
            request: The HTTP request with form data
            
        Returns:
            JSON response with created resource
        """
        # Validate request data
        data = request.json()
        
        # Create resource
        {model_variable} = {model_class}.create(data) if "{model_class}" else None
        
        if not {model_variable}:
            return JsonResponse({{
                'error': 'Failed to create resource'
            }}, status=500)
        
        return JsonResponse({{
            'data': {model_variable}.to_dict(),
            'message': 'Resource created successfully'
        }}, status=201)''')
        else:
            methods.append(f'''
    def store(self, request: Request) -> Response:
        """
        Store a newly created resource.
        
        Args:
            request: The HTTP request with form data
            
        Returns:
            Redirect response
        """
        # Validate request data
        data = request.input()
        
        # Create resource
        {model_variable} = {model_class}.create(data) if "{model_class}" else None
        
        if not {model_variable}:
            return redirect_response('{model_plural}.create').with_error('Failed to create resource')
        
        return redirect_response('{model_plural}.show', id={model_variable}.id).with_success('Resource created successfully')''')
        
        # Edit method (for web controllers)
        if not api:
            methods.append(f'''
    def edit(self, request: Request, id: str) -> Response:
        """
        Show the form for editing the specified resource.
        
        Args:
            request: The HTTP request
            id: Resource ID
            
        Returns:
            Response with edit form
        """
        {model_variable} = {model_class}.find(id) if "{model_class}" else None
        
        if not {model_variable}:
            return Response('Resource not found', status=404)
        
        return view_response('{model_plural}.edit', {{
            '{model_variable}': {model_variable}
        }})''')
        
        # Update method
        if api:
            methods.append(f'''
    def update(self, request: Request, id: str) -> JsonResponse:
        """
        Update the specified resource.
        
        Args:
            request: The HTTP request with form data
            id: Resource ID
            
        Returns:
            JSON response with updated resource
        """
        {model_variable} = {model_class}.find(id) if "{model_class}" else None
        
        if not {model_variable}:
            return JsonResponse({{
                'error': 'Resource not found'
            }}, status=404)
        
        # Update resource
        data = request.json()
        {model_variable}.update(data)
        
        return JsonResponse({{
            'data': {model_variable}.to_dict(),
            'message': 'Resource updated successfully'
        }})''')
        else:
            methods.append(f'''
    def update(self, request: Request, id: str) -> Response:
        """
        Update the specified resource.
        
        Args:
            request: The HTTP request with form data
            id: Resource ID
            
        Returns:
            Redirect response
        """
        {model_variable} = {model_class}.find(id) if "{model_class}" else None
        
        if not {model_variable}:
            return Response('Resource not found', status=404)
        
        # Update resource
        data = request.input()
        {model_variable}.update(data)
        
        return redirect_response('{model_plural}.show', id=id).with_success('Resource updated successfully')''')
        
        # Destroy method
        if api:
            methods.append(f'''
    def destroy(self, request: Request, id: str) -> JsonResponse:
        """
        Remove the specified resource.
        
        Args:
            request: The HTTP request
            id: Resource ID
            
        Returns:
            JSON response confirming deletion
        """
        {model_variable} = {model_class}.find(id) if "{model_class}" else None
        
        if not {model_variable}:
            return JsonResponse({{
                'error': 'Resource not found'
            }}, status=404)
        
        # Delete resource
        {model_variable}.delete()
        
        return JsonResponse({{
            'message': 'Resource deleted successfully'
        }})''')
        else:
            methods.append(f'''
    def destroy(self, request: Request, id: str) -> Response:
        """
        Remove the specified resource.
        
        Args:
            request: The HTTP request
            id: Resource ID
            
        Returns:
            Redirect response
        """
        {model_variable} = {model_class}.find(id) if "{model_class}" else None
        
        if not {model_variable}:
            return Response('Resource not found', status=404)
        
        # Delete resource
        {model_variable}.delete()
        
        return redirect_response('{model_plural}.index').with_success('Resource deleted successfully')''')
        
        return ''.join(methods)
    
    def _generate_custom_methods(self, methods: List[Dict[str, str]]) -> str:
        """Generate custom controller methods."""
        if not methods:
            return self._get_default_methods()
        
        method_lines = []
        for method_config in methods:
            method = self._generate_custom_method(method_config)
            if method:
                method_lines.append(method)
        
        return ''.join(method_lines)
    
    def _generate_custom_method(self, method_config: Dict[str, str]) -> str:
        """Generate a single custom method."""
        method_name = method_config.get('name')
        description = method_config.get('description', f"Handle {method_name} request")
        parameters = method_config.get('parameters', 'self, request: Request')
        return_type = method_config.get('return_type', 'Response')
        body = method_config.get('body', 'return Response("Method not implemented")')
        
        if not method_name:
            return ""
        
        docstring = self.format_docstring(
            description,
            args=[('request', 'The HTTP request')],
            returns=f"{return_type} object"
        )
        
        return f"""
{docstring}
    def {method_name}({parameters}) -> {return_type}:
        {body}"""
    
    def _get_default_methods(self) -> str:
        """Get default methods for basic controller."""
        return '''
    def index(self, request: Request) -> Response:
        """
        Display a listing of the resource.
        
        Args:
            request: The HTTP request
            
        Returns:
            HTTP response
        """
        return Response("Index method")
    
    def show(self, request: Request, id: str) -> Response:
        """
        Display the specified resource.
        
        Args:
            request: The HTTP request
            id: Resource ID
            
        Returns:
            HTTP response
        """
        return Response(f"Show method for ID: {id}")'''
    
    def _load_templates(self):
        """Load controller templates."""
        self.templates['basic_controller'] = '''"""
{{class_name}} Controller

{{description}}
"""

from larapy.http.request import Request
from larapy.http.response import Response{{model_class and '\n' + model_import or ''}}


class {{class_name}}:
    """
    {{class_name}} for handling requests.
    """{{methods}}
'''

        self.templates['web_resource_controller'] = '''"""
{{class_name}} Controller

Resource controller for {{model_class}} model.
"""

from larapy.http.request import Request
from larapy.http.response import Response
from larapy.view import view_response
from larapy.http.redirect_response import redirect_response{{model_class and '\n' + model_import or ''}}


class {{class_name}}:
    """
    {{class_name}} for handling {{model_class}} resource requests.
    """{{resource_methods}}
'''

        self.templates['api_resource_controller'] = '''"""
{{class_name}} API Controller

API resource controller for {{model_class}} model.
"""

from larapy.http.request import Request
from larapy.http.response import Response
from larapy.http.json_response import JsonResponse{{model_class and '\n' + model_import or ''}}


class {{class_name}}:
    """
    {{class_name}} for handling {{model_class}} API requests.
    """{{resource_methods}}
'''