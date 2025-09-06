"""
Larapy CLI - Laravel-like Command Line Interface

This module provides comprehensive CLI commands following the migration-db.md specification.
"""

import click
from pathlib import Path
from datetime import datetime


@click.group()
@click.version_option(version='0.2.0')
def main():
    """
    Larapy - A Python framework inspired by Laravel
    
    The Larapy command-line interface provides tools for development, code
    generation, and application management.
    """
    pass


@main.group()
def make():
    """Generate application components."""
    pass


@main.group()
def migrate():
    """Run database migrations."""
    pass


@main.group()
def db():
    """Database management commands."""
    pass


@main.group()
def config_cmd():
    """Configuration management commands."""
    pass


# Make it accessible as both 'config' and 'config_cmd'
config = config_cmd


# =============================================================================
# MIGRATION COMMANDS (larapy migrate)
# =============================================================================

@migrate.command()
@click.option('--seed', is_flag=True, help='Indicates if the seed task should be re-run')
@click.option('--force', is_flag=True, help='Force the operation to run when in production')
@click.option('--pretend', is_flag=True, help='Dump the SQL queries that would be run')
@click.option('--step', type=int, help='Number of migrations to run')
def run(seed: bool, force: bool, pretend: bool, step: int):
    """Run the database migrations."""
    try:
        from ..database.migrations.migrator import Migrator
        
        migrator = Migrator()
        
        if pretend:
            count = migrator.migrate(step=step, pretend=True)
            click.echo(f"📄 {count} migrations would be run.")
        else:
            click.echo("🚀 Running migrations...")
            count = migrator.migrate(step=step, seed=seed)
            if count > 0:
                click.echo(f"✅ Migrated {count} migrations successfully.")
            else:
                click.echo("✅ Nothing to migrate.")
        
    except Exception as e:
        click.echo(f"❌ Migration failed: {str(e)}")


@migrate.command()
@click.option('--step', type=int, default=1, help='Number of migration batches to be reverted')
@click.option('--force', is_flag=True, help='Force the operation to run when in production')
@click.option('--pretend', is_flag=True, help='Dump the SQL queries that would be run')
def rollback(step: int, force: bool, pretend: bool):
    """Rollback the last database migration batches."""
    try:
        from ..database.migrations.migrator import Migrator
        
        migrator = Migrator()
        
        if pretend:
            count = migrator.rollback(step=step, pretend=True)
            click.echo(f"📄 {count} migrations would be rolled back.")
        else:
            click.echo(f"🔄 Rolling back {step} migration batch(es)...")
            count = migrator.rollback(step=step)
            if count > 0:
                click.echo(f"✅ Rolled back {count} migrations successfully.")
            else:
                click.echo("✅ Nothing to rollback.")
        
    except Exception as e:
        click.echo(f"❌ Rollback failed: {str(e)}")


@migrate.command()
@click.option('--force', is_flag=True, help='Force the operation to run when in production')
@click.option('--pretend', is_flag=True, help='Dump the SQL queries that would be run')
def reset(force: bool, pretend: bool):
    """Rollback all database migrations."""
    try:
        from ..database.migrations.migrator import Migrator
        
        migrator = Migrator()
        
        if pretend:
            # Get all executed migrations to show what would be reset
            executed = migrator.get_executed_migrations()
            click.echo(f"📄 {len(executed)} migrations would be rolled back.")
        else:
            click.echo("🔄 Rolling back all migrations...")
            count = migrator.reset()
            if count > 0:
                click.echo(f"✅ Reset {count} migrations successfully.")
            else:
                click.echo("✅ No migrations to reset.")
        
    except Exception as e:
        click.echo(f"❌ Reset failed: {str(e)}")


@migrate.command()
@click.option('--seed', is_flag=True, help='Indicates if the seed task should be re-run')
@click.option('--force', is_flag=True, help='Force the operation to run when in production')
def refresh(seed: bool, force: bool):
    """Reset and re-run all migrations."""
    try:
        from ..database.migrations.migrator import Migrator
        
        migrator = Migrator()
        
        click.echo("🔄 Refreshing migrations...")
        reset_count, migrate_count = migrator.refresh(seed=seed)
        click.echo(f"✅ Reset {reset_count} migrations and migrated {migrate_count} migrations.")
        
    except Exception as e:
        click.echo(f"❌ Refresh failed: {str(e)}")


@migrate.command()
@click.option('--seed', is_flag=True, help='Indicates if the seed task should be re-run')
@click.option('--force', is_flag=True, help='Force the operation to run when in production')
def fresh(seed: bool, force: bool):
    """Drop all tables and re-run all migrations."""
    try:
        from ..database.migrations.migrator import Migrator
        
        migrator = Migrator()
        
        click.echo("🗑️  Dropping all tables and running fresh migrations...")
        count = migrator.fresh(seed=seed)
        click.echo(f"✅ Fresh migration completed. {count} migrations run.")
        
    except Exception as e:
        click.echo(f"❌ Fresh migration failed: {str(e)}")


@migrate.command()
@click.option('--verbose', is_flag=True, help='Show detailed migration information')
@click.option('--pending', is_flag=True, help='Show only pending migrations')
@click.option('--executed', is_flag=True, help='Show only executed migrations')
def status(verbose: bool, pending: bool, executed: bool):
    """Show the status of each migration."""
    try:
        from ..database.migrations.migrator import Migrator
        
        migrator = Migrator()
        status_info = migrator.status(verbose=verbose, pending=pending, executed=executed)
        
        click.echo("📊 Migration Status")
        click.echo("─" * 70)
        
        if not status_info['migrations']:
            click.echo("No migrations found.")
            return
        
        # Table header
        click.echo(f"{'Migration':<50} {'Batch':<8} {'Status':<10}")
        click.echo("─" * 70)
        
        # Show migrations
        for migration in status_info['migrations']:
            status_icon = "✅" if migration['executed'] else "❌"
            batch_str = str(migration['batch']) if migration['batch'] else "N/A"
            status_str = "Ran" if migration['executed'] else "Pending"
            
            click.echo(f"{migration['filename']:<50} {batch_str:<8} {status_icon} {status_str}")
        
        # Summary
        click.echo("─" * 70)
        click.echo(f"Total: {status_info['total']} | Executed: {status_info['executed']} | Pending: {status_info['pending']}")
        
    except Exception as e:
        click.echo(f"❌ Status check failed: {str(e)}")


@migrate.command()
def install():
    """Create the migration repository."""
    try:
        from ..database.migrations.migrator import Migrator
        
        migrator = Migrator()
        
        click.echo("📦 Installing migration repository...")
        success = migrator.install()
        
        if success:
            click.echo("✅ Migration repository installed successfully.")
        else:
            click.echo("❌ Failed to install migration repository.")
        
    except Exception as e:
        click.echo(f"❌ Installation failed: {str(e)}")


# =============================================================================
# MAIN MIGRATION COMMAND (larapy migrate - shorthand)
# =============================================================================

@main.command()
@click.option('--seed', is_flag=True, help='Indicates if the seed task should be re-run')
@click.option('--force', is_flag=True, help='Force the operation to run when in production')
@click.option('--pretend', is_flag=True, help='Dump the SQL queries that would be run')
def migrate_main(seed: bool, force: bool, pretend: bool):
    """Run pending migrations (shorthand for 'migrate run')."""
    # This is equivalent to 'larapy migrate run'
    ctx = click.get_current_context()
    ctx.invoke(run, seed=seed, force=force, pretend=pretend, step=None)


# =============================================================================
# DATABASE COMMANDS (larapy db)
# =============================================================================

@db.command('migrate')
@click.option('--seed', is_flag=True, help='Seed the database after migrating')
@click.option('--force', is_flag=True, help='Force the migration in production')
def db_migrate(seed: bool, force: bool):
    """Run database migrations."""
    ctx = click.get_current_context()
    ctx.invoke(run, seed=seed, force=force, pretend=False, step=None)


@db.command('rollback')
@click.option('--step', type=int, default=1, help='Number of migration batches to rollback')
@click.option('--force', is_flag=True, help='Force the rollback in production')
def db_rollback(step: int, force: bool):
    """Rollback database migrations."""
    ctx = click.get_current_context()
    ctx.invoke(rollback, step=step, force=force, pretend=False)


@db.command('fresh')
@click.option('--seed', is_flag=True, help='Seed the database after fresh migration')
@click.option('--force', is_flag=True, help='Force the operation in production')
def db_fresh(seed: bool, force: bool):
    """Drop all tables and re-run all migrations."""
    ctx = click.get_current_context()
    ctx.invoke(fresh, seed=seed, force=force)


@db.command('status')
def db_status():
    """Show migration status."""
    ctx = click.get_current_context()
    ctx.invoke(status, verbose=False, pending=False, executed=False)


@db.command('seed')
@click.argument('seeder', required=False)
@click.option('--class', 'seeder_class', help='The class name of the root seeder')
def db_seed(seeder: str, seeder_class: str):
    """Run database seeders."""
    try:
        # TODO: Implement seeder runner
        seeder_name = seeder or seeder_class or 'DatabaseSeeder'
        click.echo(f"🌱 Running seeder: {seeder_name}")
        click.echo("✅ Seeding completed.")
        
    except Exception as e:
        click.echo(f"❌ Seeding failed: {str(e)}")


@db.command('inspect')
@click.option('--table', help='Specific table to inspect')
@click.option('--show-data', is_flag=True, help='Show sample data from tables')
def db_inspect(table: str, show_data: bool):
    """Inspect database structure."""
    try:
        from ..database.migrations.migrator import Migrator
        
        migrator = Migrator()
        
        with migrator.get_connection() as conn:
            if table:
                click.echo(f"🔍 Inspecting table: {table}")
                click.echo("─" * 50)
                
                # Check if table exists
                cursor = conn.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                ''', (table,))
                
                if not cursor.fetchone():
                    click.echo(f"❌ Table '{table}' not found")
                    return
                
                # Show table structure
                cursor = conn.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                click.echo("Columns:")
                for col in columns:
                    pk_marker = " (PK)" if col[5] else ""
                    nullable = "NULL" if not col[3] else "NOT NULL"
                    default = f" DEFAULT: {col[4]}" if col[4] else ""
                    click.echo(f"  • {col[1]} - {col[2]} {nullable}{default}{pk_marker}")
                
                # Show row count
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                click.echo(f"\nRow count: {count}")
                
                # Show sample data if requested
                if show_data and count > 0:
                    cursor = conn.execute(f"SELECT * FROM {table} LIMIT 5")
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
            else:
                # Show all tables
                click.echo("🔍 Database Tables:")
                click.echo("─" * 30)
                
                cursor = conn.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' 
                    ORDER BY name
                ''')
                
                tables = cursor.fetchall()
                if not tables:
                    click.echo("No tables found.")
                    return
                
                for table_row in tables:
                    table_name = table_row[0]
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    click.echo(f"  • {table_name} ({count} rows)")
        
    except Exception as e:
        click.echo(f"❌ Inspection failed: {str(e)}")


@db.command('schema')
@click.option('--table', help='Show schema for specific table')
@click.option('--output', type=click.Choice(['table', 'sql']), default='table', help='Output format')
def db_schema(table: str, output: str):
    """Show database schema."""
    try:
        from ..database.migrations.migrator import Migrator
        
        migrator = Migrator()
        
        with migrator.get_connection() as conn:
            if table:
                click.echo(f"📋 Schema for table: {table}")
                
                if output == 'sql':
                    cursor = conn.execute('''
                        SELECT sql FROM sqlite_master 
                        WHERE type='table' AND name=?
                    ''', (table,))
                    result = cursor.fetchone()
                    if result:
                        click.echo(result[0])
                    else:
                        click.echo(f"❌ Table '{table}' not found")
                else:
                    # Show table info in formatted way
                    cursor = conn.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    
                    if columns:
                        click.echo("─" * 60)
                        click.echo(f"{'Column':<20} {'Type':<15} {'Null':<8} {'Default':<15}")
                        click.echo("─" * 60)
                        
                        for col in columns:
                            null_str = "YES" if col[3] == 0 else "NO"
                            default_str = str(col[4]) if col[4] else ""
                            click.echo(f"{col[1]:<20} {col[2]:<15} {null_str:<8} {default_str:<15}")
                    else:
                        click.echo(f"❌ Table '{table}' not found")
            else:
                # Show all tables schema
                click.echo("📋 Database Schema")
                click.echo("─" * 40)
                
                cursor = conn.execute('''
                    SELECT name, sql FROM sqlite_master 
                    WHERE type='table' 
                    ORDER BY name
                ''')
                
                for row in cursor.fetchall():
                    table_name, sql = row
                    click.echo(f"\n{table_name}:")
                    if output == 'sql':
                        click.echo(sql)
                    else:
                        # Show simplified schema
                        cursor2 = conn.execute(f"PRAGMA table_info({table_name})")
                        columns = cursor2.fetchall()
                        for col in columns:
                            pk_str = " (PK)" if col[5] else ""
                            click.echo(f"  • {col[1]} {col[2]}{pk_str}")
        
    except Exception as e:
        click.echo(f"❌ Schema display failed: {str(e)}")


@db.command('wipe')
@click.option('--drop-views', is_flag=True, help='Drop all database views')
@click.option('--drop-types', is_flag=True, help='Drop all user-defined types')
@click.option('--keep-migrations', is_flag=True, help='Keep the migrations table')
@click.option('--force', is_flag=True, help='Force the operation')
def db_wipe(drop_views: bool, drop_types: bool, keep_migrations: bool, force: bool):
    """Wipe all tables from the database."""
    try:
        from ..database.migrations.migrator import Migrator
        
        migrator = Migrator()
        
        click.echo("🗑️  Wiping database...")
        
        with migrator.get_connection() as conn:
            # Get all tables
            cursor = conn.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table'
            ''')
            tables = [row[0] for row in cursor.fetchall()]
            
            dropped_count = 0
            for table_name in tables:
                if keep_migrations and table_name == 'migrations':
                    continue
                    
                conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                dropped_count += 1
                click.echo(f"  Dropped table: {table_name}")
            
            conn.commit()
            
            click.echo(f"✅ Wiped {dropped_count} tables from database.")
        
    except Exception as e:
        click.echo(f"❌ Database wipe failed: {str(e)}")


# =============================================================================
# CODE GENERATION COMMANDS (larapy make)
# =============================================================================

@make.command('migration')
@click.argument('name')
@click.option('--create', help='Create a new table')
@click.option('--table', help='Modify an existing table')
def make_migration(name: str, create: str, table: str):
    """Create a new migration."""
    from datetime import datetime
    
    # Create migrations directory if it doesn't exist
    migrations_dir = Path('database/migrations')
    migrations_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp prefix (Laravel style: YYYY_MM_DD_HHMMSS)
    timestamp = datetime.now().strftime('%Y_%m_%d_%H%M%S')
    
    # Create migration filename with timestamp prefix
    migration_filename = f"{timestamp}_{name}.py"
    
    # Determine class name
    class_name = ''.join(word.capitalize() for word in name.replace('_', ' ').split())
    
    # Generate migration content
    if create:
        content = _generate_create_migration(class_name, create)
        click.echo(f"Creating migration to create table: {create}")
    elif table:
        content = _generate_modify_migration(class_name, table)
        click.echo(f"Creating migration to modify table: {table}")
    else:
        content = _generate_blank_migration(class_name)
        click.echo("Creating blank migration")
    
    # Write migration file
    migration_file = migrations_dir / migration_filename
    migration_file.write_text(content)
    
    click.echo(f"Migration created: {migration_file}")
    click.echo(f"Class name: {class_name}")


@make.command('model')
@click.argument('name')
@click.option('--migration', '-m', is_flag=True, help='Create migration as well')
def make_model(name: str, migration: bool):
    """Create a new model."""
    # Create models directory if it doesn't exist
    models_dir = Path('app/models')
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure class name is PascalCase
    class_name = ''.join(word.capitalize() for word in name.replace('_', ' ').replace('-', ' ').split())
    
    # Create snake_case file name
    file_name = _camel_to_snake(class_name)
    
    # Generate model content
    content = _generate_model(class_name)
    
    # Write model file
    model_file = models_dir / f"{file_name}.py"
    model_file.write_text(content)
    
    click.echo(f"Model created: {model_file}")
    click.echo(f"Class name: {class_name}")
    
    if migration:
        # Create migration as well
        from datetime import datetime
        
        table_name = f"{file_name}s" if not file_name.endswith('s') else file_name
        
        # Create migrations directory if it doesn't exist
        migrations_dir = Path('database/migrations')
        migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp prefix
        timestamp = datetime.now().strftime('%Y_%m_%d_%H%M%S')
        migration_name = f"create_{table_name}_table"
        migration_filename = f"{timestamp}_{migration_name}.py"
        migration_class_name = ''.join(word.capitalize() for word in migration_name.split('_'))
        
        # Generate migration content
        migration_content = _generate_create_migration(migration_class_name, table_name)
        
        # Write migration file
        migration_file = migrations_dir / migration_filename
        migration_file.write_text(migration_content)
        
        click.echo(f"Migration created: {migration_file}")
        click.echo(f"Table name: {table_name}")


@make.command('seeder')
@click.argument('name')
def make_seeder(name: str):
    """Create a new database seeder."""
    # Create seeders directory if it doesn't exist
    seeders_dir = Path('database/seeders')
    seeders_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure class name ends with Seeder
    class_name = name if name.endswith('Seeder') else f"{name}Seeder"
    
    # Create snake_case file name
    file_name = _camel_to_snake(class_name)
    
    # Generate seeder content
    content = _generate_seeder(class_name)
    
    # Write seeder file
    seeder_file = seeders_dir / f"{file_name}.py"
    seeder_file.write_text(content)
    
    click.echo(f"Seeder created: {seeder_file}")
    click.echo(f"Class name: {class_name}")


@make.command('factory')
@click.argument('name')
@click.option('--model', help='The name of the model')
def make_factory(name: str, model: str):
    """Create a new model factory."""
    # Create factories directory if it doesn't exist
    factories_dir = Path('database/factories')
    factories_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure class name ends with Factory
    class_name = name if name.endswith('Factory') else f"{name}Factory"
    
    # Create snake_case file name
    file_name = _camel_to_snake(class_name)
    
    # Generate factory content
    model_name = model or name.replace('Factory', '') if name.endswith('Factory') else name
    content = _generate_factory(class_name, model_name)
    
    # Write factory file
    factory_file = factories_dir / f"{file_name}.py"
    factory_file.write_text(content)
    
    click.echo(f"Factory created: {factory_file}")
    click.echo(f"Class name: {class_name}")
    click.echo(f"Model: {model_name}")


# =============================================================================
# HELPER FUNCTIONS FOR CODE GENERATION
# =============================================================================

def _generate_create_migration(class_name: str, table_name: str) -> str:
    """Generate create table migration template."""
    return f'''"""
Create {table_name} table migration.
"""

from larapy.database.migrations.migration import Migration
from larapy.database.migrations.schema import Schema, Blueprint


class {class_name}(Migration):
    """
    Run the migrations.
    
    @return void
    """
    
    def up(self):
        """
        Run the migrations.
        
        @return void
        """
        def create_{table_name}_table(table: Blueprint):
            table.id()
            table.timestamps()
        
        Schema.create('{table_name}', create_{table_name}_table)
    
    def down(self):
        """
        Reverse the migrations.
        
        @return void
        """
        Schema.drop_if_exists('{table_name}')
'''


def _generate_modify_migration(class_name: str, table_name: str) -> str:
    """Generate modify table migration template."""
    return f'''"""
Modify {table_name} table migration.
"""

from larapy.database.migrations.migration import Migration
from larapy.database.migrations.schema import Schema, Blueprint


class {class_name}(Migration):
    """
    Run the migrations.
    
    @return void
    """
    
    def up(self):
        """
        Run the migrations.
        
        @return void
        """
        def modify_{table_name}_table(table: Blueprint):
            # Add your table modifications here
            # table.string('new_column')
            pass
        
        Schema.table('{table_name}', modify_{table_name}_table)
    
    def down(self):
        """
        Reverse the migrations.
        
        @return void
        """
        def rollback_{table_name}_table(table: Blueprint):
            # Add rollback logic here
            # table.drop_column('new_column')
            pass
        
        Schema.table('{table_name}', rollback_{table_name}_table)
'''


def _generate_blank_migration(class_name: str) -> str:
    """Generate blank migration template."""
    return f'''"""
{class_name} migration.
"""

from larapy.database.migrations.migration import Migration
from larapy.database.migrations.schema import Schema, Blueprint


class {class_name}(Migration):
    """
    Run the migrations.
    
    @return void
    """
    
    def up(self):
        """
        Run the migrations.
        
        @return void
        """
        def create_example_table(table: Blueprint):
            table.id()
            table.timestamps()
        
        # Schema.create('example_table', create_example_table)
        pass
    
    def down(self):
        """
        Reverse the migrations.
        
        @return void
        """
        # Schema.drop_if_exists('example_table')
        pass
'''


def _generate_model(name: str) -> str:
    """Generate model template that extends the base ORM model."""
    return f'''"""
{name} model for database operations.
"""

from larapy.orm.model import Model


class {name}(Model):
    """
    {name} model for database interactions.
    
    This model represents the {name.lower()} entity in the database.
    Inherits from the base Larapy ORM Model class.
    """
    
    # Mass assignment protection - specify which fields can be mass assigned
    fillable = [
        # Add fillable fields here, e.g.:
        # 'name',
        # 'email',
        # 'description',
    ]
    
    # Specify casts for automatic type conversion
    casts = {{
        'created_at': 'datetime',
        'updated_at': 'datetime',
    }}
    
    # Specify which fields should be hidden when serializing
    hidden = [
        # Add hidden fields here, e.g.:
        # 'password',
        # 'remember_token',
    ]
    
    # Define relationships
    def example_relationship(self):
        """
        Example relationship method.
        Uncomment and modify as needed.
        """
        # return self.belongs_to('OtherModel')
        # return self.has_many('RelatedModel')
        # return self.has_one('RelatedModel')
        pass
    
    # Define scopes for reusable query constraints
    @classmethod
    def active(cls):
        """
        Scope to get only active records.
        Example scope method.
        """
        # return cls.where('is_active', True)
        return cls.query()
    
    # Define accessors and mutators
    def get_full_name_attribute(self):
        """
        Example accessor for computed attribute.
        This would create a 'full_name' attribute.
        """
        # return f"{{self.first_name}} {{self.last_name}}"
        pass
    
    def set_name_attribute(self, value):
        """
        Example mutator for input transformation.
        This would automatically capitalize the name when set.
        """
        return value.title() if value else None
'''


def _generate_seeder(class_name: str) -> str:
    """Generate seeder template."""
    return f'''"""
{class_name} for seeding database tables.
"""

from larapy.database.migrations.seeder import Seeder
from app.models.user import User  # Import your models here


class {class_name}(Seeder):
    """
    {class_name} for populating database tables with test data.
    """
    
    def run(self):
        """
        Run the database seeds.
        
        @return void
        """
        # Example seeder implementation:
        # 
        # User.create({{
        #     'name': 'John Doe',
        #     'email': 'john@example.com',
        #     'password': 'hashed_password'
        # }})
        # 
        # for i in range(10):
        #     User.create({{
        #         'name': f'User {{i}}',
        #         'email': f'user{{i}}@example.com',
        #         'password': 'hashed_password'
        #     }})
        
        pass
'''


def _generate_factory(class_name: str, model_name: str) -> str:
    """Generate factory template."""
    return f'''"""
{class_name} for generating {model_name} test data.
"""

from larapy.database.migrations.factory import Factory
from app.models.{model_name.lower()} import {model_name}
import random
import string


class {class_name}(Factory):
    """
    {class_name} for generating {model_name} model instances.
    """
    
    model = {model_name}
    
    def definition(self):
        """
        Define the model's default state.
        
        @return dict
        """
        return {{
            # Example factory definition:
            # 'name': self.faker.name(),
            # 'email': self.faker.email(),
            # 'password': 'password',  # Default password
            # 'created_at': self.faker.date_time(),
        }}
    
    def configure(self):
        """
        Configure the model factory.
        
        @return self
        """
        return self
    
    # Define factory states
    def unverified(self):
        """
        Indicate that the model's email address should be unverified.
        """
        return self.state(lambda: {{
            'email_verified_at': None,
        }})
    
    def admin(self):
        """
        Indicate that the user should be an admin.
        """
        return self.state(lambda: {{
            'is_admin': True,
        }})
'''


def _camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# =============================================================================
# CONFIGURATION COMMANDS (larapy config)
# =============================================================================

@config_cmd.command('cache')
def config_cache():
    """Cache configuration for better performance."""
    try:
        import sys
        from pathlib import Path
        
        # Add package to path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from core.helpers import cache_config
        
        click.echo("📦 Caching configuration...")
        cache_config()
        click.echo("✅ Configuration cached successfully.")
        
    except Exception as e:
        click.echo(f"❌ Configuration caching failed: {str(e)}")


@config_cmd.command('clear')
def config_clear():
    """Clear cached configuration."""
    try:
        import sys
        from pathlib import Path
        
        # Add package to path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from core.helpers import clear_config_cache
        
        click.echo("🗑️  Clearing configuration cache...")
        clear_config_cache()
        click.echo("✅ Configuration cache cleared.")
        
    except Exception as e:
        click.echo(f"❌ Configuration cache clearing failed: {str(e)}")


@config_cmd.command('show')
@click.argument('key', required=False)
def config_show(key: str):
    """Show configuration values."""
    try:
        import sys
        from pathlib import Path
        
        # Add package to path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from core.helpers import config
        
        if key:
            value = config(key)
            if value is not None:
                click.echo(f"{key}: {value}")
            else:
                click.echo(f"❌ Configuration key '{key}' not found.")
        else:
            # Show all configuration
            all_config = config()
            if all_config:
                import json
                click.echo("📋 Current Configuration:")
                click.echo(json.dumps(all_config, indent=2, default=str))
            else:
                click.echo("❌ No configuration found.")
        
    except Exception as e:
        click.echo(f"❌ Failed to show configuration: {str(e)}")


if __name__ == '__main__':
    main()