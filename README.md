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