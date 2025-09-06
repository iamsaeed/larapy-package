"""
Create user_permissions pivot table migration.
"""

from ...database.migrations.migration import Migration
from ...database.schema import Schema


class CreateUserPermissionsTable(Migration):
    """Create user_permissions pivot table migration."""
    
    def up(self):
        """Run the migration."""
        Schema.create('user_permissions', lambda table: [
            table.id(),
            table.foreign_id('user_id').constrained('users').on_delete('cascade'),
            table.foreign_id('permission_id').constrained('permissions').on_delete('cascade'),
            table.timestamps(),
            
            # Create unique index to prevent duplicate assignments
            table.unique(['user_id', 'permission_id'])
        ])
    
    def down(self):
        """Rollback the migration."""
        Schema.drop_if_exists('user_permissions')