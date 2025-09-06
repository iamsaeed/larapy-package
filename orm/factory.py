"""
Model factory system for Larapy.

This module provides a factory system for generating test data and model instances,
similar to Laravel's model factories.
"""

import random
import string
from typing import Any, Dict, List, Optional, Type, Callable, Union
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from .model import Model


class Factory(ABC):
    """Base factory class for generating model instances."""
    
    def __init__(self, model_class: Type[Model], count: int = 1):
        self.model_class = model_class
        self.count = count
        self._states = {}
        self._after_creating = []
        self._after_making = []
        
    @abstractmethod
    def definition(self) -> Dict[str, Any]:
        """Define the model's default state."""
        pass
        
    def state(self, state_name: str, attributes: Dict[str, Any]) -> 'Factory':
        """Define a state transformation for the factory."""
        factory = self.__class__(self.model_class, self.count)
        factory._states = self._states.copy()
        factory._states[state_name] = attributes
        factory._after_creating = self._after_creating.copy()
        factory._after_making = self._after_making.copy()
        return factory
        
    def count(self, count: int) -> 'Factory':
        """Set the count of models to create."""
        factory = self.__class__(self.model_class, count)
        factory._states = self._states.copy()
        factory._after_creating = self._after_creating.copy()
        factory._after_making = self._after_making.copy()
        return factory
        
    def after_creating(self, callback: Callable[[Model], None]) -> 'Factory':
        """Register a callback to run after creating a model."""
        factory = self.__class__(self.model_class, self.count)
        factory._states = self._states.copy()
        factory._after_creating = self._after_creating.copy()
        factory._after_making = self._after_making.copy()
        factory._after_creating.append(callback)
        return factory
        
    def after_making(self, callback: Callable[[Model], None]) -> 'Factory':
        """Register a callback to run after making a model."""
        factory = self.__class__(self.model_class, self.count)
        factory._states = self._states.copy()
        factory._after_creating = self._after_creating.copy()
        factory._after_making = self._after_making.copy()
        factory._after_making.append(callback)
        return factory
        
    def raw(self, attributes: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Generate raw attribute data without creating model instances."""
        if self.count == 1:
            return self._generate_attributes(attributes)
        else:
            return [self._generate_attributes(attributes) for _ in range(self.count)]
            
    def make(self, attributes: Optional[Dict[str, Any]] = None) -> Union[Model, List[Model]]:
        """Create model instances without persisting to database."""
        if self.count == 1:
            attrs = self._generate_attributes(attributes)
            instance = self.model_class(attrs)
            
            # Run after making callbacks
            for callback in self._after_making:
                callback(instance)
                
            return instance
        else:
            instances = []
            for _ in range(self.count):
                attrs = self._generate_attributes(attributes)
                instance = self.model_class(attrs)
                
                # Run after making callbacks
                for callback in self._after_making:
                    callback(instance)
                    
                instances.append(instance)
            return instances
            
    async def create(self, attributes: Optional[Dict[str, Any]] = None) -> Union[Model, List[Model]]:
        """Create and persist model instances to database."""
        if self.count == 1:
            attrs = self._generate_attributes(attributes)
            instance = await self.model_class.create(attrs)
            
            # Run after creating callbacks
            for callback in self._after_creating:
                callback(instance)
                
            return instance
        else:
            instances = []
            for _ in range(self.count):
                attrs = self._generate_attributes(attributes)
                instance = await self.model_class.create(attrs)
                
                # Run after creating callbacks
                for callback in self._after_creating:
                    callback(instance)
                    
                instances.append(instance)
            return instances
            
    def _generate_attributes(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate attributes for a single model instance."""
        # Start with base definition
        attributes = self.definition()
        
        # Apply any states
        for state_attrs in self._states.values():
            attributes.update(state_attrs)
            
        # Apply overrides
        if overrides:
            attributes.update(overrides)
            
        return attributes


class FactoryRegistry:
    """Registry for managing model factories."""
    
    _factories: Dict[Type[Model], Type[Factory]] = {}
    
    @classmethod
    def register(cls, model_class: Type[Model], factory_class: Type[Factory]) -> None:
        """Register a factory for a model."""
        cls._factories[model_class] = factory_class
        
    @classmethod
    def get_factory(cls, model_class: Type[Model]) -> Optional[Type[Factory]]:
        """Get the factory for a model."""
        return cls._factories.get(model_class)
        
    @classmethod
    def has_factory(cls, model_class: Type[Model]) -> bool:
        """Check if a model has a registered factory."""
        return model_class in cls._factories


# Faker-like utilities for generating fake data
class Fake:
    """Utilities for generating fake data."""
    
    @staticmethod
    def name() -> str:
        """Generate a fake name."""
        first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa', 'William', 'Jessica']
        last_names = ['Smith', 'Johnson', 'Brown', 'Taylor', 'Miller', 'Wilson', 'Moore', 'Anderson', 'Thomas', 'Jackson']
        return f"{random.choice(first_names)} {random.choice(last_names)}"
        
    @staticmethod
    def email(domain: str = 'example.com') -> str:
        """Generate a fake email address."""
        username = ''.join(random.choices(string.ascii_lowercase, k=8))
        return f"{username}@{domain}"
        
    @staticmethod
    def password(length: int = 12) -> str:
        """Generate a fake password."""
        chars = string.ascii_letters + string.digits + '!@#$%^&*'
        return ''.join(random.choices(chars, k=length))
        
    @staticmethod
    def sentence(words: int = 6) -> str:
        """Generate a fake sentence."""
        word_list = [
            'lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit',
            'sed', 'do', 'eiusmod', 'tempor', 'incididunt', 'ut', 'labore', 'et', 'dolore',
            'magna', 'aliqua', 'enim', 'ad', 'minim', 'veniam', 'quis', 'nostrud'
        ]
        selected_words = random.choices(word_list, k=words)
        sentence = ' '.join(selected_words)
        return sentence.capitalize() + '.'
        
    @staticmethod
    def paragraph(sentences: int = 4) -> str:
        """Generate a fake paragraph."""
        return ' '.join([Fake.sentence() for _ in range(sentences)])
        
    @staticmethod
    def text(paragraphs: int = 3) -> str:
        """Generate fake text with multiple paragraphs."""
        return '\n\n'.join([Fake.paragraph() for _ in range(paragraphs)])
        
    @staticmethod
    def integer(min_val: int = 1, max_val: int = 1000) -> int:
        """Generate a random integer."""
        return random.randint(min_val, max_val)
        
    @staticmethod
    def float(min_val: float = 0.0, max_val: float = 100.0) -> float:
        """Generate a random float."""
        return random.uniform(min_val, max_val)
        
    @staticmethod
    def boolean() -> bool:
        """Generate a random boolean."""
        return random.choice([True, False])
        
    @staticmethod
    def choice(choices: List[Any]) -> Any:
        """Choose randomly from a list."""
        return random.choice(choices)
        
    @staticmethod
    def datetime_between(start_date: datetime = None, end_date: datetime = None) -> datetime:
        """Generate a random datetime between two dates."""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()
            
        time_between = end_date - start_date
        random_seconds = random.randint(0, int(time_between.total_seconds()))
        return start_date + timedelta(seconds=random_seconds)
        
    @staticmethod
    def date_between(start_date: datetime = None, end_date: datetime = None) -> datetime:
        """Generate a random date between two dates."""
        return Fake.datetime_between(start_date, end_date).date()
        
    @staticmethod
    def slug(words: int = 3) -> str:
        """Generate a URL-friendly slug."""
        word_list = ['awesome', 'great', 'wonderful', 'amazing', 'fantastic', 'incredible', 
                    'brilliant', 'excellent', 'outstanding', 'remarkable', 'superb', 'terrific']
        selected_words = random.choices(word_list, k=words)
        return '-'.join(selected_words)
        
    @staticmethod
    def uuid() -> str:
        """Generate a fake UUID."""
        import uuid
        return str(uuid.uuid4())


# Example factory implementations
class UserFactory(Factory):
    """Example factory for User model."""
    
    def definition(self) -> Dict[str, Any]:
        """Define the model's default state."""
        return {
            'name': Fake.name(),
            'email': Fake.email(),
            'password': 'hashed_password_here',  # In real app, this would be hashed
            'email_verified_at': None,
            'remember_token': None,
        }
        
    def verified(self) -> 'UserFactory':
        """Create a verified user state."""
        return self.state('verified', {
            'email_verified_at': datetime.now()
        })
        
    def admin(self) -> 'UserFactory':
        """Create an admin user state."""
        return self.state('admin', {
            'name': 'Admin User',
            'email': 'admin@example.com',
            'email_verified_at': datetime.now()
        })


class PostFactory(Factory):
    """Example factory for Post model."""
    
    def definition(self) -> Dict[str, Any]:
        """Define the model's default state."""
        return {
            'title': Fake.sentence(words=4).rstrip('.'),
            'content': Fake.text(paragraphs=3),
            'slug': Fake.slug(),
            'published': Fake.boolean(),
            'user_id': 1,  # Default to user ID 1
        }
        
    def published(self) -> 'PostFactory':
        """Create a published post state."""
        return self.state('published', {
            'published': True
        })
        
    def draft(self) -> 'PostFactory':
        """Create a draft post state."""
        return self.state('draft', {
            'published': False
        })


# Factory helper functions
def factory(model_class: Type[Model], count: int = 1) -> Factory:
    """Create a factory instance for a model."""
    factory_class = FactoryRegistry.get_factory(model_class)
    if not factory_class:
        raise ValueError(f"No factory registered for model {model_class.__name__}")
    return factory_class(model_class, count)


# Model factory mixin
class HasFactory:
    """Mixin to add factory methods to models."""
    
    @classmethod
    def factory(cls, count: int = 1) -> Factory:
        """Create a factory for this model."""
        factory_class = FactoryRegistry.get_factory(cls)
        if not factory_class:
            raise ValueError(f"No factory registered for model {cls.__name__}")
        return factory_class(cls, count)


# Example of how to use factories with models
"""
# In your model file
class User(Model, HasFactory):
    table = 'users'
    fillable = ['name', 'email', 'password']

# Register the factory
FactoryRegistry.register(User, UserFactory)

# Usage in tests
user = await User.factory().create()
users = await User.factory().count(5).create()
admin = await User.factory().admin().create()
verified_users = await User.factory().count(3).verified().create()

# Making without persisting
user_data = User.factory().raw()
user_instance = User.factory().make()
"""