"""
Create user_roles pivot table migration.
"""

from ...database.migrations.migration import Migration
from ...database.schema import Schema


class CreateUserRolesTable(Migration):
    """Create user_roles pivot table migration."""
    
    def up(self):
        """Run the migration."""
        Schema.create('user_roles', lambda table: [
            table.id(),
            table.foreign_id('user_id').constrained('users').on_delete('cascade'),
            table.foreign_id('role_id').constrained('roles').on_delete('cascade'),
            table.timestamps(),
            
            # Create unique index to prevent duplicate assignments
            table.unique(['user_id', 'role_id'])
        ])
    
    def down(self):
        """Rollback the migration."""
        Schema.drop_if_exists('user_roles')