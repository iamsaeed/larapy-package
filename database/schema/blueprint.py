"""
Database blueprint for fluent table definition in Larapy.

This module provides the Blueprint class for defining database table schemas
with a fluent, Laravel-like API.
"""

from typing import List, Optional, Any, Callable, Union
from sqlalchemy import (
    Column as SQLColumn,
    Integer, String, Text, Boolean, DateTime, Date, Time,
    Float, Numeric, LargeBinary, ForeignKey, Index, UniqueConstraint,
    CheckConstraint, MetaData, Table
)
from sqlalchemy.sql import func
from datetime import datetime


class Column:
    """Represents a database column with fluent configuration."""
    
    def __init__(self, name: str, column_type: Any, **kwargs):
        self.name = name
        self.type = column_type
        self.is_nullable = kwargs.get('nullable', True)
        self.is_primary_key = kwargs.get('primary_key', False)
        self.is_unique = kwargs.get('unique', False)
        self.default_value = kwargs.get('default')
        self.is_autoincrement = kwargs.get('autoincrement', False)
        self.foreign_key = kwargs.get('foreign_key')
        self.comment_text = kwargs.get('comment')
        
    def nullable(self) -> 'Column':
        """Mark the column as nullable."""
        self.is_nullable = True
        return self
        
    def not_nullable(self) -> 'Column':
        """Mark the column as not nullable."""
        self.is_nullable = False
        return self
    
    def unique(self) -> 'Column':
        """Mark the column as unique."""
        self.is_unique = True
        return self
        
    def primary(self) -> 'Column':
        """Mark the column as primary key."""
        self.is_primary_key = True
        self.is_nullable = False
        return self
        
    def default(self, value: Any) -> 'Column':
        """Set the default value for the column."""
        self.default_value = value
        return self
        
    def comment(self, text: str) -> 'Column':
        """Add a comment to the column."""
        self.comment_text = text
        return self
        
    def references(self, table_column: str) -> 'Column':
        """Add a foreign key reference."""
        self.foreign_key = table_column
        return self
        
    def to_sqlalchemy_column(self) -> SQLColumn:
        """Convert to SQLAlchemy column."""
        kwargs = {
            'nullable': self.is_nullable,
            'primary_key': self.is_primary_key,
            'unique': self.is_unique,
            'autoincrement': self.is_autoincrement
        }
        
        if self.default_value is not None:
            kwargs['default'] = self.default_value
            
        if self.foreign_key:
            kwargs['foreign_key'] = ForeignKey(self.foreign_key)
            
        if self.comment_text:
            kwargs['comment'] = self.comment_text
            
        return SQLColumn(self.name, self.type, **kwargs)


class Blueprint:
    """Fluent table builder for database schema definition."""
    
    def __init__(self, table_name: str, metadata: MetaData):
        self.table_name = table_name
        self.metadata = metadata
        self.columns: List[Column] = []
        self.indexes: List[dict] = []
        self.constraints: List[dict] = []
        self._temporary = False
        
    def temporary(self) -> 'Blueprint':
        """Mark the table as temporary."""
        self._temporary = True
        return self
        
    # Column definition methods
    def id(self, name: str = 'id') -> Column:
        """Create an auto-incrementing integer primary key column."""
        column = Column(name, Integer, primary_key=True, autoincrement=True, nullable=False)
        self.columns.append(column)
        return column
        
    def string(self, name: str, length: int = 255) -> Column:
        """Create a string column."""
        column = Column(name, String(length))
        self.columns.append(column)
        return column
        
    def text(self, name: str) -> Column:
        """Create a text column."""
        column = Column(name, Text)
        self.columns.append(column)
        return column
        
    def integer(self, name: str) -> Column:
        """Create an integer column."""
        column = Column(name, Integer)
        self.columns.append(column)
        return column
        
    def boolean(self, name: str) -> Column:
        """Create a boolean column."""
        column = Column(name, Boolean)
        self.columns.append(column)
        return column
        
    def datetime(self, name: str) -> Column:
        """Create a datetime column."""
        column = Column(name, DateTime)
        self.columns.append(column)
        return column
        
    def timestamp(self, name: str) -> Column:
        """Create a timestamp column."""
        column = Column(name, DateTime)
        self.columns.append(column)
        return column
        
    def date(self, name: str) -> Column:
        """Create a date column."""
        column = Column(name, Date)
        self.columns.append(column)
        return column
        
    def time(self, name: str) -> Column:
        """Create a time column."""
        column = Column(name, Time)
        self.columns.append(column)
        return column
        
    def float(self, name: str, precision: Optional[int] = None) -> Column:
        """Create a float column."""
        column_type = Float(precision) if precision else Float
        column = Column(name, column_type)
        self.columns.append(column)
        return column
        
    def decimal(self, name: str, precision: int = 10, scale: int = 2) -> Column:
        """Create a decimal column."""
        column = Column(name, Numeric(precision, scale))
        self.columns.append(column)
        return column
        
    def binary(self, name: str) -> Column:
        """Create a binary column."""
        column = Column(name, LargeBinary)
        self.columns.append(column)
        return column
        
    def json(self, name: str) -> Column:
        """Create a JSON column (stored as text)."""
        column = Column(name, Text)
        self.columns.append(column)
        return column
        
    # Convenience methods for common patterns
    def timestamps(self) -> 'Blueprint':
        """Add created_at and updated_at timestamp columns."""
        self.timestamp('created_at').default(func.now()).not_nullable()
        self.timestamp('updated_at').default(func.now()).not_nullable()
        return self
        
    def soft_deletes(self, column: str = 'deleted_at') -> 'Blueprint':
        """Add a soft delete timestamp column."""
        self.timestamp(column).nullable()
        return self
        
    def remember_token(self) -> 'Blueprint':
        """Add a remember token column for authentication."""
        self.string('remember_token', 100).nullable()
        return self
        
    # Index methods
    def index(self, columns: Union[str, List[str]], name: Optional[str] = None) -> 'Blueprint':
        """Add an index to the table."""
        if isinstance(columns, str):
            columns = [columns]
            
        index_name = name or f"idx_{self.table_name}_{'_'.join(columns)}"
        self.indexes.append({
            'name': index_name,
            'columns': columns,
            'unique': False
        })
        return self
        
    def unique(self, columns: Union[str, List[str]], name: Optional[str] = None) -> 'Blueprint':
        """Add a unique index to the table."""
        if isinstance(columns, str):
            columns = [columns]
            
        index_name = name or f"unq_{self.table_name}_{'_'.join(columns)}"
        self.indexes.append({
            'name': index_name,
            'columns': columns,
            'unique': True
        })
        return self
        
    def foreign(self, column: str) -> 'ForeignKeyBuilder':
        """Create a foreign key constraint."""
        return ForeignKeyBuilder(self, column)
        
    # Build methods
    def build(self) -> Table:
        """Build the SQLAlchemy table from the blueprint."""
        # Convert columns to SQLAlchemy columns
        sqlalchemy_columns = [col.to_sqlalchemy_column() for col in self.columns]
        
        # Create the table
        table = Table(
            self.table_name,
            self.metadata,
            *sqlalchemy_columns,
            prefixes=['TEMPORARY'] if self._temporary else None
        )
        
        # Add indexes
        for index_config in self.indexes:
            if index_config['unique']:
                UniqueConstraint(*index_config['columns'], name=index_config['name'])
            else:
                Index(index_config['name'], *[table.c[col] for col in index_config['columns']])
        
        return table


class ForeignKeyBuilder:
    """Builder for foreign key constraints."""
    
    def __init__(self, blueprint: Blueprint, column: str):
        self.blueprint = blueprint
        self.column = column
        self.reference_table: Optional[str] = None
        self.reference_column: Optional[str] = None
        self.on_delete: Optional[str] = None
        self.on_update: Optional[str] = None
        
    def references(self, column: str) -> 'ForeignKeyBuilder':
        """Set the referenced column."""
        self.reference_column = column
        return self
        
    def on(self, table: str) -> 'ForeignKeyBuilder':
        """Set the referenced table."""
        self.reference_table = table
        return self
        
    def on_delete(self, action: str) -> 'ForeignKeyBuilder':
        """Set the on delete action."""
        self.on_delete = action.upper()
        return self
        
    def on_update(self, action: str) -> 'ForeignKeyBuilder':
        """Set the on update action."""
        self.on_update = action.upper()
        return self
        
    def cascade(self) -> 'ForeignKeyBuilder':
        """Set cascade for both delete and update."""
        self.on_delete = 'CASCADE'
        self.on_update = 'CASCADE'
        return self
        
    def restrict(self) -> 'ForeignKeyBuilder':
        """Set restrict for both delete and update."""
        self.on_delete = 'RESTRICT'
        self.on_update = 'RESTRICT'
        return self
        
    def set_null(self) -> 'ForeignKeyBuilder':
        """Set null for both delete and update."""
        self.on_delete = 'SET NULL'
        self.on_update = 'SET NULL'
        return self
        
    def build(self) -> dict:
        """Build the foreign key constraint configuration."""
        if not self.reference_table or not self.reference_column:
            raise ValueError("Foreign key must specify both table and column")
            
        reference = f"{self.reference_table}.{self.reference_column}"
        
        # Find the column in the blueprint and set its foreign key
        for col in self.blueprint.columns:
            if col.name == self.column:
                col.foreign_key = reference
                break
        
        return {
            'column': self.column,
            'references': reference,
            'on_delete': self.on_delete,
            'on_update': self.on_update
        }