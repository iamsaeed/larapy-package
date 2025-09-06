# Larapy CLI Commands Documentation

## Overview

Larapy provides a comprehensive CLI system equivalent to Laravel's Artisan, offering powerful command-line tools for development, code generation, database management, and application configuration. The CLI is accessible via the `larapy` command after installation.

## Installation

To make the `larapy` command available globally, install the package:

```bash
# From the larapy directory
cd /home/ahmad/www/goprofiled.com/larapy
pip install -e .
```

This will install Larapy in development mode and register the `larapy` command in your system.

## Command Categories

### 1. Server Management

#### `larapy serve`
Start the development server (equivalent to `php artisan serve`)

```bash
larapy serve [OPTIONS]

Options:
  --host TEXT       Host to bind to (default: 127.0.0.1)
  --port INTEGER    Port to bind to (default: 8000)
  --reload          Enable auto-reload for development
  --debug           Enable debug mode
```

**Examples:**
```bash
# Start server with defaults
larapy serve

# Start with custom host and port
larapy serve --host 0.0.0.0 --port 3000

# Development mode with auto-reload
larapy serve --reload --debug
```

### 2. Code Generation Commands

#### `larapy make:controller`
Generate a new controller (equivalent to `php artisan make:controller`)

```bash
larapy make:controller NAME [OPTIONS]

Options:
  --resource    Create a resource controller with CRUD methods
  --api         Create an API resource controller (no create/edit methods)
```

**Examples:**
```bash
# Basic controller
larapy make:controller UserController

# Resource controller with all CRUD methods
larapy make:controller PostController --resource

# API controller (no form methods)
larapy make:controller ApiUserController --api
```

**Generated Resource Controller:**
```python
class PostController:
    def index(self, request: Request) -> Response:
        """Display a listing of the resource."""
        
    def create(self, request: Request) -> Response:
        """Show the form for creating a new resource."""
        
    def store(self, request: Request) -> Response:
        """Store a newly created resource."""
        
    def show(self, request: Request, id: str) -> Response:
        """Display the specified resource."""
        
    def edit(self, request: Request, id: str) -> Response:
        """Show the form for editing the specified resource."""
        
    def update(self, request: Request, id: str) -> Response:
        """Update the specified resource."""
        
    def destroy(self, request: Request, id: str) -> Response:
        """Remove the specified resource."""
```

#### `larapy make:model`
Generate a new model (equivalent to `php artisan make:model`)

```bash
larapy make:model NAME [OPTIONS]

Options:
  -m, --migration    Also create a migration file for the model
```

**Examples:**
```bash
# Basic model
larapy make:model User

# Model with migration
larapy make:model Post --migration
```

#### `larapy make:middleware`
Generate a new middleware (equivalent to `php artisan make:middleware`)

```bash
larapy make:middleware NAME
```

**Example:**
```bash
larapy make:middleware AuthMiddleware
```

**Generated Middleware:**
```python
class AuthMiddleware:
    def handle(self, request: Request, next_handler: Callable) -> Response:
        """Handle the incoming request."""
        # Process request before passing to next middleware
        
        # Call the next middleware
        response = next_handler(request)
        
        # Process response after receiving from next middleware
        
        return response
```

### 3. Database Management Commands

#### `larapy db:migrate`
Run database migrations (equivalent to `php artisan migrate`)

```bash
larapy db:migrate [OPTIONS]

Options:
  --seed     Seed the database after migrating
  --force    Force the migration in production
```

**Examples:**
```bash
# Run migrations
larapy db:migrate

# Run migrations and seed
larapy db:migrate --seed

# Force in production
larapy db:migrate --force
```

#### `larapy db:rollback`
Rollback database migrations (equivalent to `php artisan migrate:rollback`)

```bash
larapy db:rollback [OPTIONS]

Options:
  --step INTEGER    Number of migration batches to rollback (default: 1)
  --force          Force the rollback in production
```

**Examples:**
```bash
# Rollback last batch
larapy db:rollback

# Rollback last 3 batches
larapy db:rollback --step=3
```

#### `larapy db:fresh`
Drop all tables and re-run migrations (equivalent to `php artisan migrate:fresh`)

```bash
larapy db:fresh [OPTIONS]

Options:
  --seed     Seed the database after refreshing
  --force    Force the refresh in production
```

**Example:**
```bash
# Fresh migration with seeding
larapy db:fresh --seed
```

#### `larapy db:seed`
Run database seeders (equivalent to `php artisan db:seed`)

```bash
larapy db:seed [SEEDER]

Arguments:
  SEEDER    Optional specific seeder to run
```

**Examples:**
```bash
# Run all seeders
larapy db:seed

# Run specific seeder
larapy db:seed UserSeeder
```

#### `larapy db:status`
Show migration status (equivalent to `php artisan migrate:status`)

```bash
larapy db:status
```

**Output Example:**
```
📊 Migration Status:
------------------------------------------------------------
✅ 2024_01_01_000000_create_users_table
✅ 2024_01_02_000000_create_posts_table
❌ 2024_01_03_000000_create_comments_table
```

#### `larapy db:inspect`
Inspect database structure

```bash
larapy db:inspect [OPTIONS]

Options:
  --table TEXT     Inspect specific table
  --show-data      Show sample data from tables
```

**Examples:**
```bash
# Inspect all tables
larapy db:inspect

# Inspect specific table with data
larapy db:inspect --table=users --show-data
```

#### `larapy db:schema`
Show database schema

```bash
larapy db:schema [OPTIONS]

Options:
  --table TEXT              Show schema for specific table
  --output [text|sql]       Output format (default: text)
```

**Examples:**
```bash
# Show all schemas
larapy db:schema

# Export schema as SQL
larapy db:schema --output=sql

# Show specific table schema
larapy db:schema --table=users
```

### 4. Configuration Management Commands

#### `larapy config:show`
Display configuration information

```bash
larapy config:show
```

#### `larapy config:publish`
Publish configuration files from packages

```bash
larapy config:publish PACKAGE [OPTIONS]

Options:
  --force    Overwrite existing configuration files
  --tag      Specific configuration tag to publish
```

#### `larapy config:backup`
Create a backup of configuration files

```bash
larapy config:backup [OPTIONS]

Options:
  --name TEXT        Backup name (defaults to timestamp)
  --configs TEXT     Specific configuration files to backup
```

#### `larapy config:restore`
Restore configuration files from backup

```bash
larapy config:restore BACKUP_NAME [OPTIONS]

Options:
  --no-verify    Skip checksum verification
```

#### `larapy config:validate`
Validate configuration files against schemas

```bash
larapy config:validate [CONFIGS...]
```

#### `larapy config:encrypt`
Encrypt sensitive configuration values

```bash
larapy config:encrypt CONFIG KEYS...
```

**Example:**
```bash
larapy config:encrypt database password api_key
```

#### `larapy config:decrypt`
Decrypt and display configuration values

```bash
larapy config:decrypt CONFIG [KEYS...]
```

#### `larapy config:hot-reload`
Enable or disable configuration hot-reloading

```bash
larapy config:hot-reload [enable|disable] [OPTIONS]

Options:
  --configs TEXT    Configuration files to watch
```

#### `larapy config:merge`
Merge configuration files with package overrides

```bash
larapy config:merge BASE_CONFIG [OPTIONS]

Options:
  --packages TEXT    Package configurations to merge
  --output TEXT      Output merged configuration to file
  --dry-run          Show merge result without saving
```

### 5. Environment Management Commands

#### `larapy env:status`
Display current environment status and configuration

```bash
larapy env:status [OPTIONS]

Options:
  --json          Output in JSON format
  --validation    Include validation details
```

#### `larapy env:init`
Initialize a new environment configuration

```bash
larapy env:init ENVIRONMENT [OPTIONS]

Options:
  --force              Overwrite existing configuration
  --no-deps            Skip dependency installation
  --no-db              Skip database initialization
  --template-vars      Template variables in key=value format
```

**Example:**
```bash
larapy env:init production --force
```

#### `larapy env:switch`
Switch to a different environment

```bash
larapy env:switch ENVIRONMENT [OPTIONS]

Options:
  --backup    Backup current environment before switching
```

**Example:**
```bash
larapy env:switch staging --backup
```

#### `larapy env:list`
List all available environments

```bash
larapy env:list [OPTIONS]

Options:
  --details    Show detailed information for each environment
```

#### `larapy env:validate`
Validate environment variable configuration

```bash
larapy env:validate [ENVIRONMENT] [OPTIONS]

Options:
  --fix    Attempt to fix validation issues
```

#### `larapy env:export`
Export environment configuration to a file

```bash
larapy env:export ENVIRONMENT OUTPUT_FILE [OPTIONS]

Options:
  --include-secrets    Include sensitive values in export
```

**Example:**
```bash
larapy env:export production prod.env --include-secrets
```

#### `larapy env:import`
Import environment configuration from a file

```bash
larapy env:import ENVIRONMENT INPUT_FILE [OPTIONS]

Options:
  --force    Overwrite existing environment
```

#### `larapy env:clone`
Clone an environment configuration to create a new one

```bash
larapy env:clone SOURCE TARGET [OPTIONS]

Options:
  --modifications    Modifications in key=value format
```

**Example:**
```bash
larapy env:clone development testing --modifications="DEBUG=false"
```

### 6. Other Commands

#### `larapy routes`
Display registered routes (equivalent to `php artisan route:list`)

```bash
larapy routes
```

**Output Example:**
```
Route list:
--------------------------------------------------------------------------------
Method     URI                           Name                Action
--------------------------------------------------------------------------------
GET        /                             home                HomeController@index
POST       /users                        users.store         UserController@store
GET        /users/{id}                   users.show          UserController@show
```

#### `larapy tinker`
Start an interactive Python shell (equivalent to `php artisan tinker`)

```bash
larapy tinker [NAMESPACE]
```

This starts a Python REPL with the application context loaded, allowing you to interact with your application's models, services, and other components interactively.

## Usage Examples

### Starting a New Project

```bash
# 1. Create a new project directory
mkdir my-app && cd my-app

# 2. Initialize the project structure
larapy init

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env

# 5. Run migrations
larapy db:migrate

# 6. Start development server
larapy serve --reload
```

### Creating a Blog Feature

```bash
# 1. Create the model with migration
larapy make:model Article --migration

# 2. Create a resource controller
larapy make:controller ArticleController --resource

# 3. Create middleware for authentication
larapy make:middleware AuthMiddleware

# 4. Run the migration
larapy db:migrate

# 5. Create and run a seeder
larapy make:seeder ArticleSeeder
larapy db:seed ArticleSeeder
```

### Database Workflow

```bash
# Check migration status
larapy db:status

# Run pending migrations
larapy db:migrate

# Rollback if needed
larapy db:rollback

# Fresh start with seeding
larapy db:fresh --seed

# Inspect database
larapy db:inspect --show-data
```

### Environment Management

```bash
# Check current environment
larapy env:status

# Create production environment
larapy env:init production

# Clone to staging
larapy env:clone production staging

# Switch environments
larapy env:switch staging

# Validate configuration
larapy env:validate --fix
```

## Command Structure

The Larapy CLI follows Laravel's Artisan command structure:

- **Namespace:action** format (e.g., `db:migrate`, `make:controller`)
- **Intuitive naming** matching Laravel conventions
- **Helpful options** with `--help` flag for each command
- **Colored output** for better readability
- **Progress indicators** for long-running tasks

## Extending the CLI

You can create custom commands by:

1. Creating a new command class
2. Registering it in the CLI
3. Adding it to your application's console kernel

Example custom command:
```python
@main.command()
@click.argument('name')
def custom_command(name: str):
    """Your custom command description."""
    click.echo(f"Running custom command for {name}")
```

## Best Practices

1. **Use resource controllers** for RESTful resources
2. **Run migrations with --seed** in development
3. **Always backup** before switching environments
4. **Validate configuration** after changes
5. **Use tinker** for quick testing and debugging
6. **Check db:status** before deploying

## Troubleshooting

### Command Not Found
If `larapy` command is not found:
```bash
# Reinstall in development mode
pip install -e /path/to/larapy
```

### Migration Errors
```bash
# Check status first
larapy db:status

# Rollback if needed
larapy db:rollback

# Fresh start
larapy db:fresh
```

### Environment Issues
```bash
# Validate environment
larapy env:validate --fix

# Check configuration
larapy config:validate
```

## Comparison with Laravel Artisan

| Laravel Artisan | Larapy CLI | Description |
|-----------------|------------|-------------|
| `php artisan serve` | `larapy serve` | Start development server |
| `php artisan make:controller` | `larapy make:controller` | Generate controller |
| `php artisan make:model` | `larapy make:model` | Generate model |
| `php artisan migrate` | `larapy db:migrate` | Run migrations |
| `php artisan db:seed` | `larapy db:seed` | Run seeders |
| `php artisan migrate:rollback` | `larapy db:rollback` | Rollback migrations |
| `php artisan migrate:fresh` | `larapy db:fresh` | Fresh migrations |
| `php artisan route:list` | `larapy routes` | List routes |
| `php artisan tinker` | `larapy tinker` | Interactive shell |

## Conclusion

The Larapy CLI provides a complete Laravel Artisan experience in Python, making it easy for Laravel developers to transition to Python while maintaining familiar workflows and conventions. All commands follow Laravel's naming conventions and provide similar functionality, ensuring a smooth development experience.