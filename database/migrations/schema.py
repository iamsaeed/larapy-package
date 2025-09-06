"""
Simplified Schema module for migrations.

This module provides a basic Schema implementation that works with Laravel-style
configuration and uses the config() helper to get database settings.
"""

import sqlite3
from typing import Callable, Optional
import os
import sys
from pathlib import Path

# Import helpers with improved strategy
def _import_config():
    """Import config helper with multiple fallback strategies."""
    
    # Strategy 1: Relative import (when used as package)
    try:
        from ..core.helpers import config
        return config
    except ImportError:
        pass
    
    # Strategy 2: Direct import (when core is in path)
    try:
        from core.helpers import config
        return config
    except ImportError:
        pass
    
    # Strategy 3: Add package to path and import
    try:
        # Find the package directory
        current_file = Path(__file__)
        # Go up from migrations/schema.py to package root
        package_root = current_file.parent.parent.parent
        
        if str(package_root) not in sys.path:
            sys.path.insert(0, str(package_root))
        
        from core.helpers import config
        return config
    except ImportError:
        pass
    
    # Strategy 4: Import from file directly
    try:
        import importlib.util
        current_file = Path(__file__)
        possible_helpers = current_file.parent.parent.parent / 'core' / 'helpers.py'
        
        if possible_helpers.exists():
            spec = importlib.util.spec_from_file_location("core.helpers", possible_helpers)
            if spec and spec.loader:
                helpers_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(helpers_module)
                return helpers_module.config
    except Exception:
        pass
    
    # Last resort fallback
    def config(key, default=None):
        if key == 'database.default':
            return 'sqlite'
        elif key == 'database.connections.sqlite.database':
            return 'database/database.sqlite'
        elif key == 'database.connections.sqlite.driver':
            return 'sqlite'
        return default
    
    return config

# Import config using the improved strategy
config = _import_config()


class Blueprint:
    """Simple blueprint for defining table structure."""
    
    def __init__(self, table_name: str, database_type: str = 'sqlite'):
        self.table_name = table_name
        self.database_type = database_type
        self.columns = []
        self.indexes = []
    
    def id(self, column_name: str = 'id'):
        """Add an auto-incrementing primary key."""
        if self.database_type == 'mysql':
            self.columns.append(f"{column_name} INT AUTO_INCREMENT PRIMARY KEY")
        else:  # SQLite
            self.columns.append(f"{column_name} INTEGER PRIMARY KEY AUTOINCREMENT")
        return self
    
    def string(self, column_name: str, length: int = 255):
        """Add a string column."""
        column = f"{column_name} VARCHAR({length})"
        self.columns.append(column)
        return Column(column_name, column, self)
    
    def text(self, column_name: str):
        """Add a text column."""
        column = f"{column_name} TEXT"
        self.columns.append(column)
        return Column(column_name, column, self)
    
    def integer(self, column_name: str):
        """Add an integer column."""
        column = f"{column_name} INTEGER"
        self.columns.append(column)
        return Column(column_name, column, self)
    
    def boolean(self, column_name: str):
        """Add a boolean column."""
        column = f"{column_name} BOOLEAN"
        self.columns.append(column)
        return Column(column_name, column, self)
    
    def timestamp(self, column_name: str):
        """Add a timestamp column."""
        column = f"{column_name} TIMESTAMP"
        self.columns.append(column)
        return Column(column_name, column, self)
    
    def timestamps(self):
        """Add created_at and updated_at timestamp columns."""
        self.columns.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        self.columns.append("updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        return self
    
    def build_create_sql(self) -> str:
        """Build the CREATE TABLE SQL statement."""
        columns_sql = ",\n    ".join(self.columns)
        
        sql = f"CREATE TABLE {self.table_name} (\n    {columns_sql}\n)"
        
        # Add indexes
        if self.indexes:
            for index in self.indexes:
                sql += f";\n{index}"
        
        return sql


class Column:
    """Represents a column with modifiers."""
    
    def __init__(self, name: str, definition: str, blueprint: Blueprint):
        self.name = name
        self.definition = definition
        self.blueprint = blueprint
        self.column_index = len(blueprint.columns) - 1
    
    def nullable(self):
        """Make the column nullable."""
        # Update the column definition
        self.blueprint.columns[self.column_index] += " NULL"
        return self
    
    def default(self, value):
        """Set a default value for the column."""
        if isinstance(value, str):
            self.blueprint.columns[self.column_index] += f" DEFAULT '{value}'"
        elif isinstance(value, bool):
            self.blueprint.columns[self.column_index] += f" DEFAULT {int(value)}"
        else:
            self.blueprint.columns[self.column_index] += f" DEFAULT {value}"
        return self
    
    def unique(self):
        """Add a unique constraint."""
        self.blueprint.columns[self.column_index] += " UNIQUE"
        return self
    
    def index(self):
        """Add an index for this column."""
        index_name = f"idx_{self.blueprint.table_name}_{self.name}"
        index_sql = f"CREATE INDEX {index_name} ON {self.blueprint.table_name}({self.name})"
        self.blueprint.indexes.append(index_sql)
        return self


class Schema:
    """Simple Schema class for migration operations using Laravel-style configuration."""
    
    @classmethod
    def create(cls, table_name: str, callback: Callable[[Blueprint], None], 
               connection: Optional[str] = None) -> None:
        """Create a new database table."""
        # Get database configuration
        db_config = cls._get_database_path(connection)
        
        # Determine database type
        if isinstance(db_config, dict):
            database_type = db_config.get('driver', 'sqlite')
        else:
            database_type = 'sqlite'
        
        blueprint = Blueprint(table_name, database_type)
        
        # Execute the callback to define the table structure
        callback(blueprint)
        
        # Build and execute the SQL
        sql = blueprint.build_create_sql()
        
        # Execute the SQL
        cls._execute_sql(sql, db_config)
    
    @classmethod
    def drop(cls, table_name: str, connection: Optional[str] = None) -> None:
        """Drop a database table."""
        db_config = cls._get_database_path(connection)
        sql = f"DROP TABLE {table_name}"
        cls._execute_sql(sql, db_config)
    
    @classmethod
    def drop_if_exists(cls, table_name: str, connection: Optional[str] = None) -> None:
        """Drop a database table if it exists."""
        db_config = cls._get_database_path(connection)
        sql = f"DROP TABLE IF EXISTS {table_name}"
        cls._execute_sql(sql, db_config)
    
    @classmethod
    def has_table(cls, table_name: str, connection: Optional[str] = None) -> bool:
        """Check if a table exists."""
        try:
            database_path = cls._get_database_path(connection)
            conn = sqlite3.connect(database_path)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception:
            return False
    
    @classmethod 
    def table(cls, table_name: str, callback: Callable[[Blueprint], None],
              connection: Optional[str] = None) -> None:
        """Modify an existing table (basic implementation)."""
        # For now, this is a placeholder - full ALTER TABLE support would be more complex
        # In SQLite, many ALTER TABLE operations require table recreation
        pass
    
    @classmethod
    def _get_database_path(cls, connection: Optional[str] = None) -> str:
        """
        Get the database path for the specified connection.
        
        Args:
            connection: Database connection name
            
        Returns:
            Database path
        """
        # Use default connection if not specified
        if not connection:
            connection = config('database.default', 'sqlite')
        
        # Get connection configuration
        connection_key = f'database.connections.{connection}'
        connection_config = config(connection_key, {})
        
        driver = connection_config.get('driver')
        if driver == 'sqlite':
            return connection_config.get('database', 'database/database.sqlite')
        elif driver == 'mysql':
            return connection_config  # Return full config for MySQL
        else:
            # For non-SQLite databases, we'd need different handling
            raise ValueError(f"Unsupported database driver for connection '{connection}': {driver}")
    
    @classmethod
    def _execute_sql(cls, sql: str, db_config) -> None:
        """Execute SQL statement on the database."""
        
        if isinstance(db_config, dict) and db_config.get('driver') == 'mysql':
            # MySQL connection
            import mysql.connector
            conn = mysql.connector.connect(
                host=db_config.get('host', '127.0.0.1'),
                port=db_config.get('port', 3306),
                database=db_config.get('database', ''),
                user=db_config.get('username', ''),
                password=db_config.get('password', ''),
                charset=db_config.get('charset', 'utf8mb4')
            )
            
            try:
                cursor = conn.cursor()
                # Handle multiple statements
                if ';' in sql and sql.count(';') > 1:
                    statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
                    for statement in statements:
                        cursor.execute(statement)
                else:
                    cursor.execute(sql)
                conn.commit()
                cursor.close()
            finally:
                conn.close()
        else:
            # SQLite connection (db_config is file path)
            database_path = db_config if isinstance(db_config, str) else str(db_config)
            from pathlib import Path
            
            # Ensure database directory exists
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Execute the SQL
            conn = sqlite3.connect(database_path)
            try:
                # Handle multiple statements (for indexes)
                if ';' in sql and sql.count(';') > 1:
                    statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
                    for statement in statements:
                        conn.execute(statement)
                else:
                    conn.execute(sql)
                conn.commit()
            finally:
                conn.close()