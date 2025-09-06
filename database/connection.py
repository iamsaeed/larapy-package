"""
Database connection management for Larapy.

This module provides database connection management with support for multiple
database drivers, connection pooling, and query logging.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Union
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool


class DatabaseConnection:
    """Represents a single database connection configuration."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', 'default')
        self.driver = config.get('driver', 'sqlite')
        self.host = config.get('host', 'localhost')
        self.port = config.get('port')
        self.database = config.get('database')
        self.username = config.get('username')
        self.password = config.get('password')
        self.options = config.get('options', {})
        
        self._engine: Optional[AsyncEngine] = None
        self._session_maker: Optional[sessionmaker] = None
        
    def get_dsn(self) -> str:
        """Build the database connection URL."""
        if self.driver == 'sqlite':
            if self.database == ':memory:':
                return 'sqlite+aiosqlite:///:memory:'
            return f'sqlite+aiosqlite:///{self.database}'
        
        elif self.driver == 'postgresql':
            dsn = f'postgresql+asyncpg://'
            if self.username:
                dsn += self.username
                if self.password:
                    dsn += f':{self.password}'
                dsn += '@'
            dsn += f'{self.host}'
            if self.port:
                dsn += f':{self.port}'
            if self.database:
                dsn += f'/{self.database}'
            return dsn
        
        elif self.driver == 'mysql':
            dsn = f'mysql+aiomysql://'
            if self.username:
                dsn += self.username
                if self.password:
                    dsn += f':{self.password}'
                dsn += '@'
            dsn += f'{self.host}'
            if self.port:
                dsn += f':{self.port}'
            if self.database:
                dsn += f'/{self.database}'
            return dsn
        
        else:
            raise ValueError(f"Unsupported database driver: {self.driver}")
    
    async def get_engine(self) -> AsyncEngine:
        """Get or create the SQLAlchemy async engine."""
        if self._engine is None:
            engine_options = {
                'poolclass': QueuePool,
                'pool_size': self.options.get('pool_size', 10),
                'max_overflow': self.options.get('max_overflow', 20),
                'pool_pre_ping': True,
                'echo': self.options.get('echo', False)
            }
            
            self._engine = create_async_engine(
                self.get_dsn(),
                **engine_options
            )
        
        return self._engine
    
    async def get_session_maker(self) -> sessionmaker:
        """Get or create the session maker."""
        if self._session_maker is None:
            engine = await self.get_engine()
            self._session_maker = sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        
        return self._session_maker
    
    @asynccontextmanager
    async def session(self):
        """Create a database session context manager."""
        session_maker = await self.get_session_maker()
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Close the database connection."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_maker = None


class DatabaseManager:
    """Manages multiple database connections."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connections: Dict[str, DatabaseConnection] = {}
        self.default_connection = config.get('default', 'default')
        self.logger = logging.getLogger('larapy.database')
        
        # Initialize connections from config
        connections_config = config.get('connections', {})
        for name, conn_config in connections_config.items():
            conn_config['name'] = name
            self.connections[name] = DatabaseConnection(conn_config)
    
    def add_connection(self, name: str, config: Dict[str, Any]) -> DatabaseConnection:
        """Add a new database connection."""
        config['name'] = name
        connection = DatabaseConnection(config)
        self.connections[name] = connection
        return connection
    
    def get_connection(self, name: Optional[str] = None) -> DatabaseConnection:
        """Get a database connection by name."""
        connection_name = name or self.default_connection
        
        if connection_name not in self.connections:
            raise ValueError(f"Database connection '{connection_name}' not found")
        
        return self.connections[connection_name]
    
    @asynccontextmanager
    async def session(self, connection_name: Optional[str] = None):
        """Get a database session from the specified connection."""
        connection = self.get_connection(connection_name)
        async with connection.session() as session:
            yield session
    
    async def get_engine(self, connection_name: Optional[str] = None) -> AsyncEngine:
        """Get the SQLAlchemy engine for the specified connection."""
        connection = self.get_connection(connection_name)
        return await connection.get_engine()
    
    async def test_connection(self, connection_name: Optional[str] = None) -> bool:
        """Test if a database connection is working."""
        try:
            connection = self.get_connection(connection_name)
            engine = await connection.get_engine()
            
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
                return True
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
    
    async def close_all(self):
        """Close all database connections."""
        for connection in self.connections.values():
            await connection.close()
    
    def get_connection_names(self) -> list[str]:
        """Get all configured connection names."""
        return list(self.connections.keys())
    
    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None,
                         connection_name: Optional[str] = None):
        """Execute a raw SQL query."""
        async with self.session(connection_name) as session:
            result = await session.execute(query, params or {})
            return result
    
    @asynccontextmanager
    async def transaction(self, connection_name: Optional[str] = None):
        """Create a database transaction context."""
        async with self.session(connection_name) as session:
            async with session.begin():
                yield session


# Example configuration format
DEFAULT_CONFIG = {
    'default': 'default',
    'connections': {
        'default': {
            'driver': 'sqlite',
            'database': 'database.db',
            'options': {
                'echo': False,
                'pool_size': 10,
                'max_overflow': 20
            }
        },
        'postgresql': {
            'driver': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'database': 'larapy',
            'username': 'postgres',
            'password': 'password',
            'options': {
                'echo': False,
                'pool_size': 10,
                'max_overflow': 20
            }
        },
        'mysql': {
            'driver': 'mysql',
            'host': 'localhost', 
            'port': 3306,
            'database': 'larapy',
            'username': 'root',
            'password': 'password',
            'options': {
                'echo': False,
                'pool_size': 10,
                'max_overflow': 20
            }
        }
    }
}