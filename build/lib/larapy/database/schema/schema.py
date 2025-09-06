"""
Database schema management for Larapy.

This module provides the main Schema class for creating, modifying, and dropping
database tables with a fluent Laravel-like API.
"""

from typing import Callable, Optional, Dict, Any
from sqlalchemy import MetaData, Table
from sqlalchemy.schema import CreateTable, DropTable
from .blueprint import Blueprint
from ..connection import DatabaseManager


class Schema:
    """Main schema builder class with fluent API."""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db = database_manager
        self.metadata = MetaData()
        
    @classmethod
    def create(cls, table_name: str, callback: Callable[[Blueprint], None],
               connection: Optional[str] = None) -> None:
        """Create a new database table."""
        # This would be called as a static method with app context
        from larapy.core.application import app  # Import from app context
        
        schema = cls(app.make('db'))
        blueprint = Blueprint(table_name, schema.metadata)
        
        # Execute the callback to define the table structure
        callback(blueprint)
        
        # Build the table
        table = blueprint.build()
        
        # Execute the CREATE TABLE statement
        asyncio.run(schema._execute_ddl(CreateTable(table), connection))
    
    @classmethod
    def table(cls, table_name: str, callback: Callable[[Blueprint], None],
              connection: Optional[str] = None) -> None:
        """Modify an existing database table."""
        # This would handle ALTER TABLE operations
        # For now, we'll implement basic structure
        pass
    
    @classmethod
    def drop(cls, table_name: str, connection: Optional[str] = None) -> None:
        """Drop a database table."""
        from larapy.core.application import app
        
        schema = cls(app.make('db'))
        
        # Create a table reference for dropping
        table = Table(table_name, schema.metadata)
        
        # Execute the DROP TABLE statement
        asyncio.run(schema._execute_ddl(DropTable(table), connection))
    
    @classmethod
    def drop_if_exists(cls, table_name: str, connection: Optional[str] = None) -> None:
        """Drop a database table if it exists."""
        from larapy.core.application import app
        
        schema = cls(app.make('db'))
        
        # Check if table exists first
        if asyncio.run(schema._table_exists(table_name, connection)):
            cls.drop(table_name, connection)
    
    @classmethod  
    def rename(cls, from_table: str, to_table: str, connection: Optional[str] = None) -> None:
        """Rename a database table."""
        from larapy.core.application import app
        
        schema = cls(app.make('db'))
        
        # This would execute RENAME TABLE or ALTER TABLE RENAME
        # Implementation depends on database driver
        sql = f"ALTER TABLE {from_table} RENAME TO {to_table}"
        asyncio.run(schema._execute_raw(sql, connection))
    
    @classmethod
    def has_table(cls, table_name: str, connection: Optional[str] = None) -> bool:
        """Check if a table exists."""
        from larapy.core.application import app
        
        schema = cls(app.make('db'))
        return asyncio.run(schema._table_exists(table_name, connection))
    
    @classmethod
    def has_column(cls, table_name: str, column_name: str, 
                   connection: Optional[str] = None) -> bool:
        """Check if a column exists in a table."""
        from larapy.core.application import app
        
        schema = cls(app.make('db'))
        return asyncio.run(schema._column_exists(table_name, column_name, connection))
    
    @classmethod
    def has_columns(cls, table_name: str, columns: list, 
                    connection: Optional[str] = None) -> bool:
        """Check if all specified columns exist in a table."""
        from larapy.core.application import app
        
        schema = cls(app.make('db'))
        
        for column in columns:
            if not asyncio.run(schema._column_exists(table_name, column, connection)):
                return False
        return True
    
    @classmethod
    def get_column_type(cls, table_name: str, column_name: str,
                       connection: Optional[str] = None) -> Optional[str]:
        """Get the data type of a column."""
        from larapy.core.application import app
        
        schema = cls(app.make('db'))
        return asyncio.run(schema._get_column_type(table_name, column_name, connection))
    
    @classmethod
    def get_column_listing(cls, table_name: str, 
                          connection: Optional[str] = None) -> list:
        """Get all column names for a table."""
        from larapy.core.application import app
        
        schema = cls(app.make('db'))
        return asyncio.run(schema._get_columns(table_name, connection))
    
    # Instance methods for actual database operations
    async def _execute_ddl(self, ddl_statement, connection: Optional[str] = None):
        """Execute a DDL statement."""
        async with self.db.session(connection) as session:
            await session.execute(ddl_statement)
            await session.commit()
    
    async def _execute_raw(self, sql: str, connection: Optional[str] = None):
        """Execute raw SQL."""
        async with self.db.session(connection) as session:
            await session.execute(sql)
            await session.commit()
    
    async def _table_exists(self, table_name: str, connection: Optional[str] = None) -> bool:
        """Check if a table exists."""
        try:
            engine = await self.db.get_engine(connection)
            async with engine.connect() as conn:
                # Database-specific table existence check
                db_connection = self.db.get_connection(connection)
                
                if db_connection.driver == 'sqlite':
                    result = await conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (table_name,)
                    )
                elif db_connection.driver in ['postgresql']:
                    result = await conn.execute(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema='public' AND table_name=%s",
                        (table_name,)
                    )
                elif db_connection.driver in ['mysql']:
                    result = await conn.execute(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema=DATABASE() AND table_name=%s",
                        (table_name,)
                    )
                else:
                    return False
                
                return result.fetchone() is not None
        except Exception:
            return False
    
    async def _column_exists(self, table_name: str, column_name: str, 
                           connection: Optional[str] = None) -> bool:
        """Check if a column exists."""
        try:
            columns = await self._get_columns(table_name, connection)
            return column_name in columns
        except Exception:
            return False
    
    async def _get_columns(self, table_name: str, 
                          connection: Optional[str] = None) -> list:
        """Get all column names for a table."""
        try:
            engine = await self.db.get_engine(connection)
            async with engine.connect() as conn:
                db_connection = self.db.get_connection(connection)
                
                if db_connection.driver == 'sqlite':
                    result = await conn.execute(f"PRAGMA table_info({table_name})")
                    rows = result.fetchall()
                    return [row[1] for row in rows]  # Column name is at index 1
                    
                elif db_connection.driver in ['postgresql']:
                    result = await conn.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema='public' AND table_name=%s",
                        (table_name,)
                    )
                    rows = result.fetchall()
                    return [row[0] for row in rows]
                    
                elif db_connection.driver in ['mysql']:
                    result = await conn.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema=DATABASE() AND table_name=%s",
                        (table_name,)
                    )
                    rows = result.fetchall()
                    return [row[0] for row in rows]
                    
                else:
                    return []
        except Exception:
            return []
    
    async def _get_column_type(self, table_name: str, column_name: str,
                             connection: Optional[str] = None) -> Optional[str]:
        """Get the data type of a column."""
        try:
            engine = await self.db.get_engine(connection)
            async with engine.connect() as conn:
                db_connection = self.db.get_connection(connection)
                
                if db_connection.driver == 'sqlite':
                    result = await conn.execute(f"PRAGMA table_info({table_name})")
                    rows = result.fetchall()
                    for row in rows:
                        if row[1] == column_name:  # Column name at index 1, type at index 2
                            return row[2]
                            
                elif db_connection.driver in ['postgresql']:
                    result = await conn.execute(
                        "SELECT data_type FROM information_schema.columns "
                        "WHERE table_schema='public' AND table_name=%s AND column_name=%s",
                        (table_name, column_name)
                    )
                    row = result.fetchone()
                    return row[0] if row else None
                    
                elif db_connection.driver in ['mysql']:
                    result = await conn.execute(
                        "SELECT data_type FROM information_schema.columns "
                        "WHERE table_schema=DATABASE() AND table_name=%s AND column_name=%s",
                        (table_name, column_name)
                    )
                    row = result.fetchone()
                    return row[0] if row else None
                    
                return None
        except Exception:
            return None


# Import asyncio for the class methods that need it
import asyncio