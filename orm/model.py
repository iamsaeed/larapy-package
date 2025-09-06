"""
Larapy-like ORM model for Larapy.

This module provides the base Model class with ActiveRecord pattern,
relationships, and model management capabilities.
"""

from typing import Any, Dict, List, Optional, Union, Type, ClassVar
from abc import ABC
from datetime import datetime
from ..database.query.builder import QueryBuilder
from ..database.connection import DatabaseManager
import json
import asyncio


class ModelMeta(type):
    """Metaclass for Model to handle class-level configuration."""
    
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Set up table name if not specified
        if 'table' not in namespace and name != 'Model':
            # Convert CamelCase to snake_case and pluralize
            table_name = mcs._camel_to_snake(name)
            if not table_name.endswith('s'):
                table_name += 's'
            namespace['table'] = table_name
            
        return super().__new__(mcs, name, bases, namespace)
        
    @staticmethod
    def _camel_to_snake(name: str) -> str:
        """Convert CamelCase to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class Model(metaclass=ModelMeta):
    """Base ORM model class with ActiveRecord pattern."""
    
    # Class-level configuration
    table: ClassVar[Optional[str]] = None
    primary_key: ClassVar[str] = 'id'
    incrementing: ClassVar[bool] = True
    key_type: ClassVar[str] = 'int'
    
    # Mass assignment protection
    fillable: ClassVar[List[str]] = []
    guarded: ClassVar[List[str]] = ['*']
    
    # Hidden attributes for serialization
    hidden: ClassVar[List[str]] = []
    visible: ClassVar[List[str]] = []
    
    # Timestamp handling
    timestamps: ClassVar[bool] = True
    created_at: ClassVar[str] = 'created_at'
    updated_at: ClassVar[str] = 'updated_at'
    
    # Soft delete configuration
    soft_deletes: ClassVar[bool] = False
    deleted_at: ClassVar[str] = 'deleted_at'
    
    # Connection configuration
    connection: ClassVar[Optional[str]] = None
    
    # Attribute casting
    casts: ClassVar[Dict[str, str]] = {}
    
    # Date attributes
    dates: ClassVar[List[str]] = []
    date_format: ClassVar[str] = '%Y-%m-%d %H:%M:%S'
    
    def __init__(self, attributes: Optional[Dict[str, Any]] = None, exists: bool = False):
        self.attributes: Dict[str, Any] = {}
        self.original: Dict[str, Any] = {}
        self.changes: Dict[str, Any] = {}
        self.exists = exists
        self._relations: Dict[str, Any] = {}
        
        if attributes:
            self.fill(attributes)
            if exists:
                self.sync_original()
                
    @classmethod
    def get_table_name(cls) -> str:
        """Get the table name for this model."""
        return cls.table or cls.__name__.lower() + 's'
        
    @classmethod
    def get_connection_name(cls) -> Optional[str]:
        """Get the connection name for this model."""
        return cls.connection
        
    @classmethod
    def get_db_manager(cls) -> DatabaseManager:
        """Get the database manager from the application container."""
        from larapy.core.application import app
        return app.make('db')
        
    @classmethod
    def query(cls) -> QueryBuilder:
        """Create a new query builder for this model."""
        db_manager = cls.get_db_manager()
        return QueryBuilder(db_manager, cls.get_table_name(), cls.get_connection_name())
        
    @classmethod
    async def all(cls, columns: Optional[List[str]] = None) -> List['Model']:
        """Get all models from the database."""
        query = cls.query()
        if columns:
            query.select(*columns)
            
        results = await query.get()
        return [cls(result, exists=True) for result in results]
        
    @classmethod
    async def find(cls, id: Any, columns: Optional[List[str]] = None) -> Optional['Model']:
        """Find a model by its primary key."""
        query = cls.query().where(cls.primary_key, id)
        if columns:
            query.select(*columns)
            
        result = await query.first()
        return cls(result, exists=True) if result else None
        
    @classmethod
    async def find_or_fail(cls, id: Any, columns: Optional[List[str]] = None) -> 'Model':
        """Find a model by its primary key or raise an exception."""
        model = await cls.find(id, columns)
        if model is None:
            raise ValueError(f"No query results for model [{cls.__name__}] {id}")
        return model
        
    @classmethod
    async def where(cls, column: str, operator: Optional[str] = None, value: Any = None) -> QueryBuilder:
        """Create a where query."""
        return cls.query().where(column, operator, value)
        
    @classmethod
    async def first(cls, columns: Optional[List[str]] = None) -> Optional['Model']:
        """Get the first model from the database."""
        query = cls.query()
        if columns:
            query.select(*columns)
            
        result = await query.first()
        return cls(result, exists=True) if result else None
        
    @classmethod
    async def first_or_fail(cls, columns: Optional[List[str]] = None) -> 'Model':
        """Get the first model or raise an exception."""
        model = await cls.first(columns)
        if model is None:
            raise ValueError(f"No query results for model [{cls.__name__}]")
        return model
        
    @classmethod
    async def create(cls, attributes: Dict[str, Any]) -> 'Model':
        """Create a new model and save it to the database."""
        model = cls(attributes)
        await model.save()
        return model
        
    @classmethod
    async def find_or_create(cls, attributes: Dict[str, Any], 
                           values: Optional[Dict[str, Any]] = None) -> 'Model':
        """Find a model or create it if it doesn't exist."""
        query = cls.query()
        for key, value in attributes.items():
            query.where(key, value)
            
        result = await query.first()
        if result:
            return cls(result, exists=True)
            
        # Create new model
        create_attrs = {**attributes, **(values or {})}
        return await cls.create(create_attrs)
        
    @classmethod
    async def update_or_create(cls, attributes: Dict[str, Any],
                             values: Optional[Dict[str, Any]] = None) -> 'Model':
        """Update a model or create it if it doesn't exist."""
        model = await cls.find_or_create(attributes, values)
        if values and model.exists:
            model.fill(values)
            await model.save()
        return model
        
    # Instance methods
    def fill(self, attributes: Dict[str, Any]) -> 'Model':
        """Fill the model with an array of attributes."""
        fillable_attrs = self._get_fillable_attributes(attributes)
        
        for key, value in fillable_attrs.items():
            self.set_attribute(key, value)
            
        return self
        
    def _get_fillable_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Get the fillable attributes from the given attributes."""
        if self.fillable:
            return {k: v for k, v in attributes.items() if k in self.fillable}
        elif self.guarded and '*' not in self.guarded:
            return {k: v for k, v in attributes.items() if k not in self.guarded}
        else:
            return attributes
            
    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the model."""
        # Handle mutators (setters)
        mutator_method = f'set_{key}_attribute'
        if hasattr(self, mutator_method):
            value = getattr(self, mutator_method)(value)
            
        self.attributes[key] = value
        
        # Track changes
        if self.exists and key in self.original:
            if self.original[key] != value:
                self.changes[key] = value
            elif key in self.changes:
                del self.changes[key]
                
    def get_attribute(self, key: str) -> Any:
        """Get an attribute from the model."""
        # Handle accessors (getters)
        accessor_method = f'get_{key}_attribute'
        if hasattr(self, accessor_method):
            return getattr(self, accessor_method)(self.attributes.get(key))
            
        # Handle casting
        value = self.attributes.get(key)
        if key in self.casts:
            value = self._cast_attribute(key, value)
            
        return value
        
    def _cast_attribute(self, key: str, value: Any) -> Any:
        """Cast an attribute to its proper type."""
        if value is None:
            return None
            
        cast_type = self.casts[key]
        
        if cast_type == 'int':
            return int(value)
        elif cast_type == 'float':
            return float(value)
        elif cast_type == 'string':
            return str(value)
        elif cast_type == 'bool':
            return bool(value)
        elif cast_type == 'json':
            return json.loads(value) if isinstance(value, str) else value
        elif cast_type == 'datetime':
            if isinstance(value, str):
                return datetime.strptime(value, self.date_format)
            return value
        else:
            return value
            
    def __getattr__(self, key: str) -> Any:
        """Get an attribute using dot notation."""
        if key in self.attributes:
            return self.get_attribute(key)
        elif key in self._relations:
            return self._relations[key]
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")
            
    def __setattr__(self, key: str, value: Any) -> None:
        """Set an attribute using dot notation."""
        if key.startswith('_') or key in ['attributes', 'original', 'changes', 'exists']:
            super().__setattr__(key, value)
        else:
            self.set_attribute(key, value)
            
    def get_key(self) -> Any:
        """Get the primary key value."""
        return self.get_attribute(self.primary_key)
        
    def get_key_name(self) -> str:
        """Get the primary key name."""
        return self.primary_key
        
    def get_key_type(self) -> str:
        """Get the primary key type.""" 
        return self.key_type
        
    def is_dirty(self, attributes: Optional[List[str]] = None) -> bool:
        """Check if the model has been modified."""
        if attributes:
            return any(attr in self.changes for attr in attributes)
        return len(self.changes) > 0
        
    def is_clean(self, attributes: Optional[List[str]] = None) -> bool:
        """Check if the model hasn't been modified."""
        return not self.is_dirty(attributes)
        
    def get_dirty(self) -> Dict[str, Any]:
        """Get the dirty attributes."""
        return self.changes.copy()
        
    def sync_original(self) -> 'Model':
        """Sync the original attributes with the current ones."""
        self.original = self.attributes.copy()
        self.changes = {}
        return self
        
    def get_original(self, key: Optional[str] = None, default: Any = None) -> Any:
        """Get the original value of an attribute."""
        if key:
            return self.original.get(key, default)
        return self.original.copy()
        
    async def save(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Save the model to the database."""
        # Fire saving event
        if not await self._fire_model_event('saving'):
            return False
            
        if self.exists:
            saved = await self._perform_update()
        else:
            saved = await self._perform_insert()
            
        if saved:
            # Fire saved event
            await self._fire_model_event('saved')
            
        return saved
        
    async def _perform_insert(self) -> bool:
        """Perform an insert operation."""
        # Fire creating event
        if not await self._fire_model_event('creating'):
            return False
            
        # Add timestamps
        if self.timestamps:
            now = datetime.now()
            if self.created_at and self.created_at not in self.attributes:
                self.set_attribute(self.created_at, now)
            if self.updated_at and self.updated_at not in self.attributes:
                self.set_attribute(self.updated_at, now)
                
        query = self.query()
        
        if self.incrementing:
            # Insert and get ID
            inserted_id = await query.insert_get_id(self.attributes)
            self.set_attribute(self.primary_key, inserted_id)
        else:
            # Just insert
            await query.insert(self.attributes)
            
        self.exists = True
        self.sync_original()
        
        # Fire created event
        await self._fire_model_event('created')
        
        return True
        
    async def _perform_update(self) -> bool:
        """Perform an update operation."""
        if not self.is_dirty():
            return True
            
        # Fire updating event
        if not await self._fire_model_event('updating'):
            return False
            
        # Update timestamp
        if self.timestamps and self.updated_at:
            self.set_attribute(self.updated_at, datetime.now())
            
        query = self.query().where(self.primary_key, self.get_key())
        await query.update(self.get_dirty())
        
        self.sync_original()
        
        # Fire updated event
        await self._fire_model_event('updated')
        
        return True
        
    async def delete(self) -> bool:
        """Delete the model from the database."""
        if not self.exists:
            return False
            
        # Fire deleting event
        if not await self._fire_model_event('deleting'):
            return False
            
        if self.soft_deletes:
            # Soft delete
            self.set_attribute(self.deleted_at, datetime.now())
            await self.save()
        else:
            # Hard delete
            query = self.query().where(self.primary_key, self.get_key())
            await query.delete()
            self.exists = False
            
        # Fire deleted event
        await self._fire_model_event('deleted')
        
        return True
        
    async def restore(self) -> bool:
        """Restore a soft-deleted model."""
        if not self.soft_deletes:
            return False
            
        self.set_attribute(self.deleted_at, None)
        return await self.save()
        
    def to_dict(self, include_hidden: bool = False) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        result = {}
        
        for key, value in self.attributes.items():
            # Skip hidden attributes unless requested
            if not include_hidden and self.hidden and key in self.hidden:
                continue
                
            # Only include visible attributes if specified
            if self.visible and key not in self.visible:
                continue
                
            # Handle JSON serialization
            if key in self.casts and self.casts[key] == 'json':
                if isinstance(value, (dict, list)):
                    result[key] = value
                else:
                    result[key] = json.loads(value) if value else None
            elif isinstance(value, datetime):
                result[key] = value.strftime(self.date_format)
            else:
                result[key] = value
                
        return result
        
    def to_json(self, include_hidden: bool = False) -> str:
        """Convert the model to JSON."""
        return json.dumps(self.to_dict(include_hidden))
        
    async def _fire_model_event(self, event: str) -> bool:
        """Fire a model event."""
        # This would integrate with an event system
        # For now, just check if there are any event methods
        method_name = event
        if hasattr(self, method_name):
            result = getattr(self, method_name)()
            if asyncio.iscoroutine(result):
                return await result
            return result
        return True
        
    # Relationship methods (will be expanded with actual relationship classes)
    def has_one(self, related_model: Type['Model'], foreign_key: Optional[str] = None,
               local_key: Optional[str] = None):
        """Define a one-to-one relationship."""
        # This would return a HasOne relationship instance
        pass
        
    def has_many(self, related_model: Type['Model'], foreign_key: Optional[str] = None,
                local_key: Optional[str] = None):
        """Define a one-to-many relationship."""
        # This would return a HasMany relationship instance
        pass
        
    def belongs_to(self, related_model: Type['Model'], foreign_key: Optional[str] = None,
                  owner_key: Optional[str] = None):
        """Define a many-to-one relationship."""
        # This would return a BelongsTo relationship instance
        pass
        
    def belongs_to_many(self, related_model: Type['Model'], table: Optional[str] = None,
                       foreign_pivot_key: Optional[str] = None,
                       related_pivot_key: Optional[str] = None):
        """Define a many-to-many relationship."""
        # This would return a BelongsToMany relationship instance
        pass