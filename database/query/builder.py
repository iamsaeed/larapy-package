"""
Query builder for Larapy database operations.

This module provides a fluent query builder interface similar to Laravel's
query builder with support for complex queries, joins, and aggregations.
"""

from typing import Any, Dict, List, Optional, Union, Tuple, Callable
from sqlalchemy import select, insert, update, delete, func, text, and_, or_, not_
from sqlalchemy.sql import Select, Insert, Update, Delete
from sqlalchemy.sql.elements import Label
from sqlalchemy.orm import Query
from ..connection import DatabaseManager
import asyncio


class QueryBuilder:
    """Fluent query builder for database operations."""
    
    def __init__(self, db_manager: DatabaseManager, table: str, connection: Optional[str] = None):
        self.db_manager = db_manager
        self.table_name = table
        self.connection_name = connection
        
        # Query state
        self._select_columns = []
        self._where_clauses = []
        self._or_where_clauses = []
        self._joins = []
        self._group_by = []
        self._having = []
        self._order_by = []
        self._limit_count = None
        self._offset_count = None
        self._distinct = False
        
        # For update/delete operations
        self._update_data = {}
        self._insert_data = []
        
    def select(self, *columns) -> 'QueryBuilder':
        """Select specific columns."""
        self._select_columns.extend(columns)
        return self
        
    def distinct(self) -> 'QueryBuilder':
        """Add DISTINCT to the query."""
        self._distinct = True
        return self
        
    def where(self, column: Union[str, Callable], operator: Optional[str] = None, 
              value: Any = None) -> 'QueryBuilder':
        """Add a WHERE clause."""
        if callable(column):
            # Handle closure-based where clauses
            nested_builder = QueryBuilder(self.db_manager, self.table_name, self.connection_name)
            column(nested_builder)
            self._where_clauses.append(('nested', nested_builder._where_clauses))
        else:
            if operator is None and value is None:
                # where('column', value) format
                operator = '='
                value = operator
            elif value is None:
                # where('column', '=', value) format but only 2 params
                value = operator
                operator = '='
            
            self._where_clauses.append((column, operator, value))
        return self
        
    def or_where(self, column: str, operator: Optional[str] = None, value: Any = None) -> 'QueryBuilder':
        """Add an OR WHERE clause."""
        if operator is None:
            operator = '='
            value = operator
        elif value is None:
            value = operator
            operator = '='
            
        self._or_where_clauses.append((column, operator, value))
        return self
        
    def where_in(self, column: str, values: List[Any]) -> 'QueryBuilder':
        """Add a WHERE IN clause."""
        self._where_clauses.append((column, 'IN', values))
        return self
        
    def where_not_in(self, column: str, values: List[Any]) -> 'QueryBuilder':
        """Add a WHERE NOT IN clause."""
        self._where_clauses.append((column, 'NOT IN', values))
        return self
        
    def where_null(self, column: str) -> 'QueryBuilder':
        """Add a WHERE NULL clause."""
        self._where_clauses.append((column, 'IS', None))
        return self
        
    def where_not_null(self, column: str) -> 'QueryBuilder':
        """Add a WHERE NOT NULL clause."""
        self._where_clauses.append((column, 'IS NOT', None))
        return self
        
    def where_between(self, column: str, start: Any, end: Any) -> 'QueryBuilder':
        """Add a WHERE BETWEEN clause."""
        self._where_clauses.append((column, 'BETWEEN', (start, end)))
        return self
        
    def where_not_between(self, column: str, start: Any, end: Any) -> 'QueryBuilder':
        """Add a WHERE NOT BETWEEN clause."""
        self._where_clauses.append((column, 'NOT BETWEEN', (start, end)))
        return self
        
    def where_like(self, column: str, pattern: str) -> 'QueryBuilder':
        """Add a WHERE LIKE clause."""
        self._where_clauses.append((column, 'LIKE', pattern))
        return self
        
    def where_not_like(self, column: str, pattern: str) -> 'QueryBuilder':
        """Add a WHERE NOT LIKE clause."""
        self._where_clauses.append((column, 'NOT LIKE', pattern))
        return self
        
    def join(self, table: str, first: str, operator: str = '=', second: Optional[str] = None) -> 'QueryBuilder':
        """Add an INNER JOIN clause."""
        if second is None:
            second = operator
            operator = '='
        self._joins.append(('INNER', table, first, operator, second))
        return self
        
    def left_join(self, table: str, first: str, operator: str = '=', second: Optional[str] = None) -> 'QueryBuilder':
        """Add a LEFT JOIN clause."""
        if second is None:
            second = operator
            operator = '='
        self._joins.append(('LEFT', table, first, operator, second))
        return self
        
    def right_join(self, table: str, first: str, operator: str = '=', second: Optional[str] = None) -> 'QueryBuilder':
        """Add a RIGHT JOIN clause."""
        if second is None:
            second = operator
            operator = '='
        self._joins.append(('RIGHT', table, first, operator, second))
        return self
        
    def cross_join(self, table: str) -> 'QueryBuilder':
        """Add a CROSS JOIN clause."""
        self._joins.append(('CROSS', table, None, None, None))
        return self
        
    def group_by(self, *columns) -> 'QueryBuilder':
        """Add GROUP BY clauses."""
        self._group_by.extend(columns)
        return self
        
    def having(self, column: str, operator: str, value: Any) -> 'QueryBuilder':
        """Add a HAVING clause."""
        self._having.append((column, operator, value))
        return self
        
    def order_by(self, column: str, direction: str = 'ASC') -> 'QueryBuilder':
        """Add an ORDER BY clause."""
        self._order_by.append((column, direction.upper()))
        return self
        
    def latest(self, column: str = 'created_at') -> 'QueryBuilder':
        """Order by column in descending order."""
        return self.order_by(column, 'DESC')
        
    def oldest(self, column: str = 'created_at') -> 'QueryBuilder':
        """Order by column in ascending order."""
        return self.order_by(column, 'ASC')
        
    def limit(self, count: int) -> 'QueryBuilder':
        """Limit the number of results."""
        self._limit_count = count
        return self
        
    def take(self, count: int) -> 'QueryBuilder':
        """Alias for limit()."""
        return self.limit(count)
        
    def offset(self, count: int) -> 'QueryBuilder':
        """Skip a number of results."""
        self._offset_count = count
        return self
        
    def skip(self, count: int) -> 'QueryBuilder':
        """Alias for offset()."""
        return self.offset(count)
        
    def paginate(self, page: int, per_page: int = 15) -> 'QueryBuilder':
        """Paginate the results."""
        offset = (page - 1) * per_page
        return self.limit(per_page).offset(offset)
        
    # Execution methods
    async def get(self) -> List[Dict[str, Any]]:
        """Execute the query and return all results."""
        query = self._build_select_query()
        
        async with self.db_manager.session(self.connection_name) as session:
            result = await session.execute(query)
            return [dict(row._mapping) for row in result.fetchall()]
            
    async def first(self) -> Optional[Dict[str, Any]]:
        """Execute the query and return the first result."""
        query = self._build_select_query().limit(1)
        
        async with self.db_manager.session(self.connection_name) as session:
            result = await session.execute(query)
            row = result.fetchone()
            return dict(row._mapping) if row else None
            
    async def find(self, id: Any) -> Optional[Dict[str, Any]]:
        """Find a record by ID."""
        return await self.where('id', id).first()
        
    async def count(self, column: str = '*') -> int:
        """Get the count of results."""
        query = select(func.count(text(column))).select_from(text(self.table_name))
        query = self._apply_conditions(query)
        
        async with self.db_manager.session(self.connection_name) as session:
            result = await session.execute(query)
            return result.scalar()
            
    async def exists(self) -> bool:
        """Check if any records exist."""
        count = await self.count()
        return count > 0
        
    async def sum(self, column: str) -> Union[int, float]:
        """Get the sum of a column."""
        query = select(func.sum(text(column))).select_from(text(self.table_name))
        query = self._apply_conditions(query)
        
        async with self.db_manager.session(self.connection_name) as session:
            result = await session.execute(query)
            return result.scalar() or 0
            
    async def avg(self, column: str) -> Union[int, float]:
        """Get the average of a column."""
        query = select(func.avg(text(column))).select_from(text(self.table_name))
        query = self._apply_conditions(query)
        
        async with self.db_manager.session(self.connection_name) as session:
            result = await session.execute(query)
            return result.scalar() or 0
            
    async def max(self, column: str) -> Any:
        """Get the maximum value of a column."""
        query = select(func.max(text(column))).select_from(text(self.table_name))
        query = self._apply_conditions(query)
        
        async with self.db_manager.session(self.connection_name) as session:
            result = await session.execute(query)
            return result.scalar()
            
    async def min(self, column: str) -> Any:
        """Get the minimum value of a column."""
        query = select(func.min(text(column))).select_from(text(self.table_name))
        query = self._apply_conditions(query)
        
        async with self.db_manager.session(self.connection_name) as session:
            result = await session.execute(query)
            return result.scalar()
            
    # Data modification methods
    async def insert(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """Insert data into the table."""
        if isinstance(data, dict):
            data = [data]
            
        query = insert(text(self.table_name)).values(data)
        
        async with self.db_manager.session(self.connection_name) as session:
            await session.execute(query)
            await session.commit()
            return True
            
    async def insert_get_id(self, data: Dict[str, Any]) -> Any:
        """Insert data and return the inserted ID."""
        query = insert(text(self.table_name)).values(data)
        
        async with self.db_manager.session(self.connection_name) as session:
            result = await session.execute(query)
            await session.commit()
            return result.inserted_primary_key[0]
            
    async def update(self, data: Dict[str, Any]) -> int:
        """Update records matching the current conditions."""
        query = update(text(self.table_name)).values(data)
        query = self._apply_conditions(query)
        
        async with self.db_manager.session(self.connection_name) as session:
            result = await session.execute(query)
            await session.commit()
            return result.rowcount
            
    async def delete(self) -> int:
        """Delete records matching the current conditions."""
        query = delete(text(self.table_name))
        query = self._apply_conditions(query)
        
        async with self.db_manager.session(self.connection_name) as session:
            result = await session.execute(query)
            await session.commit()
            return result.rowcount
            
    async def truncate(self) -> None:
        """Truncate the table."""
        async with self.db_manager.session(self.connection_name) as session:
            await session.execute(text(f"TRUNCATE TABLE {self.table_name}"))
            await session.commit()
            
    # Raw query methods
    async def raw(self, sql: str, bindings: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        query = text(sql)
        
        async with self.db_manager.session(self.connection_name) as session:
            result = await session.execute(query, bindings or {})
            return [dict(row._mapping) for row in result.fetchall()]
            
    # Query building helpers
    def _build_select_query(self) -> Select:
        """Build the SELECT query."""
        # Determine columns to select
        if self._select_columns:
            columns = [text(col) for col in self._select_columns]
        else:
            columns = [text('*')]
            
        query = select(*columns).select_from(text(self.table_name))
        
        if self._distinct:
            query = query.distinct()
            
        query = self._apply_conditions(query)
        query = self._apply_joins(query)
        query = self._apply_grouping(query)
        query = self._apply_ordering(query)
        query = self._apply_limits(query)
        
        return query
        
    def _apply_conditions(self, query):
        """Apply WHERE conditions to the query."""
        for clause in self._where_clauses:
            if clause[0] == 'nested':
                # Handle nested where clauses
                nested_conditions = []
                for nested_clause in clause[1]:
                    condition = self._build_condition(*nested_clause)
                    nested_conditions.append(condition)
                if nested_conditions:
                    query = query.where(and_(*nested_conditions))
            else:
                condition = self._build_condition(*clause)
                query = query.where(condition)
                
        for clause in self._or_where_clauses:
            condition = self._build_condition(*clause)
            query = query.where(or_(condition))
            
        return query
        
    def _build_condition(self, column: str, operator: str, value: Any):
        """Build a single WHERE condition."""
        col = text(column)
        
        if operator == '=':
            return col == value
        elif operator == '!=':
            return col != value
        elif operator == '>':
            return col > value
        elif operator == '>=':
            return col >= value
        elif operator == '<':
            return col < value
        elif operator == '<=':
            return col <= value
        elif operator == 'LIKE':
            return col.like(value)
        elif operator == 'NOT LIKE':
            return not_(col.like(value))
        elif operator == 'IN':
            return col.in_(value)
        elif operator == 'NOT IN':
            return not_(col.in_(value))
        elif operator == 'IS':
            return col.is_(value)
        elif operator == 'IS NOT':
            return col.is_not(value)
        elif operator == 'BETWEEN':
            return col.between(value[0], value[1])
        elif operator == 'NOT BETWEEN':
            return not_(col.between(value[0], value[1]))
        else:
            raise ValueError(f"Unsupported operator: {operator}")
            
    def _apply_joins(self, query):
        """Apply JOIN clauses to the query."""
        for join in self._joins:
            join_type, table, first, operator, second = join
            
            if join_type == 'CROSS':
                query = query.join(text(table), isouter=False, full=True)
            else:
                on_clause = text(f"{first} {operator} {second}")
                
                if join_type == 'LEFT':
                    query = query.join(text(table), on_clause, isouter=True)
                elif join_type == 'RIGHT':
                    query = query.join(text(table), on_clause, isouter=True)  # SQLAlchemy doesn't have right join
                else:  # INNER
                    query = query.join(text(table), on_clause)
                    
        return query
        
    def _apply_grouping(self, query):
        """Apply GROUP BY and HAVING clauses."""
        if self._group_by:
            query = query.group_by(*[text(col) for col in self._group_by])
            
        for clause in self._having:
            column, operator, value = clause
            condition = self._build_condition(column, operator, value)
            query = query.having(condition)
            
        return query
        
    def _apply_ordering(self, query):
        """Apply ORDER BY clauses."""
        for column, direction in self._order_by:
            col = text(column)
            if direction == 'DESC':
                query = query.order_by(col.desc())
            else:
                query = query.order_by(col.asc())
                
        return query
        
    def _apply_limits(self, query):
        """Apply LIMIT and OFFSET."""
        if self._limit_count:
            query = query.limit(self._limit_count)
            
        if self._offset_count:
            query = query.offset(self._offset_count)
            
        return query
        
    # Helper methods for creating new instances
    def new_query(self) -> 'QueryBuilder':
        """Create a new query builder instance."""
        return QueryBuilder(self.db_manager, self.table_name, self.connection_name)
        
    def clone(self) -> 'QueryBuilder':
        """Clone the current query builder."""
        clone = self.new_query()
        clone._select_columns = self._select_columns.copy()
        clone._where_clauses = self._where_clauses.copy()
        clone._or_where_clauses = self._or_where_clauses.copy()
        clone._joins = self._joins.copy()
        clone._group_by = self._group_by.copy()
        clone._having = self._having.copy()
        clone._order_by = self._order_by.copy()
        clone._limit_count = self._limit_count
        clone._offset_count = self._offset_count
        clone._distinct = self._distinct
        return clone