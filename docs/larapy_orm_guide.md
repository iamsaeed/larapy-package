# Larapy ORM Guide

A comprehensive guide to using Larapy's Object-Relational Mapping (ORM) system inspired by Laravel's Eloquent ORM.

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Model Definition](#model-definition)
4. [Configuration](#configuration)
5. [Querying Models](#querying-models)
6. [Creating and Updating](#creating-and-updating)
7. [Relationships](#relationships)
8. [Scopes](#scopes)
9. [Accessors and Mutators](#accessors-and-mutators)
10. [Attribute Casting](#attribute-casting)
11. [Serialization](#serialization)
12. [Events](#events)
13. [Advanced Features](#advanced-features)
14. [Complete API Reference](#complete-api-reference)

## Introduction

Larapy ORM provides an elegant, simple ActiveRecord implementation for working with your database. Each database table has a corresponding "Model" which is used to interact with that table. Models allow you to query for data in your tables, as well as insert new records into the table.

Key Features:
- **ActiveRecord Pattern**: Each model instance represents a single row in the database
- **Async/Await Support**: All database operations are asynchronous
- **Mass Assignment Protection**: Secure attribute assignment with fillable/guarded
- **Attribute Casting**: Automatic type conversion
- **Relationships**: Define relationships between models
- **Query Builder**: Fluent query building interface
- **Timestamps**: Automatic created_at and updated_at handling
- **Soft Deletes**: Mark records as deleted without removing them

## Getting Started

### Creating Models

Use the Larapy CLI to generate models:

```bash
larapy make model User
larapy make model BlogPost
larapy make model UserProfile
```

This creates model files in `app/models/` directory following PEP 8 naming conventions.

### Basic Model Structure

```python
"""
User model for database operations.
"""

from larapy.orm.model import Model

class User(Model):
    """User model for database interactions."""
    
    # Table name (optional - auto-generated from class name)
    table = 'users'
    
    # Mass assignment protection
    fillable = ['name', 'email', 'password']
    
    # Attribute casting
    casts = {
        'is_active': 'boolean',
        'metadata': 'json',
        'created_at': 'datetime'
    }
```

## Model Definition

### Table Names

By default, the table name is the snake_case plural of the class name:

```python
class User(Model):      # Table: users
    pass

class BlogPost(Model):  # Table: blog_posts
    pass

# Override default table name
class User(Model):
    table = 'custom_users'
```

### Primary Keys

```python
class User(Model):
    primary_key = 'id'      # Default
    incrementing = True     # Auto-incrementing
    key_type = 'int'       # Key type
```

For non-incrementing or string primary keys:

```python
class User(Model):
    primary_key = 'uuid'
    incrementing = False
    key_type = 'string'
```

### Timestamps

```python
class User(Model):
    timestamps = True                # Default - enables timestamps
    created_at = 'created_at'       # Default column name
    updated_at = 'updated_at'       # Default column name

# Disable timestamps
class LogEntry(Model):
    timestamps = False
```

## Configuration

### Mass Assignment Protection

Use `fillable` to specify which attributes can be mass assigned:

```python
class User(Model):
    fillable = ['name', 'email', 'bio']
```

Or use `guarded` to specify which attributes cannot be mass assigned:

```python
class User(Model):
    guarded = ['id', 'password', 'remember_token']
```

### Hidden Attributes

Hide sensitive attributes from serialization:

```python
class User(Model):
    hidden = ['password', 'remember_token']
```

### Visible Attributes

Only include specific attributes in serialization:

```python
class User(Model):
    visible = ['name', 'email', 'created_at']
```

### Database Connection

Specify a different database connection:

```python
class User(Model):
    connection = 'mysql'  # Use specific connection
```

## Querying Models

All query operations are asynchronous and must be awaited.

### Retrieving Models

```python
import asyncio
from app.models.user import User

# Get all users
users = await User.all()

# Get all users with specific columns
users = await User.all(['name', 'email'])

# Get first user
user = await User.first()

# Find user by primary key
user = await User.find(1)

# Find user or raise exception
user = await User.find_or_fail(1)

# Get first user or raise exception
user = await User.first_or_fail()
```

### Query Constraints

```python
# Basic where clause
users = await User.where('name', 'John').get()

# Where with operator
users = await User.where('age', '>', 18).get()

# Multiple where clauses
users = await (User.where('status', 'active')
              .where('age', '>', 21)
              .get())

# Or conditions
users = await (User.where('name', 'John')
              .or_where('name', 'Jane')
              .get())

# Where in
users = await User.where_in('id', [1, 2, 3]).get()

# Where null
users = await User.where_null('deleted_at').get()

# Where not null
users = await User.where_not_null('email_verified_at').get()

# Where between
users = await User.where_between('age', 18, 65).get()

# Where like
users = await User.where('email', 'LIKE', '%@gmail.com').get()
```

### Ordering and Limiting

```python
# Order by
users = await User.order_by('name', 'asc').get()
users = await User.order_by('created_at', 'desc').get()

# Latest and oldest (by created_at)
users = await User.latest().get()
users = await User.oldest().get()

# Limit and offset
users = await User.take(10).get()
users = await User.skip(10).take(10).get()
```

### Aggregates

```python
# Count
count = await User.count()
count = await User.where('status', 'active').count()

# Max, min, avg, sum
max_age = await User.max('age')
min_age = await User.min('age')
avg_age = await User.avg('age')
total_points = await User.sum('points')
```

## Creating and Updating

### Creating Models

```python
# Create and save
user = await User.create({
    'name': 'John Doe',
    'email': 'john@example.com'
})

# Create instance and save separately
user = User({
    'name': 'Jane Doe',
    'email': 'jane@example.com'
})
await user.save()

# Mass assignment with fill
user = User()
user.fill({
    'name': 'Bob Smith',
    'email': 'bob@example.com'
})
await user.save()
```

### Updating Models

```python
# Update existing model
user = await User.find(1)
user.name = 'Updated Name'
user.email = 'updated@example.com'
await user.save()

# Update multiple attributes
user = await User.find(1)
user.fill({
    'name': 'New Name',
    'bio': 'New bio'
})
await user.save()

# Mass update
await User.where('status', 'pending').update({
    'status': 'approved'
})
```

### Upserting

```python
# Find or create
user = await User.find_or_create(
    {'email': 'john@example.com'},
    {'name': 'John Doe', 'status': 'active'}
)

# Update or create
user = await User.update_or_create(
    {'email': 'john@example.com'},
    {'name': 'John Doe', 'last_login': datetime.now()}
)
```

### Deleting Models

```python
# Delete model instance
user = await User.find(1)
await user.delete()

# Delete by query
await User.where('status', 'inactive').delete()

# Soft delete (if enabled)
class User(Model):
    soft_deletes = True
    deleted_at = 'deleted_at'

user = await User.find(1)
await user.delete()  # Sets deleted_at timestamp

# Restore soft deleted model
await user.restore()
```

## Relationships

Define relationships between models:

### One-to-One (Has One)

```python
class User(Model):
    def profile(self):
        return self.has_one(UserProfile, 'user_id', 'id')

class UserProfile(Model):
    def user(self):
        return self.belongs_to(User, 'user_id', 'id')
```

### One-to-Many (Has Many)

```python
class User(Model):
    def posts(self):
        return self.has_many(BlogPost, 'user_id', 'id')

class BlogPost(Model):
    def user(self):
        return self.belongs_to(User, 'user_id', 'id')
```

### Many-to-Many (Belongs To Many)

```python
class User(Model):
    def roles(self):
        return self.belongs_to_many(
            Role, 
            'user_roles',      # Pivot table
            'user_id',         # Foreign key
            'role_id'          # Related key
        )

class Role(Model):
    def users(self):
        return self.belongs_to_many(User, 'user_roles', 'role_id', 'user_id')
```

## Scopes

Define reusable query constraints:

```python
class User(Model):
    @classmethod
    def active(cls):
        """Scope to get only active users."""
        return cls.where('status', 'active')
    
    @classmethod
    def verified(cls):
        """Scope to get only verified users."""
        return cls.where_not_null('email_verified_at')
    
    @classmethod
    def recent(cls, days=30):
        """Scope to get recently created users."""
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=days)
        return cls.where('created_at', '>', cutoff)

# Usage
active_users = await User.active().get()
recent_verified = await User.recent(7).verified().get()
```

## Accessors and Mutators

Transform attribute values when getting or setting:

### Accessors (Getters)

```python
class User(Model):
    def get_full_name_attribute(self):
        """Accessor for full_name computed attribute."""
        return f"{self.first_name} {self.last_name}"
    
    def get_avatar_url_attribute(self):
        """Accessor for avatar_url computed attribute."""
        return f"https://cdn.example.com/avatars/{self.id}.jpg"

# Usage
user = await User.find(1)
print(user.full_name)    # Calls get_full_name_attribute()
print(user.avatar_url)   # Calls get_avatar_url_attribute()
```

### Mutators (Setters)

```python
class User(Model):
    def set_name_attribute(self, value):
        """Mutator to automatically capitalize names."""
        self.attributes['name'] = value.title() if value else None
    
    def set_email_attribute(self, value):
        """Mutator to automatically lowercase emails."""
        self.attributes['email'] = value.lower() if value else None

# Usage
user = User()
user.name = 'john doe'      # Stored as 'John Doe'
user.email = 'JOHN@EXAMPLE.COM'  # Stored as 'john@example.com'
```

## Attribute Casting

Automatically cast attributes to specific types:

```python
class User(Model):
    casts = {
        'id': 'int',
        'is_active': 'boolean',
        'metadata': 'json',
        'birth_date': 'datetime',
        'score': 'float',
        'bio': 'string'
    }

# Available cast types:
# 'int', 'float', 'string', 'boolean', 'json', 'datetime'

# Usage
user = await User.find(1)
print(type(user.is_active))  # <class 'bool'>
print(type(user.metadata))   # <class 'dict'>
```

## Serialization

Convert models to dictionaries or JSON:

```python
# Convert to dictionary
user = await User.find(1)
user_data = user.to_dict()

# Include hidden attributes
user_data = user.to_dict(include_hidden=True)

# Convert to JSON string
user_json = user.to_json()

# Custom serialization with hidden/visible
class User(Model):
    hidden = ['password', 'remember_token']
    # Only password and remember_token are excluded

class User(Model):
    visible = ['id', 'name', 'email']
    # Only id, name, and email are included
```

## Events

Define model events for lifecycle hooks:

```python
class User(Model):
    async def saving(self):
        """Called before creating or updating."""
        print(f"Saving user: {self.name}")
        return True  # Return False to cancel save
    
    async def saved(self):
        """Called after creating or updating."""
        print(f"User saved: {self.name}")
    
    async def creating(self):
        """Called before creating (insert)."""
        self.created_by = get_current_user_id()
        return True
    
    async def created(self):
        """Called after creating (insert)."""
        await send_welcome_email(self.email)
    
    async def updating(self):
        """Called before updating."""
        return True
    
    async def updated(self):
        """Called after updating."""
        await log_user_update(self.id)
    
    async def deleting(self):
        """Called before deleting."""
        return True
    
    async def deleted(self):
        """Called after deleting."""
        await cleanup_user_files(self.id)
```

## Advanced Features

### Model State Tracking

```python
user = await User.find(1)

# Check if model exists in database
print(user.exists)  # True

# Check if model has been modified
user.name = 'New Name'
print(user.is_dirty())  # True
print(user.is_clean())  # False

# Check specific attributes
print(user.is_dirty(['name']))  # True
print(user.is_dirty(['email'])) # False

# Get dirty attributes
dirty = user.get_dirty()  # {'name': 'New Name'}

# Get original values
original_name = user.get_original('name')
original_attrs = user.get_original()  # All original attributes
```

### Model Cloning

```python
user = await User.find(1)

# Clone model (creates new instance)
cloned_user = user.clone()
cloned_user.email = 'new@example.com'
await cloned_user.save()  # Creates new record
```

### Fresh Models

```python
user = await User.find(1)
user.name = 'Modified'

# Get fresh instance from database
fresh_user = await user.fresh()
print(fresh_user.name)  # Original name from database
```

## Complete API Reference

### Class Methods

```python
# Querying
await User.all(columns=None)
await User.find(id, columns=None)
await User.find_or_fail(id, columns=None)
await User.first(columns=None)
await User.first_or_fail(columns=None)
await User.where(column, operator=None, value=None)

# Creating
await User.create(attributes)
await User.find_or_create(attributes, values=None)
await User.update_or_create(attributes, values=None)

# Query Building
User.query()
User.select(*columns)
User.where(column, operator, value)
User.or_where(column, operator, value)
User.where_in(column, values)
User.where_not_in(column, values)
User.where_null(column)
User.where_not_null(column)
User.where_between(column, min_val, max_val)
User.order_by(column, direction='asc')
User.group_by(*columns)
User.having(column, operator, value)
User.take(limit)
User.skip(offset)
User.latest(column='created_at')
User.oldest(column='created_at')

# Aggregates
User.count(column='*')
User.max(column)
User.min(column)
User.avg(column)
User.sum(column)

# Utility
User.get_table_name()
User.get_connection_name()
User.get_db_manager()
```

### Instance Methods

```python
# Attributes
user.fill(attributes)
user.set_attribute(key, value)
user.get_attribute(key)
user.get_key()  # Primary key value
user.get_key_name()  # Primary key column name

# State
user.is_dirty(attributes=None)
user.is_clean(attributes=None)
user.get_dirty()
user.sync_original()
user.get_original(key=None, default=None)

# Persistence
await user.save(options=None)
await user.delete()
await user.restore()  # For soft deletes

# Serialization
user.to_dict(include_hidden=False)
user.to_json(include_hidden=False)

# Relationships
user.has_one(related_model, foreign_key=None, local_key=None)
user.has_many(related_model, foreign_key=None, local_key=None)
user.belongs_to(related_model, foreign_key=None, owner_key=None)
user.belongs_to_many(related_model, table=None, foreign_pivot_key=None, related_pivot_key=None)
```

### Model Configuration Attributes

```python
class MyModel(Model):
    # Table configuration
    table = 'custom_table_name'
    primary_key = 'id'
    incrementing = True
    key_type = 'int'
    
    # Mass assignment
    fillable = []
    guarded = ['*']
    
    # Serialization
    hidden = []
    visible = []
    
    # Timestamps
    timestamps = True
    created_at = 'created_at'
    updated_at = 'updated_at'
    
    # Soft deletes
    soft_deletes = False
    deleted_at = 'deleted_at'
    
    # Database connection
    connection = None
    
    # Attribute casting
    casts = {}
    
    # Date attributes
    dates = []
    date_format = '%Y-%m-%d %H:%M:%S'
```

## Example Usage

Here's a complete example showing various ORM features:

```python
from larapy.orm.model import Model
from datetime import datetime

class User(Model):
    fillable = ['name', 'email', 'bio', 'is_active']
    hidden = ['password']
    casts = {
        'is_active': 'boolean',
        'metadata': 'json',
        'last_login': 'datetime'
    }
    
    @classmethod
    def active(cls):
        return cls.where('is_active', True)
    
    def get_display_name_attribute(self):
        return self.name.title() if self.name else 'Anonymous'
    
    def set_email_attribute(self, value):
        self.attributes['email'] = value.lower() if value else None
    
    async def creating(self):
        self.metadata = {'created_via': 'api'}
        return True

# Usage
async def example():
    # Create user
    user = await User.create({
        'name': 'john doe',
        'email': 'JOHN@EXAMPLE.COM',
        'is_active': True
    })
    
    # Query users
    active_users = await User.active().get()
    
    # Update user
    user.bio = 'Software Developer'
    await user.save()
    
    # Serialize
    user_data = user.to_dict()
    print(user_data)
```

This comprehensive guide covers all major features of the Larapy ORM. For more specific use cases or advanced scenarios, refer to the individual method documentation in the source code.