"""
Base migration class for Larapy.

This module provides the base Migration class that all migration files
will extend to define schema changes.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional
from ..schema import Schema, Blueprint


class Migration(ABC):
    """Base class for database migrations."""
    
    def __init__(self):
        self.connection: Optional[str] = None
        
    @abstractmethod
    async def up(self) -> None:
        """Run the migration."""
        pass
        
    @abstractmethod
    async def down(self) -> None:
        """Reverse the migration."""
        pass
        
    # Helper methods for common migration operations
    def create(self, table_name: str, callback: Callable[[Blueprint], None]) -> None:
        """Create a new table."""
        Schema.create(table_name, callback, self.connection)
        
    def table(self, table_name: str, callback: Callable[[Blueprint], None]) -> None:
        """Modify an existing table."""
        Schema.table(table_name, callback, self.connection)
        
    def drop(self, table_name: str) -> None:
        """Drop a table."""
        Schema.drop(table_name, self.connection)
        
    def drop_if_exists(self, table_name: str) -> None:
        """Drop a table if it exists."""
        Schema.drop_if_exists(table_name, self.connection)
        
    def rename(self, from_table: str, to_table: str) -> None:
        """Rename a table."""
        Schema.rename(from_table, to_table, self.connection)
        
    def has_table(self, table_name: str) -> bool:
        """Check if a table exists."""
        return Schema.has_table(table_name, self.connection)
        
    def has_column(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists."""
        return Schema.has_column(table_name, column_name, self.connection)


class CreateMigration(Migration):
    """Base class for create table migrations."""
    
    def __init__(self, table_name: str):
        super().__init__()
        self.table_name = table_name
        
    async def up(self) -> None:
        """Create the table."""
        self.create(self.table_name, self.define_table)
        
    async def down(self) -> None:
        """Drop the table."""
        self.drop(self.table_name)
        
    @abstractmethod
    def define_table(self, table: Blueprint) -> None:
        """Define the table structure."""
        pass


class ModifyMigration(Migration):
    """Base class for table modification migrations."""
    
    def __init__(self, table_name: str):
        super().__init__()
        self.table_name = table_name
        
    async def up(self) -> None:
        """Modify the table."""
        self.table(self.table_name, self.modify_table)
        
    @abstractmethod
    def modify_table(self, table: Blueprint) -> None:
        """Define the table modifications."""
        pass
        
    @abstractmethod
    async def down(self) -> None:
        """Reverse the modifications."""
        pass