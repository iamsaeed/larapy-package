"""
View helpers and utilities for Larapy templates.

Provides helper functions for forms, URLs, assets, and common template operations.
"""

import html
import urllib.parse
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


class ViewHelpers:
    """Collection of view helper functions."""
    
    @staticmethod
    def escape(text: str) -> str:
        """Escape HTML characters."""
        if text is None:
            return ''
        return html.escape(str(text))
    
    @staticmethod
    def raw(text: str) -> str:
        """Return raw unescaped text."""
        return str(text) if text is not None else ''
    
    @staticmethod
    def url(path: str, params: Dict[str, Any] = None) -> str:
        """Generate a URL."""
        if params:
            query_string = urllib.parse.urlencode(params)
            return f"{path}?{query_string}"
        return path
    
    @staticmethod
    def route(name: str, params: Dict[str, Any] = None) -> str:
        """Generate URL for named route."""
        # This would integrate with routing system
        # For now, return simple placeholder
        url = f"/{name}"
        if params:
            query_string = urllib.parse.urlencode(params)
            url += f"?{query_string}"
        return url
    
    @staticmethod
    def asset(path: str, version: str = None) -> str:
        """Generate asset URL with optional versioning."""
        asset_url = f"/assets/{path.lstrip('/')}"
        if version:
            separator = '&' if '?' in asset_url else '?'
            asset_url += f"{separator}v={version}"
        return asset_url
    
    @staticmethod
    def csrf_token() -> str:
        """Generate CSRF token."""
        # This would integrate with CSRF protection middleware
        return "csrf_token_placeholder"
    
    @staticmethod
    def csrf_field() -> str:
        """Generate CSRF hidden input field."""
        token = ViewHelpers.csrf_token()
        return f'<input type="hidden" name="_token" value="{token}">'
    
    @staticmethod
    def method_field(method: str) -> str:
        """Generate method spoofing field for forms."""
        if method.upper() in ['PUT', 'PATCH', 'DELETE']:
            return f'<input type="hidden" name="_method" value="{method.upper()}">'
        return ''
    
    @staticmethod
    def old(key: str, default: Any = '') -> Any:
        """Get old input value for form repopulation."""
        # This would integrate with session/request handling
        return default
    
    @staticmethod
    def errors(key: str = None) -> Union[List[str], Dict[str, List[str]]]:
        """Get validation errors."""
        # This would integrate with validation system
        if key:
            return []
        return {}
    
    @staticmethod
    def has_error(key: str) -> bool:
        """Check if field has validation error."""
        return False  # Placeholder
    
    @staticmethod
    def error_class(key: str, class_name: str = 'is-invalid') -> str:
        """Return CSS class if field has error."""
        return class_name if ViewHelpers.has_error(key) else ''


class FormHelpers:
    """Helper functions for forms."""
    
    @staticmethod
    def form_open(action: str = '', method: str = 'POST', 
                  attributes: Dict[str, str] = None) -> str:
        """Open a form tag."""
        attrs = attributes or {}
        method = method.upper()
        
        # Handle method spoofing
        actual_method = 'POST' if method in ['PUT', 'PATCH', 'DELETE'] else method
        
        attr_str = ' '.join([f'{k}="{v}"' for k, v in attrs.items()])
        form_tag = f'<form method="{actual_method}"'
        
        if action:
            form_tag += f' action="{action}"'
        
        if attr_str:
            form_tag += f' {attr_str}'
        
        form_tag += '>'
        
        # Add CSRF and method fields
        hidden_fields = ViewHelpers.csrf_field()
        if method in ['PUT', 'PATCH', 'DELETE']:
            hidden_fields += ViewHelpers.method_field(method)
        
        return form_tag + hidden_fields
    
    @staticmethod
    def form_close() -> str:
        """Close a form tag."""
        return '</form>'
    
    @staticmethod
    def label(name: str, text: str = None, attributes: Dict[str, str] = None) -> str:
        """Generate a label tag."""
        attrs = attributes or {}
        display_text = text or name.replace('_', ' ').title()
        
        attr_str = ' '.join([f'{k}="{v}"' for k, v in attrs.items()])
        attr_part = f' {attr_str}' if attr_str else ''
        
        return f'<label for="{name}"{attr_part}>{display_text}</label>'
    
    @staticmethod
    def text(name: str, value: str = None, attributes: Dict[str, str] = None) -> str:
        """Generate a text input."""
        attrs = attributes or {}
        value = value or ViewHelpers.old(name, '')
        
        default_attrs = {
            'type': 'text',
            'name': name,
            'id': name,
            'value': value
        }
        
        # Add error class if needed
        if ViewHelpers.has_error(name):
            css_class = attrs.get('class', '')
            attrs['class'] = f"{css_class} {ViewHelpers.error_class(name)}".strip()
        
        final_attrs = {**default_attrs, **attrs}
        attr_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])
        
        return f'<input {attr_str}>'
    
    @staticmethod
    def password(name: str, attributes: Dict[str, str] = None) -> str:
        """Generate a password input."""
        attrs = attributes or {}
        attrs['type'] = 'password'
        return FormHelpers.text(name, '', attrs)
    
    @staticmethod
    def email(name: str, value: str = None, attributes: Dict[str, str] = None) -> str:
        """Generate an email input."""
        attrs = attributes or {}
        attrs['type'] = 'email'
        return FormHelpers.text(name, value, attrs)
    
    @staticmethod
    def hidden(name: str, value: str = '') -> str:
        """Generate a hidden input."""
        return f'<input type="hidden" name="{name}" value="{value}">'
    
    @staticmethod
    def textarea(name: str, value: str = None, attributes: Dict[str, str] = None) -> str:
        """Generate a textarea."""
        attrs = attributes or {}
        value = value or ViewHelpers.old(name, '')
        
        default_attrs = {
            'name': name,
            'id': name
        }
        
        # Add error class if needed
        if ViewHelpers.has_error(name):
            css_class = attrs.get('class', '')
            attrs['class'] = f"{css_class} {ViewHelpers.error_class(name)}".strip()
        
        final_attrs = {**default_attrs, **attrs}
        attr_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])
        
        return f'<textarea {attr_str}>{ViewHelpers.escape(value)}</textarea>'
    
    @staticmethod
    def select(name: str, options: Dict[str, str], selected: str = None,
               attributes: Dict[str, str] = None) -> str:
        """Generate a select dropdown."""
        attrs = attributes or {}
        selected = selected or ViewHelpers.old(name, '')
        
        default_attrs = {
            'name': name,
            'id': name
        }
        
        # Add error class if needed
        if ViewHelpers.has_error(name):
            css_class = attrs.get('class', '')
            attrs['class'] = f"{css_class} {ViewHelpers.error_class(name)}".strip()
        
        final_attrs = {**default_attrs, **attrs}
        attr_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])
        
        option_html = []
        for value, text in options.items():
            selected_attr = ' selected' if str(value) == str(selected) else ''
            option_html.append(f'<option value="{value}"{selected_attr}>{text}</option>')
        
        return f'<select {attr_str}>{"".join(option_html)}</select>'
    
    @staticmethod
    def checkbox(name: str, value: str = '1', checked: bool = None,
                 attributes: Dict[str, str] = None) -> str:
        """Generate a checkbox input."""
        attrs = attributes or {}
        is_checked = checked if checked is not None else ViewHelpers.old(name) == value
        
        default_attrs = {
            'type': 'checkbox',
            'name': name,
            'id': name,
            'value': value
        }
        
        if is_checked:
            default_attrs['checked'] = 'checked'
        
        final_attrs = {**default_attrs, **attrs}
        attr_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])
        
        return f'<input {attr_str}>'
    
    @staticmethod
    def radio(name: str, value: str, checked: bool = None,
              attributes: Dict[str, str] = None) -> str:
        """Generate a radio button."""
        attrs = attributes or {}
        is_checked = checked if checked is not None else ViewHelpers.old(name) == value
        
        default_attrs = {
            'type': 'radio',
            'name': name,
            'value': value
        }
        
        if is_checked:
            default_attrs['checked'] = 'checked'
        
        final_attrs = {**default_attrs, **attrs}
        attr_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])
        
        return f'<input {attr_str}>'
    
    @staticmethod
    def submit(text: str = 'Submit', attributes: Dict[str, str] = None) -> str:
        """Generate a submit button."""
        attrs = attributes or {}
        
        default_attrs = {
            'type': 'submit',
            'value': text
        }
        
        final_attrs = {**default_attrs, **attrs}
        attr_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])
        
        return f'<input {attr_str}>'
    
    @staticmethod
    def button(text: str, attributes: Dict[str, str] = None) -> str:
        """Generate a button."""
        attrs = attributes or {}
        
        default_attrs = {
            'type': 'button'
        }
        
        final_attrs = {**default_attrs, **attrs}
        attr_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])
        
        return f'<button {attr_str}>{text}</button>'


class AssetHelpers:
    """Helper functions for assets."""
    
    @staticmethod
    def css(path: str, attributes: Dict[str, str] = None) -> str:
        """Generate CSS link tag."""
        attrs = attributes or {}
        
        default_attrs = {
            'rel': 'stylesheet',
            'href': ViewHelpers.asset(path),
            'type': 'text/css'
        }
        
        final_attrs = {**default_attrs, **attrs}
        attr_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])
        
        return f'<link {attr_str}>'
    
    @staticmethod
    def js(path: str, attributes: Dict[str, str] = None) -> str:
        """Generate JavaScript script tag."""
        attrs = attributes or {}
        
        default_attrs = {
            'src': ViewHelpers.asset(path),
            'type': 'text/javascript'
        }
        
        final_attrs = {**default_attrs, **attrs}
        attr_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])
        
        return f'<script {attr_str}></script>'
    
    @staticmethod
    def image(path: str, alt: str = '', attributes: Dict[str, str] = None) -> str:
        """Generate image tag."""
        attrs = attributes or {}
        
        default_attrs = {
            'src': ViewHelpers.asset(path),
            'alt': alt
        }
        
        final_attrs = {**default_attrs, **attrs}
        attr_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])
        
        return f'<img {attr_str}>'


class DateHelpers:
    """Helper functions for dates."""
    
    @staticmethod
    def format_date(date: datetime, format_str: str = '%Y-%m-%d') -> str:
        """Format a date."""
        if not date:
            return ''
        return date.strftime(format_str)
    
    @staticmethod
    def human_date(date: datetime) -> str:
        """Format date in human-readable format."""
        if not date:
            return ''
        return date.strftime('%B %d, %Y')
    
    @staticmethod
    def time_ago(date: datetime) -> str:
        """Get time ago string."""
        if not date:
            return ''
        
        now = datetime.now()
        diff = now - date
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"


class StringHelpers:
    """Helper functions for strings."""
    
    @staticmethod
    def truncate(text: str, length: int = 100, suffix: str = '...') -> str:
        """Truncate text to specified length."""
        if not text:
            return ''
        
        text = str(text)
        if len(text) <= length:
            return text
        
        return text[:length].rstrip() + suffix
    
    @staticmethod
    def word_limit(text: str, words: int = 10, suffix: str = '...') -> str:
        """Limit text to specified number of words."""
        if not text:
            return ''
        
        word_list = str(text).split()
        if len(word_list) <= words:
            return text
        
        return ' '.join(word_list[:words]) + suffix
    
    @staticmethod
    def title_case(text: str) -> str:
        """Convert text to title case."""
        if not text:
            return ''
        return str(text).title()
    
    @staticmethod
    def snake_case(text: str) -> str:
        """Convert text to snake_case."""
        if not text:
            return ''
        
        import re
        text = str(text)
        # Replace spaces and dashes with underscores
        text = re.sub(r'[-\s]+', '_', text)
        # Insert underscore before capital letters
        text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text)
        return text.lower()


class PaginationHelpers:
    """Helper functions for pagination."""
    
    @staticmethod
    def pagination_links(current_page: int, total_pages: int, 
                        base_url: str = '', window: int = 3) -> str:
        """Generate pagination links."""
        if total_pages <= 1:
            return ''
        
        links = ['<nav><ul class="pagination">']
        
        # Previous link
        if current_page > 1:
            prev_url = f"{base_url}?page={current_page - 1}"
            links.append(f'<li class="page-item"><a class="page-link" href="{prev_url}">Previous</a></li>')
        
        # Page numbers
        start = max(1, current_page - window)
        end = min(total_pages, current_page + window)
        
        for page in range(start, end + 1):
            active_class = ' active' if page == current_page else ''
            page_url = f"{base_url}?page={page}"
            links.append(f'<li class="page-item{active_class}"><a class="page-link" href="{page_url}">{page}</a></li>')
        
        # Next link
        if current_page < total_pages:
            next_url = f"{base_url}?page={current_page + 1}"
            links.append(f'<li class="page-item"><a class="page-link" href="{next_url}">Next</a></li>')
        
        links.append('</ul></nav>')
        
        return ''.join(links)