"""
Database seeding system for Larapy.

This module provides database seeding functionality for populating tables
with test or initial data.
"""

import importlib
import importlib.util
import os
from typing import Dict, List, Optional, Type, Any
from abc import ABC, abstractmethod
from ..connection import DatabaseManager


class Seeder(ABC):
    """Base class for database seeders."""
    
    def __init__(self):
        self.connection: Optional[str] = None
        
    @abstractmethod
    async def run(self) -> None:
        """Run the seeder."""
        pass
        
    async def call(self, seeder_class: Type['Seeder']) -> None:
        """Call another seeder."""
        seeder_instance = seeder_class()
        if self.connection:
            seeder_instance.connection = self.connection
        await seeder_instance.run()


class DatabaseSeeder(Seeder):
    """Main database seeder that calls other seeders."""
    
    async def run(self) -> None:
        """Run all seeders."""
        # Override this method in your application's DatabaseSeeder
        pass


class SeederRunner:
    """Handles running database seeders."""
    
    def __init__(self, db_manager: DatabaseManager, seeders_path: str):
        self.db_manager = db_manager
        self.seeders_path = seeders_path
        
    async def run(self, seeder_class: Optional[str] = None, 
                 connection: Optional[str] = None) -> List[str]:
        """Run database seeders."""
        if seeder_class:
            # Run specific seeder
            seeder = self._load_seeder_class(seeder_class)
            if seeder:
                seeder_instance = seeder()
                if connection:
                    seeder_instance.connection = connection
                await seeder_instance.run()
                return [seeder_class]
            else:
                raise ValueError(f"Seeder class '{seeder_class}' not found")
        else:
            # Run DatabaseSeeder
            return await self.run('DatabaseSeeder', connection)
            
    def _load_seeder_class(self, seeder_name: str) -> Optional[Type[Seeder]]:
        """Load seeder class from file."""
        try:
            # First try to find by class name
            seeder_files = self._get_seeder_files()
            
            for seeder_file in seeder_files:
                seeder_class = self._load_seeder_from_file(seeder_file, seeder_name)
                if seeder_class:
                    return seeder_class
                    
            return None
            
        except Exception as e:
            print(f"Failed to load seeder {seeder_name}: {e}")
            return None
            
    def _get_seeder_files(self) -> List[str]:
        """Get all seeder files from the seeders directory."""
        if not os.path.exists(self.seeders_path):
            return []
            
        files = []
        for file in os.listdir(self.seeders_path):
            if file.endswith('.py') and not file.startswith('__'):
                files.append(file)
                
        return files
        
    def _load_seeder_from_file(self, seeder_file: str, 
                              seeder_name: str) -> Optional[Type[Seeder]]:
        """Load seeder class from a specific file."""
        try:
            file_path = os.path.join(self.seeders_path, seeder_file)
            
            # Load module
            spec = importlib.util.spec_from_file_location("seeder", file_path)
            if not spec or not spec.loader:
                return None
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find seeder class
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, Seeder) and 
                    attr is not Seeder and
                    attr.__name__ == seeder_name):
                    return attr
                    
            return None
            
        except Exception:
            return None
    
    def run_all(self, seeders_path: Path) -> int:
        """Run all seeders in a directory synchronously."""
        import asyncio
        self.seeders_path = str(seeders_path)
        
        seeder_files = []
        for file in seeders_path.glob("*.py"):
            if file.name != "__init__.py":
                seeder_files.append(file.name)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            count = 0
            for seeder_file in seeder_files:
                loop.run_until_complete(self.run(seeder_file))
                count += 1
            return count
        finally:
            loop.close()
    
    def run_single(self, seeder_name: str):
        """Run a single seeder synchronously."""
        import asyncio
        seeder_file = f"{seeder_name}.py"
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.run(seeder_file))
        finally:
            loop.close()


class ModelSeeder(Seeder):
    """Helper seeder for seeding model data."""
    
    def __init__(self, model_class, data: List[Dict[str, Any]]):
        super().__init__()
        self.model_class = model_class
        self.data = data
        
    async def run(self) -> None:
        """Seed the model data."""
        for item in self.data:
            await self.model_class.create(item)


# Example seeder implementations
class UserSeeder(Seeder):
    """Example user seeder."""
    
    async def run(self) -> None:
        """Seed users table."""
        from larapy.orm import Model
        
        # This would typically import your actual User model
        # from app.models import User
        
        users_data = [
            {
                'name': 'Admin User',
                'email': 'admin@example.com',
                'password': 'hashed_password_here'
            },
            {
                'name': 'Test User',
                'email': 'test@example.com', 
                'password': 'hashed_password_here'
            },
            {
                'name': 'Demo User',
                'email': 'demo@example.com',
                'password': 'hashed_password_here'
            }
        ]
        
        # Create a simple User model for demonstration
        class User(Model):
            table = 'users'
            fillable = ['name', 'email', 'password']
            
        for user_data in users_data:
            await User.create(user_data)
            
        print(f"Seeded {len(users_data)} users")


class PostSeeder(Seeder):
    """Example post seeder."""
    
    async def run(self) -> None:
        """Seed posts table."""
        from larapy.orm import Model
        
        posts_data = [
            {
                'title': 'Welcome to Larapy',
                'content': 'This is the first post in our Larapy application.',
                'user_id': 1,
                'published': True
            },
            {
                'title': 'Getting Started with ORM',
                'content': 'Learn how to use Larapy ORM for database operations.',
                'user_id': 1,
                'published': True
            },
            {
                'title': 'Building APIs with Larapy',
                'content': 'A comprehensive guide to building REST APIs.',
                'user_id': 2,
                'published': False
            }
        ]
        
        class Post(Model):
            table = 'posts'
            fillable = ['title', 'content', 'user_id', 'published']
            
        for post_data in posts_data:
            await Post.create(post_data)
            
        print(f"Seeded {len(posts_data)} posts")


class RoleSeeder(Seeder):
    """Example role seeder for authentication."""
    
    async def run(self) -> None:
        """Seed roles table."""
        from larapy.orm import Model
        
        roles_data = [
            {'name': 'admin', 'description': 'Administrator role'},
            {'name': 'editor', 'description': 'Content editor role'},
            {'name': 'user', 'description': 'Regular user role'}
        ]
        
        class Role(Model):
            table = 'roles'
            fillable = ['name', 'description']
            
        for role_data in roles_data:
            await Role.create(role_data)
            
        print(f"Seeded {len(roles_data)} roles")


# Example DatabaseSeeder
class ExampleDatabaseSeeder(DatabaseSeeder):
    """Example main database seeder."""
    
    async def run(self) -> None:
        """Run all seeders in order."""
        print("Starting database seeding...")
        
        # Run seeders in order
        await self.call(RoleSeeder)
        await self.call(UserSeeder)
        await self.call(PostSeeder)
        
        print("Database seeding completed!")


def make_seeder_name(description: str) -> str:
    """Create a seeder class name from description."""
    # Convert to PascalCase
    words = description.replace('_', ' ').replace('-', ' ').split()
    class_name = ''.join(word.capitalize() for word in words)
    
    if not class_name.endswith('Seeder'):
        class_name += 'Seeder'
        
    return class_name


def create_seeder_file(seeder_name: str, seeders_path: str, table_name: Optional[str] = None) -> str:
    """Create a new seeder file."""
    # Ensure seeders directory exists
    os.makedirs(seeders_path, exist_ok=True)
    
    # Create filename
    filename = f"{seeder_name.lower()}.py"
    file_path = os.path.join(seeders_path, filename)
    
    # Generate seeder content
    template = f'''"""
{seeder_name} seeder.

This seeder populates the database with sample data.
"""

from larapy.database.migrations.seeder import Seeder
from larapy.orm import Model


class {seeder_name}(Seeder):
    """Seeder for {table_name or 'data'}."""
    
    async def run(self) -> None:
        """Run the seeder."""
        # TODO: Implement seeder logic
        
        # Example:
        # data = [
        #     {{'field1': 'value1', 'field2': 'value2'}},
        #     {{'field1': 'value3', 'field2': 'value4'}},
        # ]
        # 
        # class YourModel(Model):
        #     table = '{table_name or 'your_table'}'
        #     fillable = ['field1', 'field2']
        # 
        # for item in data:
        #     await YourModel.create(item)
        
        print("Seeder {seeder_name} completed")
'''
    
    # Write file
    with open(file_path, 'w') as f:
        f.write(template)
        
    return file_path