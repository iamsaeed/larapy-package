"""
Component system for Larapy views.

Provides reusable UI components with slots, attributes, and data binding.
"""

from typing import Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod


class Component(ABC):
    """Base class for view components."""
    
    def __init__(self, **attributes):
        """
        Initialize component with attributes.
        
        Args:
            **attributes: Component attributes
        """
        self.attributes = attributes
        self.slots: Dict[str, str] = {}
        
    @abstractmethod
    def render(self) -> str:
        """Render the component to HTML."""
        pass
    
    def with_slot(self, name: str, content: str) -> 'Component':
        """Add slot content to component."""
        self.slots[name] = content
        return self
    
    def attribute(self, name: str, default: Any = None) -> Any:
        """Get component attribute value."""
        return self.attributes.get(name, default)
    
    def has_attribute(self, name: str) -> bool:
        """Check if component has attribute."""
        return name in self.attributes
    
    def slot(self, name: str, default: str = '') -> str:
        """Get slot content."""
        return self.slots.get(name, default)
    
    def has_slot(self, name: str) -> bool:
        """Check if component has slot."""
        return name in self.slots
    
    def view(self, template: str, data: Dict[str, Any] = None):
        """Render a view template from component."""
        from .view import view_manager
        
        component_data = {
            'attributes': self.attributes,
            'slots': self.slots,
            **(data or {})
        }
        
        return view_manager.render(template, component_data)
    
    def __str__(self) -> str:
        return self.render()


class AlertComponent(Component):
    """Alert component for displaying messages."""
    
    def render(self) -> str:
        """Render alert component."""
        alert_type = self.attribute('type', 'info')
        message = self.attribute('message', '')
        dismissible = self.attribute('dismissible', False)
        
        css_classes = f"alert alert-{alert_type}"
        if dismissible:
            css_classes += " alert-dismissible"
        
        dismiss_button = ""
        if dismissible:
            dismiss_button = '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>'
        
        return f"""
        <div class="{css_classes}" role="alert">
            {message}
            {self.slot('default')}
            {dismiss_button}
        </div>
        """.strip()


class CardComponent(Component):
    """Card component for content containers."""
    
    def render(self) -> str:
        """Render card component."""
        title = self.attribute('title', '')
        subtitle = self.attribute('subtitle', '')
        
        header_html = ""
        if title:
            header_html = f"""
            <div class="card-header">
                <h5 class="card-title">{title}</h5>
                {f'<h6 class="card-subtitle mb-2 text-muted">{subtitle}</h6>' if subtitle else ''}
            </div>
            """
        
        footer_html = ""
        if self.has_slot('footer'):
            footer_html = f'<div class="card-footer">{self.slot("footer")}</div>'
        
        return f"""
        <div class="card">
            {header_html}
            <div class="card-body">
                {self.slot('default')}
            </div>
            {footer_html}
        </div>
        """.strip()


class ButtonComponent(Component):
    """Button component."""
    
    def render(self) -> str:
        """Render button component."""
        button_type = self.attribute('type', 'button')
        variant = self.attribute('variant', 'primary')
        size = self.attribute('size', '')
        disabled = self.attribute('disabled', False)
        href = self.attribute('href')
        
        css_classes = f"btn btn-{variant}"
        if size:
            css_classes += f" btn-{size}"
        
        attributes = []
        if disabled:
            attributes.append('disabled')
        
        content = self.slot('default', self.attribute('text', 'Button'))
        
        if href:
            # Render as link
            disabled_class = ' disabled' if disabled else ''
            return f'<a href="{href}" class="{css_classes}{disabled_class}">{content}</a>'
        else:
            # Render as button
            attr_str = ' '.join(attributes)
            return f'<button type="{button_type}" class="{css_classes}" {attr_str}>{content}</button>'


class FormComponent(Component):
    """Form component with CSRF protection."""
    
    def render(self) -> str:
        """Render form component."""
        method = self.attribute('method', 'POST').upper()
        action = self.attribute('action', '')
        enctype = self.attribute('enctype', '')
        
        # Handle method spoofing for PUT/PATCH/DELETE
        actual_method = 'POST' if method in ['PUT', 'PATCH', 'DELETE'] else method
        method_field = ''
        
        if method in ['PUT', 'PATCH', 'DELETE']:
            method_field = f'<input type="hidden" name="_method" value="{method}">'
        
        # Add CSRF token for state-changing methods
        csrf_field = ''
        if actual_method == 'POST':
            csrf_field = '<input type="hidden" name="_token" value="{{ csrf_token() }}">'
        
        enctype_attr = f' enctype="{enctype}"' if enctype else ''
        action_attr = f' action="{action}"' if action else ''
        
        return f"""
        <form method="{actual_method}"{action_attr}{enctype_attr}>
            {csrf_field}
            {method_field}
            {self.slot('default')}
        </form>
        """.strip()


class ComponentRegistry:
    """Registry for managing components."""
    
    def __init__(self):
        self.components: Dict[str, type] = {}
        self.aliases: Dict[str, str] = {}
        self._register_builtin_components()
    
    def register(self, name: str, component_class: type, alias: str = None):
        """
        Register a component.
        
        Args:
            name: Component name
            component_class: Component class
            alias: Optional alias name
        """
        if not issubclass(component_class, Component):
            raise ValueError("Component class must extend Component")
        
        self.components[name] = component_class
        
        if alias:
            self.aliases[alias] = name
    
    def make(self, name: str, **attributes) -> Optional[Component]:
        """
        Create component instance.
        
        Args:
            name: Component name
            **attributes: Component attributes
            
        Returns:
            Component instance or None if not found
        """
        # Check aliases first
        component_name = self.aliases.get(name, name)
        
        if component_name not in self.components:
            return None
        
        component_class = self.components[component_name]
        return component_class(**attributes)
    
    def exists(self, name: str) -> bool:
        """Check if component exists."""
        component_name = self.aliases.get(name, name)
        return component_name in self.components
    
    def get_registered(self) -> List[str]:
        """Get list of registered component names."""
        return list(self.components.keys())
    
    def _register_builtin_components(self):
        """Register built-in components."""
        self.register('alert', AlertComponent)
        self.register('card', CardComponent) 
        self.register('button', ButtonComponent, 'btn')
        self.register('form', FormComponent)


# Global component registry
component_registry = ComponentRegistry()


def component(name: str, **attributes) -> Optional[Component]:
    """Helper function to create a component."""
    return component_registry.make(name, **attributes)


def register_component(name: str, component_class: type, alias: str = None):
    """Helper function to register a component."""
    component_registry.register(name, component_class, alias)


class DynamicComponent(Component):
    """Component that can render different components dynamically."""
    
    def __init__(self, component_name: str, **attributes):
        """
        Initialize dynamic component.
        
        Args:
            component_name: Name of component to render
            **attributes: Attributes to pass to component
        """
        super().__init__(**attributes)
        self.component_name = component_name
    
    def render(self) -> str:
        """Render the dynamic component."""
        component_instance = component_registry.make(self.component_name, **self.attributes)
        
        if not component_instance:
            return f"<!-- Component '{self.component_name}' not found -->"
        
        # Pass along any slots
        for slot_name, content in self.slots.items():
            component_instance.with_slot(slot_name, content)
        
        return component_instance.render()


class ComponentCollection:
    """Collection of components for bulk operations."""
    
    def __init__(self):
        self.components: List[Component] = []
    
    def add(self, component: Component):
        """Add component to collection."""
        self.components.append(component)
    
    def render_all(self) -> str:
        """Render all components."""
        return ''.join(comp.render() for comp in self.components)
    
    def filter_by_type(self, component_type: type) -> List[Component]:
        """Filter components by type."""
        return [comp for comp in self.components if isinstance(comp, component_type)]
    
    def count(self) -> int:
        """Get component count."""
        return len(self.components)
    
    def clear(self):
        """Clear all components."""
        self.components.clear()