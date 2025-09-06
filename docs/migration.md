# Larapy Migration System

## Overview

The Larapy Migration System provides a Laravel-like database migration experience for Python applications. It allows you to manage database schema changes in a version-controlled, systematic way with automatic migration tracking, batch management, and rollback capabilities.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Creating Migrations](#creating-migrations)
3. [Running Migrations](#running-migrations)
4. [Rolling Back Migrations](#rolling-back-migrations)
5. [Migration Status](#migration-status)
6. [Advanced Features](#advanced-features)
7. [Command Reference](#command-reference)
8. [Migration File Structure](#migration-file-structure)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Install Migration Repository
First, initialize the migration tracking system:

```bash
larapy migrate install
```

This creates the `migrations` table in your SQLite database to track executed migrations.

### 2. Create Your First Migration
Create a migration to set up a users table:

```bash
larapy make:migration create_users_table --create=users
```

### 3. Edit the Migration
Open the generated migration file in `database/migrations/` and define your table structure:

```python
def up(self):
    """Run the migrations."""
    def create_users_table(table: Blueprint):
        table.id()
        table.string('name')
        table.string('email').unique()
        table.string('password')
        table.timestamps()
    
    Schema.create('users', create_users_table)
```

### 4. Run the Migration
Execute your migrations:

```bash
larapy migrate run
```

## Creating Migrations

### Using Make Commands

#### Create Table Migration
```bash
larapy make:migration create_posts_table --create=posts
```

#### Modify Table Migration
```bash
larapy make:migration add_status_to_posts --table=posts
```

#### Blank Migration
```bash
larapy make:migration update_user_preferences
```

### Migration File Naming
Migrations are automatically named with timestamps in the format:
```
YYYY_MM_DD_HHMMSS_migration_name.py
```

Example: `2025_01_06_143022_create_users_table.py`

### Migration Class Structure

Every migration file contains a class that extends `Migration` with two methods:

```python
from larapy.database.migrations.migration import Migration
from larapy.database.schema import Schema, Blueprint

class CreateUsersTable(Migration):
    def up(self):
        """Run the migrations - define changes"""
        def create_users_table(table: Blueprint):
            table.id()
            table.string('name')
            table.string('email').unique()
            table.timestamps()
        
        Schema.create('users', create_users_table)
    
    def down(self):
        """Reverse the migrations - undo changes"""
        Schema.drop_if_exists('users')
```

## Running Migrations

### Basic Migration Execution

#### Run All Pending Migrations
```bash
larapy migrate run
```

#### Run Specific Number of Migrations
```bash
larapy migrate run --step=3
```

#### Dry Run (Show What Would Execute)
```bash
larapy migrate run --pretend
```

#### Run Migrations and Seeders
```bash
larapy migrate run --seed
```

### Alternative Commands

#### Shorthand Migration
```bash
larapy migrate
```

#### Using DB Command Group
```bash
larapy db:migrate
larapy db:migrate --seed
```

## Rolling Back Migrations

### Rollback Commands

#### Rollback Last Batch
```bash
larapy migrate rollback
```

#### Rollback Multiple Batches
```bash
larapy migrate rollback --step=3
```

#### Rollback All Migrations
```bash
larapy migrate reset
```

#### Dry Run Rollback
```bash
larapy migrate rollback --pretend
```

### Refresh and Fresh Migrations

#### Refresh (Reset + Migrate)
```bash
larapy migrate refresh
larapy migrate refresh --seed
```

#### Fresh (Drop All Tables + Migrate)
```bash
larapy migrate fresh
larapy migrate fresh --seed
```

## Migration Status

### Check Migration Status
```bash
larapy migrate status
```

Output example:
```
📊 Migration Status
──────────────────────────────────────────────────────────────────────
Migration                                          Batch    Status    
──────────────────────────────────────────────────────────────────────
2025_01_06_143022_create_users_table              1        ✅ Ran
2025_01_06_143045_create_posts_table              1        ✅ Ran
2025_01_06_143102_add_status_to_posts             N/A      ❌ Pending
──────────────────────────────────────────────────────────────────────
Total: 3 | Executed: 2 | Pending: 1
```

### Filtered Status Views

#### Show Only Pending Migrations
```bash
larapy migrate status --pending
```

#### Show Only Executed Migrations
```bash
larapy migrate status --executed
```

#### Verbose Status
```bash
larapy migrate status --verbose
```

## Advanced Features

### Database Inspection

#### Inspect All Tables
```bash
larapy db:inspect
```

#### Inspect Specific Table
```bash
larapy db:inspect --table=users
```

#### Show Sample Data
```bash
larapy db:inspect --table=users --show-data
```

### Schema Operations

#### View Database Schema
```bash
larapy db:schema
```

#### View Specific Table Schema
```bash
larapy db:schema --table=users
```

#### Export Schema as SQL
```bash
larapy db:schema --output=sql
```

### Database Management

#### Wipe Database
```bash
larapy db:wipe
```

#### Wipe but Keep Migrations Table
```bash
larapy db:wipe --keep-migrations
```

## Command Reference

### Migration Commands

| Command | Description | Options |
|---------|-------------|---------|
| `larapy migrate run` | Run pending migrations | `--step`, `--seed`, `--pretend`, `--force` |
| `larapy migrate rollback` | Rollback migrations | `--step`, `--pretend`, `--force` |
| `larapy migrate reset` | Rollback all migrations | `--pretend`, `--force` |
| `larapy migrate refresh` | Reset and re-run all migrations | `--seed`, `--force` |
| `larapy migrate fresh` | Drop all tables and re-migrate | `--seed`, `--force` |
| `larapy migrate status` | Show migration status | `--verbose`, `--pending`, `--executed` |
| `larapy migrate install` | Create migration repository | None |

### Make Commands

| Command | Description | Options |
|---------|-------------|---------|
| `larapy make:migration name` | Create new migration | `--create=table`, `--table=table` |
| `larapy make:model Name` | Create new model | `--migration`, `-m` |
| `larapy make:seeder NameSeeder` | Create new seeder | None |
| `larapy make:factory NameFactory` | Create new factory | `--model=Model` |

### Database Commands

| Command | Description | Options |
|---------|-------------|---------|
| `larapy db:migrate` | Run migrations (alias) | `--seed`, `--force` |
| `larapy db:rollback` | Rollback migrations (alias) | `--step`, `--force` |
| `larapy db:fresh` | Fresh migrate (alias) | `--seed`, `--force` |
| `larapy db:status` | Migration status (alias) | None |
| `larapy db:inspect` | Inspect database structure | `--table`, `--show-data` |
| `larapy db:schema` | View database schema | `--table`, `--output` |
| `larapy db:wipe` | Wipe all tables | `--keep-migrations`, `--force` |
| `larapy db:seed` | Run seeders | `--class` |

## Migration File Structure

### Directory Structure
```
database/
├── migrations/
│   ├── 2025_01_06_143022_create_users_table.py
│   ├── 2025_01_06_143045_create_posts_table.py
│   └── 2025_01_06_143102_add_status_to_posts.py
├── seeders/
│   ├── user_seeder.py
│   └── post_seeder.py
└── database.sqlite
```

### Migration Tracking

Migrations are tracked in the `migrations` table:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-incrementing ID |
| `migration` | VARCHAR(255) | Migration filename |
| `batch` | INTEGER | Batch number for grouped rollbacks |
| `executed_at` | TIMESTAMP | When the migration was executed |

### Batch System

The migration system uses batches to group migrations that were run together:

- **Batch 1**: Initial migrations run together
- **Batch 2**: Next set of migrations run together
- **Batch 3**: Subsequent migrations, etc.

This allows you to rollback the most recent group of migrations with:
```bash
larapy migrate rollback  # Rolls back the latest batch
larapy migrate rollback --step=2  # Rolls back the 2 most recent batches
```

## Best Practices

### 1. Migration Naming
- Use descriptive names that explain the change
- Follow the Laravel convention: `verb_table_description`
- Examples:
  - `create_users_table`
  - `add_email_to_users`
  - `drop_unused_columns_from_posts`

### 2. Migration Content
- Always implement both `up()` and `down()` methods
- Make migrations reversible whenever possible
- Test rollbacks before deploying

### 3. Schema Changes
- Create migrations for all schema changes
- Never edit existing migrations that have been run in production
- Create new migrations for schema corrections

### 4. Data Migrations
- Separate schema changes from data migrations
- Consider performance for large datasets
- Test data migrations thoroughly

### 5. Version Control
- Commit migrations with the code that depends on them
- Review migrations in code reviews
- Don't delete migration files from version control

## Schema Blueprint Reference

The Blueprint class provides methods for defining database schema:

### Column Types
```python
# Primary key
table.id()                          # Auto-incrementing primary key

# String columns
table.string('name')                # VARCHAR(255)
table.string('title', 100)         # VARCHAR(100)
table.text('description')           # TEXT

# Numeric columns
table.integer('count')              # INTEGER
table.bigInteger('big_count')       # BIGINT
table.decimal('price', 8, 2)        # DECIMAL(8,2)
table.float('rating')               # FLOAT
table.boolean('is_active')          # BOOLEAN

# Date/Time columns
table.timestamp('created_at')       # TIMESTAMP
table.timestamps()                  # created_at & updated_at
table.date('birth_date')            # DATE
table.time('start_time')            # TIME
table.datetime('event_time')        # DATETIME

# Special columns
table.json('metadata')              # JSON
table.binary('file_data')           # BLOB
```

### Column Modifiers
```python
table.string('email').unique()      # Add unique constraint
table.string('name').nullable()     # Allow NULL values
table.integer('sort_order').default(0)  # Set default value
table.string('status').index()      # Add index
```

### Indexes
```python
table.index('email')                # Single column index
table.index(['user_id', 'post_id']) # Composite index
table.unique('email')               # Unique constraint
table.unique(['user_id', 'role_id'])# Composite unique
```

### Foreign Keys
```python
table.foreign('user_id').references('id').on('users')
table.foreign('user_id').references('id').on('users').onDelete('cascade')
```

## Troubleshooting

### Common Issues

#### 1. Migration Table Not Found
```bash
# Error: no such table: migrations
larapy migrate install
```

#### 2. Migration File Not Found
Check that:
- Migration file exists in `database/migrations/`
- File follows naming convention
- File is not corrupted

#### 3. SQLite Database Locked
```bash
# Kill any processes using the database
pkill -f database.sqlite
```

#### 4. Migration Fails Partially
```bash
# Check status
larapy migrate status

# If needed, manually fix and re-run
larapy migrate run
```

### Debugging Tips

#### 1. Use Pretend Mode
```bash
larapy migrate run --pretend
larapy migrate rollback --pretend
```

#### 2. Check Migration Status
```bash
larapy migrate status --verbose
```

#### 3. Inspect Database State
```bash
larapy db:inspect
larapy db:schema
```

#### 4. Check Migration Files
Ensure migration files have proper:
- Class name (PascalCase)
- Method definitions (`up()` and `down()`)
- Proper imports

### Recovery Procedures

#### 1. Reset Migration State
If migrations are in an inconsistent state:

```bash
# WARNING: This will lose all data
larapy migrate fresh
```

#### 2. Manual Migration Table Fix
If the migration table is corrupted:

```bash
# Drop and recreate migration table
larapy db:wipe --keep-migrations=false
larapy migrate install
```

#### 3. Rollback to Specific Point
```bash
# Check current status
larapy migrate status

# Rollback specific number of batches
larapy migrate rollback --step=N
```

## Examples

### Example 1: User Management System

1. Create users migration:
```bash
larapy make:migration create_users_table --create=users
```

2. Edit migration:
```python
def up(self):
    def create_users_table(table: Blueprint):
        table.id()
        table.string('name')
        table.string('email').unique()
        table.string('password')
        table.boolean('is_active').default(True)
        table.timestamps()
    
    Schema.create('users', create_users_table)
```

3. Create roles migration:
```bash
larapy make:migration create_roles_table --create=roles
```

4. Add user-role relationship:
```bash
larapy make:migration add_role_to_users --table=users
```

5. Run all migrations:
```bash
larapy migrate run
```

### Example 2: Blog System

1. Create posts table:
```bash
larapy make:migration create_posts_table --create=posts
```

2. Add categories:
```bash
larapy make:migration create_categories_table --create=categories
larapy make:migration add_category_to_posts --table=posts
```

3. Add tags (many-to-many):
```bash
larapy make:migration create_tags_table --create=tags
larapy make:migration create_post_tag_table --create=post_tag
```

4. Run migrations with seeding:
```bash
larapy migrate run --seed
```

## Integration with Models

While this documentation focuses on the migration system, migrations work seamlessly with Larapy's ORM models:

```python
# In your model file (app/models/user.py)
from larapy.orm.model import Model

class User(Model):
    fillable = ['name', 'email', 'password']
    
    casts = {
        'created_at': 'datetime',
        'updated_at': 'datetime',
    }
```

The migration system ensures your database schema matches your model definitions, providing a complete database management solution for your Larapy applications.