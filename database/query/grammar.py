"""
Query grammar for Larapy database operations.

This module provides database-specific SQL generation capabilities.
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod


class QueryGrammar(ABC):
    """Base query grammar class."""
    
    def __init__(self):
        self.table_prefix = ''
        
    @abstractmethod
    def compile_select(self, query_data: Dict[str, Any]) -> str:
        """Compile a SELECT query."""
        pass
        
    @abstractmethod
    def compile_insert(self, query_data: Dict[str, Any]) -> str:
        """Compile an INSERT query."""
        pass
        
    @abstractmethod
    def compile_update(self, query_data: Dict[str, Any]) -> str:
        """Compile an UPDATE query."""
        pass
        
    @abstractmethod
    def compile_delete(self, query_data: Dict[str, Any]) -> str:
        """Compile a DELETE query."""
        pass
        

class SQLiteGrammar(QueryGrammar):
    """SQLite-specific query grammar."""
    
    def compile_select(self, query_data: Dict[str, Any]) -> str:
        """Compile a SELECT query for SQLite."""
        sql_parts = ['SELECT']
        
        # Handle DISTINCT
        if query_data.get('distinct'):
            sql_parts.append('DISTINCT')
            
        # Columns
        columns = query_data.get('columns', ['*'])
        sql_parts.append(', '.join(columns))
        
        # FROM clause
        sql_parts.extend(['FROM', query_data['table']])
        
        # WHERE clause
        where_conditions = query_data.get('where', [])
        if where_conditions:
            sql_parts.append('WHERE')
            sql_parts.append(' AND '.join(where_conditions))
            
        # ORDER BY
        order_by = query_data.get('order_by', [])
        if order_by:
            sql_parts.append('ORDER BY')
            sql_parts.append(', '.join(order_by))
            
        # LIMIT and OFFSET
        if query_data.get('limit'):
            sql_parts.extend(['LIMIT', str(query_data['limit'])])
            
        if query_data.get('offset'):
            sql_parts.extend(['OFFSET', str(query_data['offset'])])
            
        return ' '.join(sql_parts)
        
    def compile_insert(self, query_data: Dict[str, Any]) -> str:
        """Compile an INSERT query for SQLite."""
        table = query_data['table']
        data = query_data['data']
        
        if isinstance(data, list) and data:
            # Multiple rows
            columns = list(data[0].keys())
            column_list = ', '.join(columns)
            
            value_rows = []
            for row in data:
                values = ', '.join([f":{key}" for key in columns])
                value_rows.append(f"({values})")
                
            return f"INSERT INTO {table} ({column_list}) VALUES {', '.join(value_rows)}"
        else:
            # Single row
            columns = ', '.join(data.keys())
            values = ', '.join([f":{key}" for key in data.keys()])
            return f"INSERT INTO {table} ({columns}) VALUES ({values})"
            
    def compile_update(self, query_data: Dict[str, Any]) -> str:
        """Compile an UPDATE query for SQLite."""
        table = query_data['table']
        data = query_data['data']
        
        set_clause = ', '.join([f"{key} = :{key}" for key in data.keys()])
        sql = f"UPDATE {table} SET {set_clause}"
        
        where_conditions = query_data.get('where', [])
        if where_conditions:
            sql += ' WHERE ' + ' AND '.join(where_conditions)
            
        return sql
        
    def compile_delete(self, query_data: Dict[str, Any]) -> str:
        """Compile a DELETE query for SQLite."""
        table = query_data['table']
        sql = f"DELETE FROM {table}"
        
        where_conditions = query_data.get('where', [])
        if where_conditions:
            sql += ' WHERE ' + ' AND '.join(where_conditions)
            
        return sql


class PostgreSQLGrammar(QueryGrammar):
    """PostgreSQL-specific query grammar."""
    
    def compile_select(self, query_data: Dict[str, Any]) -> str:
        """Compile a SELECT query for PostgreSQL."""
        # Similar to SQLite but with PostgreSQL-specific features
        return SQLiteGrammar().compile_select(query_data)
        
    def compile_insert(self, query_data: Dict[str, Any]) -> str:
        """Compile an INSERT query for PostgreSQL."""
        sql = SQLiteGrammar().compile_insert(query_data)
        
        # Add RETURNING clause for PostgreSQL
        if query_data.get('returning'):
            sql += f" RETURNING {query_data['returning']}"
            
        return sql
        
    def compile_update(self, query_data: Dict[str, Any]) -> str:
        """Compile an UPDATE query for PostgreSQL."""
        return SQLiteGrammar().compile_update(query_data)
        
    def compile_delete(self, query_data: Dict[str, Any]) -> str:
        """Compile a DELETE query for PostgreSQL."""
        return SQLiteGrammar().compile_delete(query_data)


class MySQLGrammar(QueryGrammar):
    """MySQL-specific query grammar."""
    
    def compile_select(self, query_data: Dict[str, Any]) -> str:
        """Compile a SELECT query for MySQL."""
        # Similar to SQLite but with MySQL-specific features
        return SQLiteGrammar().compile_select(query_data)
        
    def compile_insert(self, query_data: Dict[str, Any]) -> str:
        """Compile an INSERT query for MySQL."""
        return SQLiteGrammar().compile_insert(query_data)
        
    def compile_update(self, query_data: Dict[str, Any]) -> str:
        """Compile an UPDATE query for MySQL."""
        return SQLiteGrammar().compile_update(query_data)
        
    def compile_delete(self, query_data: Dict[str, Any]) -> str:
        """Compile a DELETE query for MySQL."""
        return SQLiteGrammar().compile_delete(query_data)


def get_grammar(driver: str) -> QueryGrammar:
    """Get the appropriate grammar for a database driver."""
    grammars = {
        'sqlite': SQLiteGrammar,
        'postgresql': PostgreSQLGrammar,
        'mysql': MySQLGrammar,
    }
    
    grammar_class = grammars.get(driver, SQLiteGrammar)
    return grammar_class()