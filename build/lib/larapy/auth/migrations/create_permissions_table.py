"""
Create permissions table migration.
"""

from ...database.migrations.migration import Migration
from ...database.schema import Schema


class CreatePermissionsTable(Migration):
    """Create permissions table migration."""
    
    def up(self):
        """Run the migration."""
        Schema.create('permissions', lambda table: [
            table.id(),
            table.string('name', 125).unique(),
            table.string('display_name', 255).nullable(),
            table.text('description').nullable(),
            table.string('guard_name', 125).default('web'),
            table.timestamps(),
            
            # Create unique index on name and guard_name
            table.unique(['name', 'guard_name'])
        ])
    
    def down(self):
        """Rollback the migration."""
        Schema.drop_if_exists('permissions')