"""
Migration system for Larapy.

This module provides the Migrator class that handles running migrations,
tracking migration status, and performing rollbacks.
"""

import os
import re
import importlib
import importlib.util
from typing import Dict, List, Optional, Tuple, Type, Any
from datetime import datetime
from pathlib import Path
from ..connection import DatabaseManager
from .migration import Migration


class MigrationRecord:
    """Represents a migration record in the database."""
    
    def __init__(self, id: int, migration: str, batch: int, ran_at: datetime):
        self.id = id
        self.migration = migration
        self.batch = batch
        self.ran_at = ran_at


class Migrator:
    """Handles database migrations."""
    
    def __init__(self, db_manager: DatabaseManager, migration_path: str = None):
        self.db_manager = db_manager
        self.migration_path = migration_path or 'database/migrations'
        self.migration_table = 'migrations'
        
    async def run(self, connection: Optional[str] = None, pretend: bool = False,
                 step: Optional[int] = None) -> List[str]:
        """Run pending migrations."""
        # Ensure migration table exists
        await self._create_migration_table(connection)
        
        # Get pending migrations
        pending = await self.get_pending_migrations(connection)
        
        if step:
            pending = pending[:step]
            
        if not pending:
            return []
            
        # Get next batch number
        next_batch = await self._get_next_batch_number(connection)
        
        # Run migrations
        ran_migrations = []
        for migration_file in pending:
            if pretend:
                print(f"Would run: {migration_file}")
                ran_migrations.append(migration_file)
            else:
                success = await self._run_migration(migration_file, 'up', connection, next_batch)
                if success:
                    ran_migrations.append(migration_file)
                    
        return ran_migrations
        
    async def rollback(self, connection: Optional[str] = None, pretend: bool = False,
                      step: int = 1) -> List[str]:
        """Rollback migrations."""
        # Get migrations to rollback
        to_rollback = await self._get_migrations_to_rollback(step, connection)
        
        if not to_rollback:
            return []
            
        # Rollback migrations
        rolled_back = []
        for migration_record in to_rollback:
            if pretend:
                print(f"Would rollback: {migration_record.migration}")
                rolled_back.append(migration_record.migration)
            else:
                success = await self._run_migration(migration_record.migration, 'down', connection)
                if success:
                    await self._delete_migration_record(migration_record.migration, connection)
                    rolled_back.append(migration_record.migration)
                    
        return rolled_back
        
    async def reset(self, connection: Optional[str] = None, pretend: bool = False) -> List[str]:
        """Rollback all migrations."""
        # Get all ran migrations
        ran_migrations = await self._get_ran_migrations(connection)
        ran_migrations.reverse()  # Rollback in reverse order
        
        if not ran_migrations:
            return []
            
        # Rollback all migrations
        rolled_back = []
        for migration_record in ran_migrations:
            if pretend:
                print(f"Would rollback: {migration_record.migration}")
                rolled_back.append(migration_record.migration)
            else:
                success = await self._run_migration(migration_record.migration, 'down', connection)
                if success:
                    await self._delete_migration_record(migration_record.migration, connection)
                    rolled_back.append(migration_record.migration)
                    
        return rolled_back
        
    async def refresh(self, connection: Optional[str] = None, pretend: bool = False,
                     step: Optional[int] = None) -> Dict[str, List[str]]:
        """Rollback all migrations and run them again."""
        rolled_back = await self.reset(connection, pretend)
        ran = await self.run(connection, pretend, step)
        
        return {
            'rolled_back': rolled_back,
            'ran': ran
        }
        
    async def fresh(self, connection: Optional[str] = None, pretend: bool = False) -> List[str]:
        """Drop all tables and re-run all migrations."""
        if pretend:
            print("Would drop all tables and re-run migrations")
            return await self.get_pending_migrations(connection)
        else:
            # Drop all tables (implementation depends on database driver)
            await self._drop_all_tables(connection)
            
            # Re-create migration table
            await self._create_migration_table(connection)
            
            # Run all migrations
            return await self.run(connection)
            
    async def status(self, connection: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get the status of all migrations."""
        # Ensure migration table exists
        await self._create_migration_table(connection)
        
        # Get all migration files
        all_migrations = self._get_migration_files()
        
        # Get ran migrations
        ran_migrations = {record.migration for record in await self._get_ran_migrations(connection)}
        
        # Build status list
        status_list = []
        for migration_file in all_migrations:
            migration_name = os.path.splitext(migration_file)[0]
            status_list.append({
                'migration': migration_name,
                'batch': None,  # Would need to query for specific batch
                'ran': migration_name in ran_migrations
            })
            
        return status_list
        
    async def get_pending_migrations(self, connection: Optional[str] = None) -> List[str]:
        """Get migrations that haven't been run yet."""
        # Get all migration files
        all_migrations = self._get_migration_files()
        
        # Get ran migrations
        ran_migrations = {record.migration for record in await self._get_ran_migrations(connection)}
        
        # Filter pending migrations
        pending = []
        for migration_file in all_migrations:
            migration_name = os.path.splitext(migration_file)[0]
            if migration_name not in ran_migrations:
                pending.append(migration_file)
                
        return pending
        
    def _get_migration_files(self) -> List[str]:
        """Get all migration files from the migration directory."""
        if not os.path.exists(self.migration_path):
            return []
            
        files = []
        for file in os.listdir(self.migration_path):
            if file.endswith('.py') and not file.startswith('__'):
                files.append(file)
                
        # Sort by timestamp prefix
        files.sort(key=lambda x: self._extract_timestamp(x))
        return files
        
    def _extract_timestamp(self, filename: str) -> str:
        """Extract timestamp from migration filename."""
        match = re.match(r'^(\d{4}_\d{2}_\d{2}_\d{6})', filename)
        return match.group(1) if match else filename
        
    async def _run_migration(self, migration_file: str, direction: str, 
                           connection: Optional[str] = None, batch: Optional[int] = None) -> bool:
        """Run a single migration."""
        try:
            # Load migration class
            migration_class = self._load_migration_class(migration_file)
            if not migration_class:
                return False
                
            # Create migration instance
            migration_instance = migration_class()
            if connection:
                migration_instance.connection = connection
                
            # Run migration
            if direction == 'up':
                await migration_instance.up()
                if batch is not None:
                    await self._log_migration(migration_file, batch, connection)
            else:
                await migration_instance.down()
                
            return True
            
        except Exception as e:
            print(f"Migration failed: {migration_file} - {e}")
            return False
            
    def _load_migration_class(self, migration_file: str) -> Optional[Type[Migration]]:
        """Load migration class from file."""
        try:
            # Build file path
            file_path = os.path.join(self.migration_path, migration_file)
            
            # Load module
            spec = importlib.util.spec_from_file_location("migration", file_path)
            if not spec or not spec.loader:
                return None
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find migration class
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, Migration) and 
                    attr is not Migration):
                    return attr
                    
            return None
            
        except Exception as e:
            print(f"Failed to load migration {migration_file}: {e}")
            return None
            
    async def _create_migration_table(self, connection: Optional[str] = None) -> None:
        """Create the migration tracking table."""
        from ..schema import Schema, Blueprint
        
        def create_migrations_table(table: Blueprint) -> None:
            table.id()
            table.string('migration')
            table.integer('batch')
            table.timestamp('created_at').default('CURRENT_TIMESTAMP')
            
        if not Schema.has_table(self.migration_table, connection):
            Schema.create(self.migration_table, create_migrations_table, connection)
            
    async def _log_migration(self, migration_file: str, batch: int, 
                           connection: Optional[str] = None) -> None:
        """Log a migration run."""
        migration_name = os.path.splitext(migration_file)[0]
        
        async with self.db_manager.session(connection) as session:
            query = f"""
                INSERT INTO {self.migration_table} (migration, batch, created_at)
                VALUES (?, ?, ?)
            """
            await session.execute(query, (migration_name, batch, datetime.now()))
            await session.commit()
            
    async def _delete_migration_record(self, migration_file: str, 
                                     connection: Optional[str] = None) -> None:
        """Delete a migration record."""
        migration_name = os.path.splitext(migration_file)[0]
        
        async with self.db_manager.session(connection) as session:
            query = f"DELETE FROM {self.migration_table} WHERE migration = ?"
            await session.execute(query, (migration_name,))
            await session.commit()
            
    async def _get_ran_migrations(self, connection: Optional[str] = None) -> List[MigrationRecord]:
        """Get all ran migrations from the database."""
        async with self.db_manager.session(connection) as session:
            query = f"""
                SELECT id, migration, batch, created_at 
                FROM {self.migration_table} 
                ORDER BY batch, id
            """
            result = await session.execute(query)
            rows = result.fetchall()
            
            return [
                MigrationRecord(row[0], row[1], row[2], row[3])
                for row in rows
            ]
            
    async def _get_migrations_to_rollback(self, steps: int, 
                                        connection: Optional[str] = None) -> List[MigrationRecord]:
        """Get migrations to rollback."""
        async with self.db_manager.session(connection) as session:
            query = f"""
                SELECT id, migration, batch, created_at 
                FROM {self.migration_table} 
                ORDER BY batch DESC, id DESC 
                LIMIT ?
            """
            result = await session.execute(query, (steps,))
            rows = result.fetchall()
            
            return [
                MigrationRecord(row[0], row[1], row[2], row[3])
                for row in rows
            ]
            
    async def _get_next_batch_number(self, connection: Optional[str] = None) -> int:
        """Get the next batch number."""
        async with self.db_manager.session(connection) as session:
            query = f"SELECT MAX(batch) FROM {self.migration_table}"
            result = await session.execute(query)
            max_batch = result.scalar()
            
            return (max_batch or 0) + 1
            
    async def _drop_all_tables(self, connection: Optional[str] = None) -> None:
        """Drop all tables in the database."""
        # This is database-specific implementation
        # For now, we'll implement a basic version
        async with self.db_manager.session(connection) as session:
            # Get database connection to determine driver
            db_connection = self.db_manager.get_connection(connection)
            
            if db_connection.driver == 'sqlite':
                # Get all tables
                result = await session.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = [row[0] for row in result.fetchall()]
                
                # Drop each table
                for table in tables:
                    if table != 'sqlite_sequence':
                        await session.execute(f"DROP TABLE IF EXISTS {table}")
                        
            elif db_connection.driver in ['postgresql']:
                # Drop all tables in public schema
                await session.execute("""
                    DROP SCHEMA public CASCADE;
                    CREATE SCHEMA public;
                """)
                
            elif db_connection.driver in ['mysql']:
                # Get all tables
                result = await session.execute("SHOW TABLES")
                tables = [row[0] for row in result.fetchall()]
                
                # Drop each table
                for table in tables:
                    await session.execute(f"DROP TABLE {table}")
                    
            await session.commit()
    
    # Synchronous wrapper methods for CLI commands
    def run_migrations(self, migrations_path: Path = None) -> int:
        """Synchronous wrapper for running migrations."""
        import asyncio
        if migrations_path:
            self.migration_path = str(migrations_path)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            migrations = loop.run_until_complete(self.run())
            return len(migrations)
        finally:
            loop.close()
    
    def rollback_migrations(self, steps: int = 1) -> int:
        """Synchronous wrapper for rollback migrations."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            migrations = loop.run_until_complete(self.rollback(step=steps))
            return len(migrations)
        finally:
            loop.close()
    
    def drop_all_tables(self):
        """Synchronous wrapper for dropping all tables."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._drop_all_tables())
        finally:
            loop.close()
    
    def get_migration_status(self) -> Dict[str, bool]:
        """Get migration status synchronously."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            status_list = loop.run_until_complete(self.status())
            return {item['migration']: item['ran'] for item in status_list}
        finally:
            loop.close()


def make_migration_name(description: str) -> str:
    """Create a migration filename with timestamp."""
    timestamp = datetime.now().strftime('%Y_%m_%d_%H%M%S')
    # Convert to snake_case
    description = re.sub(r'[^a-zA-Z0-9]+', '_', description).lower().strip('_')
    return f"{timestamp}_{description}.py"