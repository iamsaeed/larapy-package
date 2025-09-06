# Larapy

A Python framework inspired by Laravel, providing Laravel-like functionality for Python web development, including dependency injection, routing, HTTP handling, database ORM, authentication, middleware, and more.

## Features

- 🚀 **Fast & Modern**: Built with modern Python features and best practices
- 🛣️ **Laravel-inspired Routing**: Familiar routing syntax and functionality
- 🏗️ **Dependency Injection**: Powerful IoC container for service management
- 📊 **Database ORM**: Eloquent-like ORM for database interactions
- 🔐 **Authentication**: Built-in authentication system
- 🔧 **Middleware**: Request/response middleware pipeline
- 🎨 **View Engine**: Flexible template rendering system
- ⚡ **CLI Tools**: Artisan-like command line interface

## Installation

### Install from GitHub

```bash
pip install git+https://github.com/yourusername/larapy-package.git
```

### Development Installation

```bash
git clone https://github.com/yourusername/larapy-package.git
cd larapy-package
pip install -e .
```

## Quick Start

```python
from larapy import Application, Route, Request, Response

# Create application
app = Application()

# Define routes
@Route.get('/')
def home(request: Request) -> Response:
    return Response("Hello, Larapy!")

# Run the application
if __name__ == '__main__':
    app.run()
```

## 🐍 Python Naming Conventions (PEP 8)

This project strictly follows PEP 8 naming conventions to ensure consistency and readability:

### **Naming Standards**
- **Modules/Files**: `snake_case.py` (e.g., `user_controller.py`, `auth_manager.py`)
- **Directories**: `snake_case/` (e.g., `http/`, `controllers/`, `middleware/`)
- **Classes**: `PascalCase` (e.g., `UserController`, `DatabaseManager`, `AuthenticationGuard`)
- **Functions/Methods**: `snake_case` (e.g., `get_user_data()`, `register_routes()`, `authenticate_user()`)
- **Variables**: `snake_case` (e.g., `user_name`, `total_amount`, `is_authenticated`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_CONNECTIONS`, `DEFAULT_TIMEOUT`, `SECRET_KEY`)
- **Private Methods**: `_leading_underscore` (e.g., `_internal_method()`, `_validate_token()`)

### **Laravel Compatibility Note**
While Laravel uses PascalCase for directories (e.g., `Http/Controllers/`), we follow Python's PEP 8 convention of snake_case for all module and directory names. This ensures consistency with Python ecosystem standards while maintaining Laravel's familiar structure and functionality.

### **Code Style Examples**
```python
# Good - PEP 8 compliant
from larapy.auth.guards.jwt_guard import JwtGuard
from larapy.http.middleware.cors_middleware import CorsMiddleware

class UserController:
    MAX_LOGIN_ATTEMPTS = 3
    
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self._session_timeout = 3600
    
    def authenticate_user(self, user_name, password):
        is_valid = self._validate_credentials(user_name, password)
        return self._create_session() if is_valid else None
    
    def _validate_credentials(self, user_name, password):
        # Private method implementation
        pass
```

## CLI Usage

Larapy comes with a powerful CLI tool for development:

```bash
# Start development server
larapy serve

# Generate code
larapy make:controller UserController
larapy make:model User --migration
larapy make:middleware AuthMiddleware

# Database management
larapy db:migrate
larapy db:seed
larapy db:rollback

# Environment management
larapy env:status
larapy env:init production

# Configuration
larapy config:show
larapy config:publish auth
```

## Requirements

- Python 3.8+
- click >= 8.0.0

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Documentation

For full documentation, visit our [documentation site](https://github.com/yourusername/larapy-package#readme).