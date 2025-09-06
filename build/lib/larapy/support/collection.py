"""
Collection class providing fluent array manipulation.

This module provides a Laravel-like Collection class with fluent API
for filtering, transforming, and manipulating arrays/lists.
"""

from typing import Any, Callable, Dict, Iterable, List, Optional, Union
import operator
from functools import reduce


class Collection:
    """
    A fluent wrapper for working with arrays of data.
    
    Provides Laravel-like collection functionality with method chaining
    for filtering, mapping, reducing, and other array operations.
    """
    
    def __init__(self, items: Any = None):
        """
        Initialize the collection.
        
        Args:
            items: The items for the collection
        """
        if items is None:
            self._items = []
        elif isinstance(items, (list, tuple)):
            self._items = list(items)
        elif isinstance(items, dict):
            self._items = list(items.items())
        elif hasattr(items, '__iter__'):
            self._items = list(items)
        else:
            self._items = [items]
    
    def all(self) -> List[Any]:
        """
        Get all items in the collection.
        
        Returns:
            All items as a list
        """
        return self._items.copy()
    
    def count(self) -> int:
        """
        Count the number of items in the collection.
        
        Returns:
            Number of items
        """
        return len(self._items)
    
    def first(self, callback: Optional[Callable] = None, default: Any = None) -> Any:
        """
        Get the first item in the collection.
        
        Args:
            callback: Optional callback to find first matching item
            default: Default value if no item found
            
        Returns:
            The first item or default
        """
        if not self._items:
            return default
        
        if callback is None:
            return self._items[0]
        
        for item in self._items:
            if callback(item):
                return item
        
        return default
    
    def last(self, callback: Optional[Callable] = None, default: Any = None) -> Any:
        """
        Get the last item in the collection.
        
        Args:
            callback: Optional callback to find last matching item
            default: Default value if no item found
            
        Returns:
            The last item or default
        """
        if not self._items:
            return default
        
        if callback is None:
            return self._items[-1]
        
        # Search from the end
        for item in reversed(self._items):
            if callback(item):
                return item
        
        return default
    
    def filter(self, callback: Optional[Callable] = None) -> "Collection":
        """
        Filter items using a callback.
        
        Args:
            callback: Filter callback (defaults to truthiness)
            
        Returns:
            New filtered collection
        """
        if callback is None:
            # Filter falsy values
            filtered = [item for item in self._items if item]
        else:
            filtered = [item for item in self._items if callback(item)]
        
        return Collection(filtered)
    
    def where(self, key: str, operator_or_value: Any = None, value: Any = None) -> "Collection":
        """
        Filter items by a given key value pair.
        
        Args:
            key: The key to filter by
            operator_or_value: Operator or value to compare
            value: Value to compare (if operator provided)
            
        Returns:
            New filtered collection
        """
        if value is None:
            # where('key', 'value') format
            target_value = operator_or_value
            op = operator.eq
        else:
            # where('key', '>', 'value') format
            target_value = value
            op_map = {
                '=': operator.eq,
                '==': operator.eq,
                '!=': operator.ne,
                '<>': operator.ne,
                '>': operator.gt,
                '>=': operator.ge,
                '<': operator.lt,
                '<=': operator.le,
                'in': lambda x, y: x in y,
                'not in': lambda x, y: x not in y,
            }
            op = op_map.get(operator_or_value, operator.eq)
        
        def check_item(item):
            if isinstance(item, dict):
                item_value = item.get(key)
            elif hasattr(item, key):
                item_value = getattr(item, key)
            else:
                return False
            
            try:
                return op(item_value, target_value)
            except:
                return False
        
        return self.filter(check_item)
    
    def map(self, callback: Callable) -> "Collection":
        """
        Transform each item using a callback.
        
        Args:
            callback: Transformation callback
            
        Returns:
            New transformed collection
        """
        mapped = [callback(item) for item in self._items]
        return Collection(mapped)
    
    def pluck(self, key: str, value_key: Optional[str] = None) -> "Collection":
        """
        Get a list of values for a given key.
        
        Args:
            key: The key to pluck
            value_key: Optional key to use as values in resulting dict
            
        Returns:
            New collection with plucked values
        """
        results = []
        
        for item in self._items:
            if isinstance(item, dict):
                item_value = item.get(key)
            elif hasattr(item, key):
                item_value = getattr(item, key)
            else:
                continue
            
            if value_key is None:
                results.append(item_value)
            else:
                # Create key-value pairs
                if isinstance(item, dict):
                    dict_key = item.get(value_key)
                elif hasattr(item, value_key):
                    dict_key = getattr(item, value_key)
                else:
                    continue
                
                results.append({dict_key: item_value})
        
        return Collection(results)
    
    def reduce(self, callback: Callable, initial: Any = None) -> Any:
        """
        Reduce the collection to a single value.
        
        Args:
            callback: Reduction callback
            initial: Initial value
            
        Returns:
            Reduced value
        """
        if initial is None:
            return reduce(callback, self._items)
        else:
            return reduce(callback, self._items, initial)
    
    def sum(self, key: Optional[str] = None) -> Union[int, float]:
        """
        Sum the values in the collection.
        
        Args:
            key: Optional key to sum by
            
        Returns:
            Sum of values
        """
        if key is None:
            return sum(self._items)
        
        total = 0
        for item in self._items:
            if isinstance(item, dict):
                value = item.get(key, 0)
            elif hasattr(item, key):
                value = getattr(item, key, 0)
            else:
                value = 0
            
            try:
                total += float(value)
            except (ValueError, TypeError):
                pass
        
        return total
    
    def avg(self, key: Optional[str] = None) -> Union[int, float]:
        """
        Get the average of values in the collection.
        
        Args:
            key: Optional key to average by
            
        Returns:
            Average value
        """
        if not self._items:
            return 0
        
        return self.sum(key) / len(self._items)
    
    def max(self, key: Optional[str] = None) -> Any:
        """
        Get the maximum value.
        
        Args:
            key: Optional key to get max by
            
        Returns:
            Maximum value
        """
        if not self._items:
            return None
        
        if key is None:
            return max(self._items)
        
        values = []
        for item in self._items:
            if isinstance(item, dict):
                value = item.get(key)
            elif hasattr(item, key):
                value = getattr(item, key)
            else:
                continue
            
            if value is not None:
                values.append(value)
        
        return max(values) if values else None
    
    def min(self, key: Optional[str] = None) -> Any:
        """
        Get the minimum value.
        
        Args:
            key: Optional key to get min by
            
        Returns:
            Minimum value
        """
        if not self._items:
            return None
        
        if key is None:
            return min(self._items)
        
        values = []
        for item in self._items:
            if isinstance(item, dict):
                value = item.get(key)
            elif hasattr(item, key):
                value = getattr(item, key)
            else:
                continue
            
            if value is not None:
                values.append(value)
        
        return min(values) if values else None
    
    def sort_by(self, key: Union[str, Callable], reverse: bool = False) -> "Collection":
        """
        Sort the collection by a given key.
        
        Args:
            key: Key to sort by or callback function
            reverse: Whether to reverse the sort
            
        Returns:
            New sorted collection
        """
        if callable(key):
            sorted_items = sorted(self._items, key=key, reverse=reverse)
        else:
            def get_sort_key(item):
                if isinstance(item, dict):
                    return item.get(key, '')
                elif hasattr(item, key):
                    return getattr(item, key, '')
                else:
                    return ''
            
            sorted_items = sorted(self._items, key=get_sort_key, reverse=reverse)
        
        return Collection(sorted_items)
    
    def group_by(self, key: Union[str, Callable]) -> "Collection":
        """
        Group the collection by a given key.
        
        Args:
            key: Key to group by or callback function
            
        Returns:
            New collection of grouped items
        """
        groups = {}
        
        for item in self._items:
            if callable(key):
                group_key = key(item)
            elif isinstance(item, dict):
                group_key = item.get(key)
            elif hasattr(item, key):
                group_key = getattr(item, key)
            else:
                group_key = 'unknown'
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)
        
        # Convert groups to collections
        for group_key in groups:
            groups[group_key] = Collection(groups[group_key])
        
        return Collection(groups)
    
    def unique(self, key: Optional[str] = None) -> "Collection":
        """
        Get unique items from the collection.
        
        Args:
            key: Optional key to determine uniqueness
            
        Returns:
            New collection with unique items
        """
        if key is None:
            # Use set to get unique items (only works with hashable items)
            seen = set()
            unique_items = []
            for item in self._items:
                try:
                    if item not in seen:
                        seen.add(item)
                        unique_items.append(item)
                except TypeError:
                    # Item not hashable, use linear search
                    if item not in unique_items:
                        unique_items.append(item)
            return Collection(unique_items)
        
        seen = set()
        unique_items = []
        
        for item in self._items:
            if isinstance(item, dict):
                item_key = item.get(key)
            elif hasattr(item, key):
                item_key = getattr(item, key)
            else:
                item_key = None
            
            if item_key not in seen:
                seen.add(item_key)
                unique_items.append(item)
        
        return Collection(unique_items)
    
    def take(self, limit: int) -> "Collection":
        """
        Take a limited number of items.
        
        Args:
            limit: Number of items to take
            
        Returns:
            New collection with limited items
        """
        if limit >= 0:
            return Collection(self._items[:limit])
        else:
            return Collection(self._items[limit:])
    
    def skip(self, count: int) -> "Collection":
        """
        Skip a number of items.
        
        Args:
            count: Number of items to skip
            
        Returns:
            New collection with remaining items
        """
        return Collection(self._items[count:])
    
    def chunk(self, size: int) -> "Collection":
        """
        Break the collection into chunks.
        
        Args:
            size: Size of each chunk
            
        Returns:
            New collection of chunks
        """
        chunks = []
        for i in range(0, len(self._items), size):
            chunk = self._items[i:i + size]
            chunks.append(Collection(chunk))
        
        return Collection(chunks)
    
    def flatten(self, depth: int = 1) -> "Collection":
        """
        Flatten a multi-dimensional collection.
        
        Args:
            depth: Depth to flatten
            
        Returns:
            Flattened collection
        """
        def _flatten(items, current_depth):
            result = []
            for item in items:
                if isinstance(item, (list, tuple)) and current_depth > 0:
                    result.extend(_flatten(item, current_depth - 1))
                else:
                    result.append(item)
            return result
        
        flattened = _flatten(self._items, depth)
        return Collection(flattened)
    
    def is_empty(self) -> bool:
        """
        Check if the collection is empty.
        
        Returns:
            True if empty, False otherwise
        """
        return len(self._items) == 0
    
    def is_not_empty(self) -> bool:
        """
        Check if the collection is not empty.
        
        Returns:
            True if not empty, False otherwise
        """
        return not self.is_empty()
    
    def to_list(self) -> List[Any]:
        """
        Convert to a regular Python list.
        
        Returns:
            List representation
        """
        return self._items.copy()
    
    def to_dict(self) -> Dict[Any, Any]:
        """
        Convert to a dictionary (if items are key-value pairs).
        
        Returns:
            Dictionary representation
        """
        result = {}
        for item in self._items:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                key, value = item
                result[key] = value
            elif isinstance(item, dict):
                result.update(item)
        
        return result
    
    def __len__(self) -> int:
        """Get collection length."""
        return len(self._items)
    
    def __iter__(self):
        """Make collection iterable."""
        return iter(self._items)
    
    def __getitem__(self, key) -> Any:
        """Allow indexing."""
        return self._items[key]
    
    def __setitem__(self, key, value) -> None:
        """Allow item assignment."""
        self._items[key] = value
    
    def __contains__(self, item) -> bool:
        """Allow 'in' operator."""
        return item in self._items
    
    def __str__(self) -> str:
        """String representation."""
        return str(self._items)
    
    def __repr__(self) -> str:
        """Developer representation."""
        return f"Collection({self._items!r})"