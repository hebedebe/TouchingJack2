"""
Object pooling system to reduce garbage collection and improve performance
"""
from typing import Dict, List, Type, Any, Callable, Optional
import weakref
from abc import ABC, abstractmethod

class Poolable(ABC):
    """Interface for objects that can be pooled"""
    
    @abstractmethod
    def reset(self) -> None:
        """Reset object to initial state for reuse"""
        pass
    
    @abstractmethod
    def on_pool_get(self) -> None:
        """Called when object is retrieved from pool"""
        pass
    
    @abstractmethod
    def on_pool_return(self) -> None:
        """Called when object is returned to pool"""
        pass

class ObjectPool:
    """Generic object pool for performance optimization"""
    
    def __init__(self, object_type: Type, initial_size: int = 10, 
                 max_size: int = 100, factory_func: Optional[Callable] = None):
        self.object_type = object_type
        self.max_size = max_size
        self.factory_func = factory_func or self._default_factory
        
        # Pool storage
        self.available: List[Any] = []
        self.in_use: weakref.WeakSet = weakref.WeakSet()
        
        # Statistics
        self.total_created = 0
        self.total_reused = 0
        self.peak_usage = 0
        
        # Pre-populate pool
        for _ in range(initial_size):
            obj = self._create_object()
            self.available.append(obj)
    
    def _default_factory(self) -> Any:
        """Default factory function"""
        return self.object_type()
    
    def _create_object(self) -> Any:
        """Create new object"""
        obj = self.factory_func()
        self.total_created += 1
        return obj
    
    def get(self) -> Any:
        """Get object from pool"""
        if self.available:
            obj = self.available.pop()
            self.total_reused += 1
        else:
            obj = self._create_object()
        
        # Track usage
        self.in_use.add(obj)
        current_usage = len(self.in_use)
        if current_usage > self.peak_usage:
            self.peak_usage = current_usage
        
        # Initialize object
        if hasattr(obj, 'on_pool_get'):
            obj.on_pool_get()
        
        return obj
    
    def return_object(self, obj: Any) -> None:
        """Return object to pool"""
        if obj not in self.in_use:
            return  # Object not from this pool
        
        # Clean up object
        if hasattr(obj, 'on_pool_return'):
            obj.on_pool_return()
        
        if hasattr(obj, 'reset'):
            obj.reset()
        
        # Return to pool if not full
        if len(self.available) < self.max_size:
            self.available.append(obj)
        
        # Remove from in-use tracking
        self.in_use.discard(obj)
    
    def clear(self) -> None:
        """Clear the pool"""
        self.available.clear()
        self.in_use.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        return {
            'total_created': self.total_created,
            'total_reused': self.total_reused,
            'available': len(self.available),
            'in_use': len(self.in_use),
            'peak_usage': self.peak_usage,
            'reuse_rate': (self.total_reused / max(1, self.total_created + self.total_reused)) * 100
        }

class PoolManager:
    """Manages multiple object pools"""
    
    def __init__(self):
        self.pools: Dict[str, ObjectPool] = {}
    
    def create_pool(self, name: str, object_type: Type, initial_size: int = 10,
                   max_size: int = 100, factory_func: Optional[Callable] = None) -> ObjectPool:
        """Create a new pool"""
        pool = ObjectPool(object_type, initial_size, max_size, factory_func)
        self.pools[name] = pool
        return pool
    
    def get_pool(self, name: str) -> Optional[ObjectPool]:
        """Get pool by name"""
        return self.pools.get(name)
    
    def get_object(self, pool_name: str) -> Any:
        """Get object from named pool"""
        pool = self.pools.get(pool_name)
        if pool:
            return pool.get()
        return None
    
    def return_object(self, pool_name: str, obj: Any) -> None:
        """Return object to named pool"""
        pool = self.pools.get(pool_name)
        if pool:
            pool.return_object(obj)
    
    def clear_all(self) -> None:
        """Clear all pools"""
        for pool in self.pools.values():
            pool.clear()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all pools"""
        return {name: pool.get_stats() for name, pool in self.pools.items()}

# Global pool manager instance
_pool_manager = None

def get_pool_manager() -> PoolManager:
    """Get global pool manager instance"""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = PoolManager()
    return _pool_manager

# Convenience functions
def create_pool(name: str, object_type: Type, initial_size: int = 10,
               max_size: int = 100, factory_func: Optional[Callable] = None) -> ObjectPool:
    """Create a new pool using global manager"""
    return get_pool_manager().create_pool(name, object_type, initial_size, max_size, factory_func)

def get_pooled_object(pool_name: str) -> Any:
    """Get object from named pool"""
    return get_pool_manager().get_object(pool_name)

def return_pooled_object(pool_name: str, obj: Any) -> None:
    """Return object to named pool"""
    get_pool_manager().return_object(pool_name, obj)
