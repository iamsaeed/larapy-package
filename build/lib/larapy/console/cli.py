"""
Command-line interface for Larapy applications.

This module provides Laravel's Artisan-like CLI functionality with
commands for development, code generation, and application management.
"""

import click
import sys
from pathlib import Path
from typing import Optional


@click.group()
@click.version_option(version="0.1.0")
@click.pass_context
def main(ctx):
    """
    Larapy - A Python framework inspired by Laravel
    
    The Larapy command-line interface provides tools for development,
    code generation, and application management.
    """
    # Ensure we have a click context
    ctx.ensure_object(dict)


@main.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8000, type=int, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def serve(host: str, port: int, reload: bool, debug: bool):
    """Start the development server."""
    click.echo(f"Starting Larapy development server...")
    click.echo(f"Server running at http://{host}:{port}")
    click.echo("Press CTRL+C to quit")
    
    if reload:
        click.echo("Auto-reload enabled")
    
    if debug:
        click.echo("Debug mode enabled")
    
    # In a full implementation, this would start uvicorn
    try:
        import uvicorn
        uvicorn.run(
            "bootstrap.app:app",  # Application import string
            host=host,
            port=port,
            reload=reload,
            log_level="debug" if debug else "info"
        )
    except ImportError:
        click.echo("Error: uvicorn not installed. Install with: pip install uvicorn")
        sys.exit(1)
    except FileNotFoundError:
        click.echo("Error: No application found. Make sure you have an app.py file.")
        sys.exit(1)


@main.group()
def make():
    """Generate application components."""
    pass


@make.command('controller')
@click.argument('name')
@click.option('--resource', is_flag=True, help='Create a resource controller')
@click.option('--api', is_flag=True, help='Create an API resource controller')
def make_controller(name: str, resource: bool, api: bool):
    """Create a new controller."""
    controller_name = name if name.endswith('Controller') else f"{name}Controller"
    
    # Create controllers directory if it doesn't exist
    controllers_dir = Path('app/http/controllers')
    controllers_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate controller content
    if resource:
        content = _generate_resource_controller(controller_name, api)
    else:
        content = _generate_basic_controller(controller_name)
    
    # Write controller file
    controller_file = controllers_dir / f"{controller_name.lower()}.py"
    controller_file.write_text(content)
    
    click.echo(f"Controller created: {controller_file}")


@make.command('model')
@click.argument('name')
@click.option('--migration', '-m', is_flag=True, help='Create migration as well')
def make_model(name: str, migration: bool):
    """Create a new model."""
    # Create models directory if it doesn't exist
    models_dir = Path('app/models')
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate model content
    content = _generate_model(name)
    
    # Write model file
    model_file = models_dir / f"{name.lower()}.py"
    model_file.write_text(content)
    
    click.echo(f"Model created: {model_file}")
    
    if migration:
        # Create migration as well
        click.echo("Creating migration...")
        # In a full implementation, this would create a migration file


@make.command('middleware')
@click.argument('name')
def make_middleware(name: str):
    """Create a new middleware."""
    middleware_name = name if name.endswith('Middleware') else f"{name}Middleware"
    
    # Create middleware directory if it doesn't exist
    middleware_dir = Path('app/http/middleware')
    middleware_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate middleware content
    content = _generate_middleware(middleware_name)
    
    # Write middleware file
    middleware_file = middleware_dir / f"{middleware_name.lower()}.py"
    middleware_file.write_text(content)
    
    click.echo(f"Middleware created: {middleware_file}")


@main.group()
def db():
    """Database management commands."""
    pass


@db.command('migrate')
@click.option('--seed', is_flag=True, help='Seed the database after migrating')
@click.option('--force', is_flag=True, help='Force the migration in production')
def db_migrate(seed: bool, force: bool):
    """Run database migrations."""
    try:
        from ..database.migrations.migrator import Migrator
        from ..database.connection import DatabaseManager
        from pathlib import Path
        import os
        
        click.echo("🔄 Running migrations...")
        
        # Load database configuration
        config = {
            'default': 'sqlite',
            'connections': {
                'sqlite': {
                    'driver': 'sqlite',
                    'database': 'database/database.sqlite'
                }
            }
        }
        
        # Create database manager and migrator
        db_manager = DatabaseManager(config)
        migrator = Migrator(db_manager)
        
        # Get migrations path
        migrations_path = Path('database/migrations')
        
        if not migrations_path.exists():
            click.echo("❌ No migrations directory found. Run 'larapy make:migration' first.")
            return
        
        # Run migrations
        count = migrator.run_migrations(migrations_path)
        
        if count > 0:
            click.echo(f"✅ Migrated {count} migrations successfully.")
        else:
            click.echo("✅ Nothing to migrate.")
        
        # Run seeders if requested
        if seed:
            click.echo("🌱 Running seeders...")
            from ..database.migrations.seeder import SeederRunner
            
            seeders_path = Path('database/seeders')
            if seeders_path.exists():
                seeder_runner = SeederRunner(db_manager)
                seeder_count = seeder_runner.run_all(seeders_path)
                click.echo(f"✅ Seeded {seeder_count} seeders successfully.")
            else:
                click.echo("⚠️ No seeders directory found.")
        
    except Exception as e:
        click.echo(f"❌ Migration failed: {str(e)}")


@db.command('rollback')
@click.option('--step', default=1, help='Number of migration batches to rollback')
@click.option('--force', is_flag=True, help='Force the rollback in production')
def db_rollback(step: int, force: bool):
    """Rollback database migrations."""
    try:
        from ..database.migrations.migrator import Migrator
        from ..database.connection import DatabaseManager
        
        click.echo(f"🔄 Rolling back {step} migration batch(es)...")
        
        # Load database configuration
        config = {
            'default': 'sqlite',
            'connections': {
                'sqlite': {
                    'driver': 'sqlite',
                    'database': 'database/database.sqlite'
                }
            }
        }
        
        # Create database manager and migrator
        db_manager = DatabaseManager(config)
        migrator = Migrator(db_manager)
        
        # Run rollbacks
        count = migrator.rollback_migrations(step)
        
        if count > 0:
            click.echo(f"✅ Rolled back {count} migrations successfully.")
        else:
            click.echo("✅ Nothing to rollback.")
        
    except Exception as e:
        click.echo(f"❌ Rollback failed: {str(e)}")


@db.command('fresh')
@click.option('--seed', is_flag=True, help='Seed the database after refreshing')
@click.option('--force', is_flag=True, help='Force the refresh in production')
def db_fresh(seed: bool, force: bool):
    """Drop all tables and re-run migrations."""
    try:
        from ..database.migrations.migrator import Migrator
        from ..database.connection import DatabaseManager
        from pathlib import Path
        
        click.echo("🔄 Dropping all tables and re-running migrations...")
        
        # Load database configuration
        config = {
            'default': 'sqlite',
            'connections': {
                'sqlite': {
                    'driver': 'sqlite',
                    'database': 'database/database.sqlite'
                }
            }
        }
        
        # Create database manager and migrator
        db_manager = DatabaseManager(config)
        migrator = Migrator(db_manager)
        
        # Drop all tables
        migrator.drop_all_tables()
        click.echo("✅ Dropped all tables.")
        
        # Re-run migrations
        migrations_path = Path('database/migrations')
        if migrations_path.exists():
            count = migrator.run_migrations(migrations_path)
            click.echo(f"✅ Re-ran {count} migrations successfully.")
        
        # Run seeders if requested
        if seed:
            click.echo("🌱 Running seeders...")
            from ..database.migrations.seeder import SeederRunner
            
            seeders_path = Path('database/seeders')
            if seeders_path.exists():
                seeder_runner = SeederRunner(db_manager)
                seeder_count = seeder_runner.run_all(seeders_path)
                click.echo(f"✅ Seeded {seeder_count} seeders successfully.")
        
    except Exception as e:
        click.echo(f"❌ Fresh migration failed: {str(e)}")


@db.command('seed')
@click.argument('seeder', required=False)
def db_seed(seeder: Optional[str]):
    """Run database seeders."""
    try:
        from ..database.migrations.seeder import SeederRunner
        from ..database.connection import DatabaseManager
        from pathlib import Path
        
        # Load database configuration
        config = {
            'default': 'sqlite',
            'connections': {
                'sqlite': {
                    'driver': 'sqlite',
                    'database': 'database/database.sqlite'
                }
            }
        }
        
        db_manager = DatabaseManager(config)
        seeder_runner = SeederRunner(db_manager)
        
        if seeder:
            click.echo(f"🌱 Running seeder: {seeder}")
            seeder_runner.run_single(seeder)
        else:
            click.echo("🌱 Running all seeders...")
            seeders_path = Path('database/seeders')
            if seeders_path.exists():
                count = seeder_runner.run_all(seeders_path)
                click.echo(f"✅ Seeded {count} seeders successfully.")
            else:
                click.echo("❌ No seeders directory found.")
    
    except Exception as e:
        click.echo(f"❌ Seeding failed: {str(e)}")


@db.command('status')
def db_status():
    """Show migration status."""
    try:
        from ..database.migrations.migrator import Migrator
        from ..database.connection import DatabaseManager
        
        click.echo("📊 Migration Status:")
        click.echo("-" * 60)
        
        # Load database configuration
        config = {
            'default': 'sqlite',
            'connections': {
                'sqlite': {
                    'driver': 'sqlite',
                    'database': 'database/database.sqlite'
                }
            }
        }
        
        db_manager = DatabaseManager(config)
        migrator = Migrator(db_manager)
        
        # Get migration status
        status = migrator.get_migration_status()
        
        for migration_file, is_run in status.items():
            status_icon = "✅" if is_run else "❌"
            click.echo(f"{status_icon} {migration_file}")
        
    except Exception as e:
        click.echo(f"❌ Status check failed: {str(e)}")


@db.command('inspect')
@click.option('--table', help='Inspect specific table')
@click.option('--show-data', is_flag=True, help='Show sample data from tables')
def db_inspect(table: str, show_data: bool):
    """Inspect database structure."""
    try:
        from pathlib import Path
        from ..database.connection import DatabaseManager
        
        click.echo("🔍 Database Inspection:")
        click.echo("=" * 60)
        
        # Load database configuration
        config = {
            'default': 'sqlite',
            'connections': {
                'sqlite': {
                    'driver': 'sqlite',
                    'database': 'database/database.sqlite'
                }
            }
        }
        
        # Create database manager
        db_manager = DatabaseManager(config)
        connection = db_manager.connection()
        
        if table:
            # Inspect specific table
            _inspect_table(connection, table, show_data)
        else:
            # Inspect all tables
            _inspect_all_tables(connection, show_data)
            
    except Exception as e:
        click.echo(f"❌ Database inspection failed: {str(e)}")


def _inspect_table(connection, table_name: str, show_data: bool):
    """Inspect a specific table."""
    import sqlite3
    
    click.echo(f"\n📋 Table: {table_name}")
    click.echo("-" * 40)
    
    try:
        cursor = connection.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        if not columns:
            click.echo(f"❌ Table '{table_name}' not found")
            return
        
        # Show columns
        click.echo("Columns:")
        for col in columns:
            pk_marker = " (PK)" if col[5] else ""
            nullable = "NULL" if not col[3] else "NOT NULL"
            default = f" DEFAULT: {col[4]}" if col[4] else ""
            click.echo(f"  • {col[1]} - {col[2]} {nullable}{default}{pk_marker}")
        
        # Show indexes
        cursor = connection.execute(f"PRAGMA index_list({table_name})")
        indexes = cursor.fetchall()
        if indexes:
            click.echo("\nIndexes:")
            for idx in indexes:
                unique_marker = " (UNIQUE)" if idx[2] else ""
                click.echo(f"  • {idx[1]}{unique_marker}")
        
        # Show row count
        cursor = connection.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        click.echo(f"\nRow count: {count}")
        
        # Show sample data if requested
        if show_data and count > 0:
            cursor = connection.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                click.echo("\nSample data (first 5 rows):")
                column_names = [col[1] for col in columns]
                
                # Print header
                header = " | ".join(f"{name:15}" for name in column_names)
                click.echo(f"  {header}")
                click.echo(f"  {'-' * len(header)}")
                
                # Print rows
                for row in rows:
                    row_str = " | ".join(f"{str(val):15}" for val in row)
                    click.echo(f"  {row_str}")
        
    except Exception as e:
        click.echo(f"❌ Error inspecting table {table_name}: {e}")


def _inspect_all_tables(connection, show_data: bool):
    """Inspect all tables in the database."""
    import sqlite3
    
    try:
        # Get all tables
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = cursor.fetchall()
        
        if not tables:
            click.echo("📭 No tables found in database")
            return
        
        click.echo(f"📊 Found {len(tables)} table(s):")
        
        for table in tables:
            table_name = table[0]
            
            # Get row count
            cursor = connection.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # Get column count
            cursor = connection.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            col_count = len(columns)
            
            click.echo(f"  • {table_name}: {count} rows, {col_count} columns")
            
            if show_data:
                _inspect_table(connection, table_name, False)
        
    except Exception as e:
        click.echo(f"❌ Error inspecting database: {e}")


@db.command('schema')
@click.option('--table', help='Show schema for specific table')
@click.option('--output', type=click.Choice(['text', 'sql']), default='text', help='Output format')
def db_schema(table: str, output: str):
    """Show database schema."""
    try:
        from pathlib import Path
        from ..database.connection import DatabaseManager
        
        click.echo("📐 Database Schema:")
        click.echo("=" * 60)
        
        # Load database configuration
        config = {
            'default': 'sqlite',
            'connections': {
                'sqlite': {
                    'driver': 'sqlite',
                    'database': 'database/database.sqlite'
                }
            }
        }
        
        # Create database manager
        db_manager = DatabaseManager(config)
        connection = db_manager.connection()
        
        if table:
            _show_table_schema(connection, table, output)
        else:
            _show_all_schemas(connection, output)
            
    except Exception as e:
        click.echo(f"❌ Schema display failed: {str(e)}")


def _show_table_schema(connection, table_name: str, output: str):
    """Show schema for a specific table."""
    try:
        if output == 'sql':
            # Get CREATE TABLE statement
            cursor = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            result = cursor.fetchone()
            if result:
                click.echo(f"\n-- {table_name}")
                click.echo(result[0] + ";")
            else:
                click.echo(f"❌ Table '{table_name}' not found")
        else:
            _inspect_table(connection, table_name, False)
            
    except Exception as e:
        click.echo(f"❌ Error showing schema for {table_name}: {e}")


def _show_all_schemas(connection, output: str):
    """Show schema for all tables."""
    try:
        # Get all tables
        cursor = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = cursor.fetchall()
        
        if not tables:
            click.echo("📭 No tables found in database")
            return
        
        if output == 'sql':
            click.echo("-- Database Schema Export")
            click.echo("-- Generated by Larapy\n")
            
            for table in tables:
                click.echo(f"-- {table[0]}")
                click.echo(table[1] + ";\n")
        else:
            for table in tables:
                _inspect_table(connection, table[0], False)
        
    except Exception as e:
        click.echo(f"❌ Error showing schemas: {e}")


@main.command()
def routes():
    """Display registered routes."""
    click.echo("Route list:")
    click.echo("-" * 80)
    click.echo(f"{'Method':<10} {'URI':<30} {'Name':<20} {'Action'}")
    click.echo("-" * 80)
    
    # In a full implementation, this would display actual routes
    click.echo(f"{'GET':<10} {'/':<30} {'home':<20} {'HomeController@index'}")
    click.echo(f"{'POST':<10} {'/users':<30} {'users.store':<20} {'UserController@store'}")


@main.group()
def config():
    """Configuration management commands."""
    pass


@config.command('show')
def config_show():
    """Display configuration information."""
    click.echo("Application Configuration:")
    click.echo("-" * 40)
    
    # In a full implementation, this would show actual config
    click.echo("Environment: development")
    click.echo("Debug: True")
    click.echo("Database: sqlite")


@config.command('publish')
@click.argument('package')
@click.option('--force', is_flag=True, help='Overwrite existing configuration files')
@click.option('--tag', help='Specific configuration tag to publish')
def config_publish(package: str, force: bool, tag: str):
    """Publish configuration files from packages."""
    try:
        from .commands.config_commands import ConfigPublishCommand
        
        command = ConfigPublishCommand()
        options = {
            'package': package,
            'force': force,
            'tag': tag
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error publishing configuration: {e}")


@config.command('backup')
@click.option('--name', help='Backup name (defaults to timestamp)')
@click.option('--configs', multiple=True, help='Specific configuration files to backup')
def config_backup(name: str, configs: tuple):
    """Create a backup of configuration files."""
    try:
        from .commands.config_commands import ConfigBackupCommand
        
        command = ConfigBackupCommand()
        options = {
            'name': name,
            'configs': list(configs) if configs else []
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error creating backup: {e}")


@config.command('restore')
@click.argument('backup_name')
@click.option('--no-verify', is_flag=True, help='Skip checksum verification')
def config_restore(backup_name: str, no_verify: bool):
    """Restore configuration files from backup."""
    try:
        from .commands.config_commands import ConfigRestoreCommand
        
        command = ConfigRestoreCommand()
        options = {
            'backup_name': backup_name,
            'no_verify': no_verify
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error restoring backup: {e}")


@config.command('list-backups')
def config_list_backups():
    """List available configuration backups."""
    try:
        from .commands.config_commands import ConfigListBackupsCommand
        
        command = ConfigListBackupsCommand()
        command.handle()
        
    except Exception as e:
        click.echo(f"❌ Error listing backups: {e}")


@config.command('validate')
@click.argument('configs', nargs=-1)
def config_validate(configs: tuple):
    """Validate configuration files against schemas."""
    try:
        from .commands.config_commands import ConfigValidateCommand
        
        command = ConfigValidateCommand()
        options = {
            'configs': list(configs) if configs else []
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error validating configuration: {e}")


@config.command('encrypt')
@click.argument('config')
@click.argument('keys', nargs=-1, required=True)
def config_encrypt(config: str, keys: tuple):
    """Encrypt sensitive configuration values."""
    try:
        from .commands.config_commands import ConfigEncryptCommand
        
        command = ConfigEncryptCommand()
        options = {
            'config': config,
            'keys': list(keys)
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error encrypting configuration: {e}")


@config.command('decrypt')
@click.argument('config')
@click.argument('keys', nargs=-1)
def config_decrypt(config: str, keys: tuple):
    """Decrypt and display configuration values."""
    try:
        from .commands.config_commands import ConfigDecryptCommand
        
        command = ConfigDecryptCommand()
        options = {
            'config': config,
            'keys': list(keys) if keys else []
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error decrypting configuration: {e}")


@config.command('hot-reload')
@click.argument('action', type=click.Choice(['enable', 'disable']))
@click.option('--configs', multiple=True, help='Configuration files to watch')
def config_hot_reload(action: str, configs: tuple):
    """Enable or disable configuration hot-reloading."""
    try:
        from .commands.config_commands import ConfigHotReloadCommand
        
        command = ConfigHotReloadCommand()
        options = {
            'action': action,
            'configs': list(configs) if configs else []
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error managing hot-reload: {e}")


@config.command('merge')
@click.argument('base_config')
@click.option('--packages', multiple=True, help='Package configurations to merge')
@click.option('--output', help='Output merged configuration to file')
@click.option('--dry-run', is_flag=True, help='Show merge result without saving')
def config_merge(base_config: str, packages: tuple, output: str, dry_run: bool):
    """Merge configuration files with package overrides."""
    try:
        from .commands.config_commands import ConfigMergeCommand
        
        command = ConfigMergeCommand()
        options = {
            'base_config': base_config,
            'packages': list(packages) if packages else [],
            'output': output,
            'dry_run': dry_run
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error merging configuration: {e}")


@main.group()
def env():
    """Environment management commands."""
    pass


@env.command('status')
@click.option('--json', is_flag=True, help='Output in JSON format')
@click.option('--validation', is_flag=True, help='Include validation details')
def env_status(json: bool, validation: bool):
    """Display current environment status and configuration."""
    try:
        from .commands.environment_commands import EnvironmentStatusCommand
        
        command = EnvironmentStatusCommand()
        options = {
            'json': json,
            'validation': validation
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error getting environment status: {e}")


@env.command('init')
@click.argument('environment')
@click.option('--force', is_flag=True, help='Overwrite existing configuration')
@click.option('--no-deps', is_flag=True, help='Skip dependency installation')
@click.option('--no-db', is_flag=True, help='Skip database initialization')
@click.option('--template-vars', multiple=True, help='Template variables in key=value format')
def env_init(environment: str, force: bool, no_deps: bool, no_db: bool, template_vars: tuple):
    """Initialize a new environment configuration."""
    try:
        from .commands.environment_commands import EnvironmentInitCommand
        
        command = EnvironmentInitCommand()
        options = {
            'environment': environment,
            'force': force,
            'no_deps': no_deps,
            'no_db': no_db,
            'template_vars': list(template_vars) if template_vars else None
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error initializing environment: {e}")


@env.command('switch')
@click.argument('environment')
@click.option('--backup', is_flag=True, help='Backup current environment before switching')
def env_switch(environment: str, backup: bool):
    """Switch to a different environment."""
    try:
        from .commands.environment_commands import EnvironmentSwitchCommand
        
        command = EnvironmentSwitchCommand()
        options = {
            'environment': environment,
            'backup': backup
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error switching environment: {e}")


@env.command('list')
@click.option('--details', is_flag=True, help='Show detailed information for each environment')
def env_list(details: bool):
    """List all available environments."""
    try:
        from .commands.environment_commands import EnvironmentListCommand
        
        command = EnvironmentListCommand()
        options = {
            'details': details
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error listing environments: {e}")


@env.command('validate')
@click.argument('environment', required=False)
@click.option('--fix', is_flag=True, help='Attempt to fix validation issues')
def env_validate(environment: str, fix: bool):
    """Validate environment variable configuration."""
    try:
        from .commands.environment_commands import EnvironmentValidateCommand
        
        command = EnvironmentValidateCommand()
        options = {
            'environment': environment,
            'fix': fix
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error validating environment: {e}")


@env.command('export')
@click.argument('environment')
@click.argument('output_file')
@click.option('--include-secrets', is_flag=True, help='Include sensitive values in export')
def env_export(environment: str, output_file: str, include_secrets: bool):
    """Export environment configuration to a file."""
    try:
        from .commands.environment_commands import EnvironmentExportCommand
        
        command = EnvironmentExportCommand()
        options = {
            'environment': environment,
            'output_file': output_file,
            'include_secrets': include_secrets
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error exporting environment: {e}")


@env.command('import')
@click.argument('environment')
@click.argument('input_file')
@click.option('--force', is_flag=True, help='Overwrite existing environment')
def env_import(environment: str, input_file: str, force: bool):
    """Import environment configuration from a file."""
    try:
        from .commands.environment_commands import EnvironmentImportCommand
        
        command = EnvironmentImportCommand()
        options = {
            'environment': environment,
            'input_file': input_file,
            'force': force
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error importing environment: {e}")


@env.command('clone')
@click.argument('source')
@click.argument('target')
@click.option('--modifications', multiple=True, help='Modifications in key=value format')
def env_clone(source: str, target: str, modifications: tuple):
    """Clone an environment configuration to create a new one."""
    try:
        from .commands.environment_commands import EnvironmentCloneCommand
        
        command = EnvironmentCloneCommand()
        options = {
            'source': source,
            'target': target,
            'modifications': list(modifications) if modifications else None
        }
        command.handle(**options)
        
    except Exception as e:
        click.echo(f"❌ Error cloning environment: {e}")


@main.command()
@click.argument('namespace', required=False)
def tinker(namespace: Optional[str]):
    """Start an interactive Python shell."""
    click.echo("Starting Larapy interactive shell...")
    
    # Set up the environment
    import code
    
    # In a full implementation, this would load the application context
    banner = "Larapy Interactive Shell\nPython %s" % sys.version
    
    # Start the interactive console
    code.interact(banner=banner, local=globals())


def _generate_basic_controller(name: str) -> str:
    """Generate basic controller template."""
    return f'''"""
{name} controller for handling HTTP requests.
"""

from larapy.http.request import Request
from larapy.http.response import Response


class {name}:
    """
    {name} for handling requests.
    """
    
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
        return Response(f"Show method for ID: {{id}}")
'''


def _generate_resource_controller(name: str, api: bool = False) -> str:
    """Generate resource controller template."""
    methods = [
        ("index", "Display a listing of the resource"),
        ("show", "Display the specified resource"),
        ("store", "Store a newly created resource"),
        ("update", "Update the specified resource"),
        ("destroy", "Remove the specified resource")
    ]
    
    if not api:
        methods.insert(1, ("create", "Show the form for creating a new resource"))
        methods.insert(4, ("edit", "Show the form for editing the specified resource"))
    
    method_implementations = []
    
    for method_name, description in methods:
        if method_name in ['index']:
            params = "self, request: Request"
            call_params = ""
        elif method_name in ['create']:
            params = "self, request: Request"
            call_params = ""
        elif method_name in ['store']:
            params = "self, request: Request"
            call_params = ""
        else:
            params = "self, request: Request, id: str"
            call_params = f" for ID: {{id}}"
        
        method_implementations.append(f'''    def {method_name}({params}) -> Response:
        """
        {description}
        
        Args:
            request: The HTTP request
            {"id: Resource ID" if "id" in params else ""}
            
        Returns:
            HTTP response
        """
        return Response("{method_name.title()} method{call_params}")''')
    
    return f'''"""
{name} controller for handling HTTP requests.
"""

from larapy.http.request import Request
from larapy.http.response import Response


class {name}:
    """
    {name} for handling resource requests.
    """
    
{chr(10).join(method_implementations)}
'''


def _generate_model(name: str) -> str:
    """Generate model template."""
    return f'''"""
{name} model for database operations.
"""


class {name}:
    """
    {name} model for database interactions.
    
    This model represents the {name.lower()} entity in the database.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the model.
        
        Args:
            **kwargs: Model attributes
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def save(self):
        """Save the model to the database."""
        # In a full implementation, this would save to database
        pass
    
    @classmethod
    def find(cls, id):
        """
        Find a model by ID.
        
        Args:
            id: The model ID
            
        Returns:
            Model instance or None
        """
        # In a full implementation, this would query the database
        return None
    
    @classmethod
    def all(cls):
        """
        Get all models.
        
        Returns:
            List of model instances
        """
        # In a full implementation, this would query the database
        return []
    
    def __str__(self):
        return f"{name}({{self.__dict__}})"
    
    def __repr__(self):
        return self.__str__()
'''


def _generate_middleware(name: str) -> str:
    """Generate middleware template."""
    return f'''"""
{name} for handling HTTP middleware.
"""

from larapy.http.request import Request
from larapy.http.response import Response
from typing import Callable


class {name}:
    """
    {name} for processing HTTP requests.
    """
    
    def handle(self, request: Request, next_handler: Callable) -> Response:
        """
        Handle the incoming request.
        
        Args:
            request: The HTTP request
            next_handler: The next middleware in the stack
            
        Returns:
            HTTP response
        """
        # Process request before passing to next middleware
        # ...
        
        # Call the next middleware
        response = next_handler(request)
        
        # Process response after receiving from next middleware
        # ...
        
        return response
'''


if __name__ == '__main__':
    main()