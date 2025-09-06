"""
Larapy Migration System - Laravel-like Migration Management

This module provides comprehensive migration tracking with automatic migration table
management, batch tracking, and rollback capabilities using Laravel-style configuration.
"""

import os
import re
import sqlite3
import importlib
import importlib.util
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

# Import the config helper
import sys
from pathlib import Path as PathLib

# Try to import helpers with better path resolution
def _import_helpers():
    """Import configuration helpers with multiple fallback strategies."""
    
    # Strategy 1: Relative import (when used as package)
    try:
        from ..core.helpers import config, env, database_path
        return config, env, database_path
    except ImportError:
        pass
    
    # Strategy 2: Direct import (when core is in path)
    try:
        from core.helpers import config, env, database_path
        return config, env, database_path
    except ImportError:
        pass
    
    # Strategy 3: Add package to path and import
    try:
        # Find the package directory
        current_file = PathLib(__file__)
        # Go up from migrations/migrator.py to package root
        package_root = current_file.parent.parent.parent
        
        if str(package_root) not in sys.path:
            sys.path.insert(0, str(package_root))
        
        from core.helpers import config, env, database_path
        return config, env, database_path
    except ImportError:
        pass
    
    # Strategy 4: Look for documentation website and import from package
    try:
        current_file = PathLib(__file__)
        # Look for pattern: .../package-larapy/database/migrations/migrator.py
        # and find .../package-larapy/core/helpers.py
        possible_helpers = current_file.parent.parent.parent / 'core' / 'helpers.py'
        
        if possible_helpers.exists():
            spec = importlib.util.spec_from_file_location("core.helpers", possible_helpers)
            if spec and spec.loader:
                helpers_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(helpers_module)
                return helpers_module.config, helpers_module.env, helpers_module.database_path
    except Exception:
        pass
    
    # Last resort fallback - return dummy functions
    def config(key, default=None):
        return default
    
    def env(key, default=None):
        return os.getenv(key, default)
    
    def database_path(path=''):
        return 'database/database.sqlite'
    
    return config, env, database_path

# Import helpers using the improved strategy
config, env, database_path = _import_helpers()


@dataclass
class MigrationRecord:
    """Represents a migration record in the migrations table."""
    id: int
    migration: str
    batch: int
    executed_at: datetime


@dataclass
class MigrationFile:
    """Represents a migration file."""
    filename: str
    name: str
    path: Path
    timestamp: str


class Migrator:
    """
    Laravel-like Migration Manager for Larapy.
    
    Handles migration tracking, execution, and rollback with automatic
    migration table management using Laravel-style configuration.
    """
    
    def __init__(self, connection: Optional[str] = None):
        """
        Initialize the migrator.
        
        Args:
            connection: Database connection name (defaults to default connection)
        """
        # Load configuration using config() helper
        self.connection = connection or config('database.default', 'sqlite')
        
        # Get database configuration
        db_config = config(f'database.connections.{self.connection}', {})
        
        driver = db_config.get('driver')
        if driver == 'sqlite':
            self.database_path = db_config.get('database', 'database/database.sqlite')
            self.database_type = 'sqlite'
        elif driver == 'mysql':
            self.mysql_config = {
                'host': db_config.get('host', '127.0.0.1'),
                'port': db_config.get('port', 3306),
                'database': db_config.get('database', ''),
                'username': db_config.get('username', ''),
                'password': db_config.get('password', ''),
                'charset': db_config.get('charset', 'utf8mb4')
            }
            self.database_type = 'mysql'
        else:
            raise ValueError(f"Unsupported database driver: {driver}")
        
        # Get migrations table name from config
        self.migration_table = config('database.migrations', 'migrations')
        
        # Set migrations directory
        self.migrations_dir = Path('database/migrations')
        
        # Ensure database directory exists (only for SQLite)
        if self.database_type == 'sqlite' and hasattr(self, 'database_path'):
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        
    def get_connection(self):
        """Get database connection."""
        if self.database_type == 'sqlite':
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            return conn
        elif self.database_type == 'mysql':
            import mysql.connector
            return mysql.connector.connect(
                host=self.mysql_config['host'],
                port=self.mysql_config['port'],
                database=self.mysql_config['database'],
                user=self.mysql_config['username'],
                password=self.mysql_config['password'],
                charset=self.mysql_config['charset']
            )
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")
    
    def _execute_query(self, query: str, params: tuple = (), fetch: str = None):
        """Execute a database query with proper handling for different database types."""
        with self.get_connection() as conn:
            if self.database_type == 'mysql':
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch == 'one':
                    result = cursor.fetchone()
                    if result:
                        # Convert MySQL result to dict-like object
                        columns = [desc[0] for desc in cursor.description]
                        result = dict(zip(columns, result))
                elif fetch == 'all':
                    rows = cursor.fetchall()
                    if rows:
                        columns = [desc[0] for desc in cursor.description]
                        result = [dict(zip(columns, row)) for row in rows]
                    else:
                        result = []
                else:
                    result = None
                
                if not fetch:
                    conn.commit()
                
                cursor.close()
                return result
            else:  # SQLite
                cursor = conn.execute(query, params)
                
                if fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'all':
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return None
        
    def create_migrations_table(self) -> None:
        """
        Create the migrations table if it doesn't exist.
        This is called automatically on first migration command.
        """
        if self.database_type == 'sqlite':
            sql = f'''
                CREATE TABLE IF NOT EXISTS {self.migration_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration VARCHAR(255) NOT NULL,
                    batch INTEGER NOT NULL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        elif self.database_type == 'mysql':
            sql = f'''
                CREATE TABLE IF NOT EXISTS {self.migration_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    migration VARCHAR(255) NOT NULL,
                    batch INT NOT NULL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        
        self._execute_query(sql)
    
    def migrations_table_exists(self) -> bool:
        """Check if migrations table exists."""
        if self.database_type == 'sqlite':
            sql = f'''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{self.migration_table}'
            '''
        elif self.database_type == 'mysql':
            sql = f'''
                SELECT TABLE_NAME FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = '{self.mysql_config["database"]}' 
                AND TABLE_NAME = '{self.migration_table}'
            '''
        
        result = self._execute_query(sql, fetch='one')
        return result is not None
    
    def get_migration_files(self) -> List[MigrationFile]:
        """Get all migration files from the migrations directory."""
        if not self.migrations_dir.exists():
            return []
        
        migration_files = []
        for file_path in self.migrations_dir.glob('*.py'):
            if file_path.name.startswith('__'):
                continue
                
            # Extract timestamp and name from filename
            filename = file_path.stem
            parts = filename.split('_', 4)
            if len(parts) >= 4:
                timestamp = f"{parts[0]}_{parts[1]}_{parts[2]}_{parts[3]}"
                name = '_'.join(parts[4:]) if len(parts) > 4 else 'unnamed'
            else:
                timestamp = filename
                name = filename
            
            migration_files.append(MigrationFile(
                filename=filename,
                name=name,
                path=file_path,
                timestamp=timestamp
            ))
        
        # Sort by timestamp
        migration_files.sort(key=lambda x: x.timestamp)
        return migration_files
    
    def get_executed_migrations(self) -> List[MigrationRecord]:
        """Get all executed migrations from the database."""
        # Ensure migrations table exists
        if not self.migrations_table_exists():
            return []
        
        sql = f'''
            SELECT id, migration, batch, executed_at 
            FROM {self.migration_table} 
            ORDER BY batch, migration
        '''
        
        rows = self._execute_query(sql, fetch='all')
        if not rows:
            return []
        
        records = []
        for row in rows:
            records.append(MigrationRecord(
                id=row['id'],
                migration=row['migration'],
                batch=row['batch'],
                executed_at=datetime.fromisoformat(str(row['executed_at']))
            ))
        
        return records
    
    def get_pending_migrations(self) -> List[MigrationFile]:
        """Get migrations that haven't been executed yet."""
        all_files = self.get_migration_files()
        executed = {record.migration for record in self.get_executed_migrations()}
        
        return [file for file in all_files if file.filename not in executed]
    
    def get_last_batch_number(self) -> int:
        """Get the highest batch number."""
        if not self.migrations_table_exists():
            return 0
        
        sql = f'SELECT MAX(batch) as max_batch FROM {self.migration_table}'
        result = self._execute_query(sql, fetch='one')
        return result['max_batch'] if result and result['max_batch'] else 0
    
    def record_migration(self, migration_name: str, batch: int) -> None:
        """Record a migration execution in the database."""
        sql = f'''
            INSERT INTO {self.migration_table} (migration, batch, executed_at)
            VALUES (%s, %s, %s)
        ''' if self.database_type == 'mysql' else f'''
            INSERT INTO {self.migration_table} (migration, batch, executed_at)
            VALUES (?, ?, ?)
        '''
        
        self._execute_query(sql, (migration_name, batch, datetime.now().isoformat()))
    
    def remove_migration_record(self, migration_name: str) -> None:
        """Remove a migration record (for rollback)."""
        sql = f'''
            DELETE FROM {self.migration_table} WHERE migration = %s
        ''' if self.database_type == 'mysql' else f'''
            DELETE FROM {self.migration_table} WHERE migration = ?
        '''
        
        self._execute_query(sql, (migration_name,))
    
    def get_migrations_to_rollback(self, step: int = 1) -> List[MigrationRecord]:
        """Get migrations to rollback based on batch count."""
        if not self.migrations_table_exists():
            return []
        
        with self.get_connection() as conn:
            # Get distinct batches in descending order
            cursor = conn.execute(f'''
                SELECT DISTINCT batch FROM {self.migration_table} 
                ORDER BY batch DESC LIMIT ?
            ''', (step,))
            
            batches = [row['batch'] for row in cursor.fetchall()]
            
            if not batches:
                return []
            
            # Get all migrations from these batches
            placeholders = ','.join('?' * len(batches))
            cursor = conn.execute(f'''
                SELECT id, migration, batch, executed_at 
                FROM {self.migration_table} 
                WHERE batch IN ({placeholders})
                ORDER BY batch DESC, migration DESC
            ''', batches)
            
            records = []
            for row in cursor.fetchall():
                records.append(MigrationRecord(
                    id=row['id'],
                    migration=row['migration'],
                    batch=row['batch'],
                    executed_at=datetime.fromisoformat(row['executed_at'])
                ))
            return records
    
    def run_migration_file(self, migration_file: MigrationFile, direction: str = 'up') -> bool:
        """Execute a migration file."""
        try:
            # Import the migration module
            spec = importlib.util.spec_from_file_location(
                f"migration_{migration_file.filename}", 
                migration_file.path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the migration class
            migration_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and 
                    hasattr(obj, 'up') and 
                    hasattr(obj, 'down') and
                    name != 'Migration'):
                    migration_class = obj
                    break
            
            if migration_class is None:
                print(f"❌ No migration class found in {migration_file.filename}")
                return False
            
            # Execute migration
            migration_instance = migration_class()
            if direction == 'up':
                migration_instance.up()
            elif direction == 'down':
                migration_instance.down()
            else:
                print(f"❌ Invalid migration direction: {direction}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error running migration {migration_file.filename}: {str(e)}")
            return False
    
    def migrate(self, step: Optional[int] = None, pretend: bool = False, seed: bool = False) -> int:
        """
        Run pending migrations.
        
        Args:
            step: Maximum number of migrations to run
            pretend: Show SQL without executing
            seed: Run seeders after migration
            
        Returns:
            Number of migrations executed
        """
        # Ensure migrations table exists
        self.create_migrations_table()
        
        # Get pending migrations
        pending = self.get_pending_migrations()
        
        if step:
            pending = pending[:step]
        
        if not pending:
            return 0
        
        # Get next batch number
        next_batch = self.get_last_batch_number() + 1
        
        if pretend:
            print("🔍 The following migrations would be executed:")
            for migration in pending:
                print(f"  - {migration.filename}")
            return len(pending)
        
        # Execute migrations
        executed_count = 0
        for migration_file in pending:
            print(f"🚀 Running migration: {migration_file.filename}")
            
            if self.run_migration_file(migration_file, 'up'):
                self.record_migration(migration_file.filename, next_batch)
                executed_count += 1
                print(f"✅ Migrated: {migration_file.filename}")
            else:
                print(f"❌ Failed: {migration_file.filename}")
                break
        
        if seed and executed_count > 0:
            print("🌱 Running seeders...")
            # TODO: Implement seeder runner
            
        return executed_count
    
    def rollback(self, step: int = 1, pretend: bool = False) -> int:
        """
        Rollback migrations.
        
        Args:
            step: Number of batches to rollback
            pretend: Show what would be rolled back
            
        Returns:
            Number of migrations rolled back
        """
        # Ensure migrations table exists
        if not self.migrations_table_exists():
            print("❌ No migrations table found. Nothing to rollback.")
            return 0
        
        # Get migrations to rollback
        to_rollback = self.get_migrations_to_rollback(step)
        
        if not to_rollback:
            print("✅ Nothing to rollback.")
            return 0
        
        if pretend:
            print("🔍 The following migrations would be rolled back:")
            for migration in to_rollback:
                print(f"  - {migration.migration} (batch {migration.batch})")
            return len(to_rollback)
        
        # Execute rollbacks
        rolled_back_count = 0
        migration_files = {f.filename: f for f in self.get_migration_files()}
        
        for migration_record in to_rollback:
            migration_file = migration_files.get(migration_record.migration)
            
            if migration_file is None:
                print(f"⚠️  Migration file not found: {migration_record.migration}")
                continue
            
            print(f"🔄 Rolling back: {migration_record.migration}")
            
            if self.run_migration_file(migration_file, 'down'):
                self.remove_migration_record(migration_record.migration)
                rolled_back_count += 1
                print(f"✅ Rolled back: {migration_record.migration}")
            else:
                print(f"❌ Failed to rollback: {migration_record.migration}")
                break
        
        return rolled_back_count
    
    def reset(self, pretend: bool = False) -> int:
        """Rollback all migrations."""
        if not self.migrations_table_exists():
            print("❌ No migrations table found. Nothing to reset.")
            return 0
        
        # Get all executed migrations
        executed = self.get_executed_migrations()
        
        if not executed:
            print("✅ No migrations to reset.")
            return 0
        
        # Rollback all batches
        max_batch = max(record.batch for record in executed)
        return self.rollback(step=max_batch, pretend=pretend)
    
    def refresh(self, seed: bool = False) -> Tuple[int, int]:
        """Reset and re-run all migrations."""
        reset_count = self.reset()
        migrate_count = self.migrate(seed=seed)
        return reset_count, migrate_count
    
    def fresh(self, seed: bool = False) -> int:
        """Drop all tables and re-run migrations."""
        # Drop all tables except SQLite system tables
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row['name'] for row in cursor.fetchall()]
            
            for table in tables:
                conn.execute(f"DROP TABLE IF EXISTS {table}")
            conn.commit()
        
        print("✅ Dropped all tables.")
        
        # Run migrations
        migrate_count = self.migrate(seed=seed)
        return migrate_count
    
    def status(self, verbose: bool = False, pending: bool = False, executed: bool = False) -> Dict[str, Any]:
        """
        Show migration status.
        
        Args:
            verbose: Show detailed information
            pending: Show only pending migrations
            executed: Show only executed migrations
            
        Returns:
            Migration status information
        """
        # Ensure migrations table exists for status check
        self.create_migrations_table()
        
        all_files = self.get_migration_files()
        executed_records = {record.migration: record for record in self.get_executed_migrations()}
        
        status_info = {
            'total': len(all_files),
            'executed': len(executed_records),
            'pending': len(all_files) - len(executed_records),
            'migrations': []
        }
        
        for migration_file in all_files:
            record = executed_records.get(migration_file.filename)
            migration_info = {
                'filename': migration_file.filename,
                'name': migration_file.name,
                'executed': record is not None,
                'batch': record.batch if record else None,
                'executed_at': record.executed_at if record else None
            }
            
            # Filter based on options
            if pending and migration_info['executed']:
                continue
            if executed and not migration_info['executed']:
                continue
                
            status_info['migrations'].append(migration_info)
        
        return status_info
    
    def install(self) -> bool:
        """Install migration repository (create migrations table)."""
        try:
            self.create_migrations_table()
            return True
        except Exception as e:
            print(f"❌ Failed to install migration repository: {str(e)}")
            return False