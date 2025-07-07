"""
Universal cache management system
"""
import time
import threading
from typing import Any, Dict, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import weakref
import hashlib

T = TypeVar('T')

class CachePolicy(Enum):
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"

@dataclass
class CacheEntry:
    """Single cache entry with metadata"""
    value: Any
    access_count: int = 0
    last_accessed: float = 0.0
    created_at: float = 0.0
    ttl: Optional[float] = None
    
    def __post_init__(self):
        current_time = time.time()
        if self.last_accessed == 0.0:
            self.last_accessed = current_time
        if self.created_at == 0.0:
            self.created_at = current_time
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self) -> None:
        """Mark entry as accessed"""
        self.access_count += 1
        self.last_accessed = time.time()

class Cache(Generic[T]):
    """Generic cache implementation with multiple eviction policies"""
    
    def __init__(self, max_size: int = 1000, policy: CachePolicy = CachePolicy.LRU,
                 default_ttl: Optional[float] = None):
        self.max_size = max_size
        self.policy = policy
        self.default_ttl = default_ttl
        
        self._entries: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
    def get(self, key: str) -> Optional[T]:
        """Get value from cache"""
        with self._lock:
            entry = self._entries.get(key)
            
            if entry is None:
                self.misses += 1
                return None
            
            if entry.is_expired():
                del self._entries[key]
                self.misses += 1
                return None
            
            entry.touch()
            self.hits += 1
            return entry.value
    
    def put(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """Put value in cache"""
        with self._lock:
            # Use default TTL if not specified
            effective_ttl = ttl if ttl is not None else self.default_ttl
            
            # Create new entry
            entry = CacheEntry(value=value, ttl=effective_ttl)
            
            # Check if we need to evict
            if key not in self._entries and len(self._entries) >= self.max_size:
                self._evict()
            
            self._entries[key] = entry
    
    def remove(self, key: str) -> bool:
        """Remove entry from cache"""
        with self._lock:
            if key in self._entries:
                del self._entries[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries"""
        with self._lock:
            self._entries.clear()
    
    def _evict(self) -> None:
        """Evict entry based on policy"""
        if not self._entries:
            return
        
        key_to_evict = None
        
        if self.policy == CachePolicy.LRU:
            # Evict least recently used
            key_to_evict = min(self._entries.keys(), 
                             key=lambda k: self._entries[k].last_accessed)
        
        elif self.policy == CachePolicy.LFU:
            # Evict least frequently used
            key_to_evict = min(self._entries.keys(),
                             key=lambda k: self._entries[k].access_count)
        
        elif self.policy == CachePolicy.FIFO:
            # Evict oldest
            key_to_evict = min(self._entries.keys(),
                             key=lambda k: self._entries[k].created_at)
        
        elif self.policy == CachePolicy.TTL:
            # Evict expired entries first, then oldest
            expired_keys = [k for k, e in self._entries.items() if e.is_expired()]
            if expired_keys:
                key_to_evict = expired_keys[0]
            else:
                key_to_evict = min(self._entries.keys(),
                                 key=lambda k: self._entries[k].created_at)
        
        if key_to_evict:
            del self._entries[key_to_evict]
            self.evictions += 1
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        with self._lock:
            expired_keys = [k for k, e in self._entries.items() if e.is_expired()]
            for key in expired_keys:
                del self._entries[key]
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._entries),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'evictions': self.evictions,
                'hit_rate': hit_rate,
                'policy': self.policy.value
            }

class CacheManager:
    """Manages multiple named caches"""
    
    def __init__(self):
        self.caches: Dict[str, Cache] = {}
        self._lock = threading.RLock()
        
        # Auto-cleanup thread
        self.cleanup_thread: Optional[threading.Thread] = None
        self.cleanup_running = False
        self.start_auto_cleanup()
    
    def create_cache(self, name: str, max_size: int = 1000, 
                    policy: CachePolicy = CachePolicy.LRU,
                    default_ttl: Optional[float] = None) -> Cache:
        """Create a new cache"""
        with self._lock:
            cache = Cache(max_size, policy, default_ttl)
            self.caches[name] = cache
            return cache
    
    def get_cache(self, name: str) -> Optional[Cache]:
        """Get cache by name"""
        with self._lock:
            return self.caches.get(name)
    
    def remove_cache(self, name: str) -> bool:
        """Remove cache by name"""
        with self._lock:
            if name in self.caches:
                del self.caches[name]
                return True
            return False
    
    def clear_all(self) -> None:
        """Clear all caches"""
        with self._lock:
            for cache in self.caches.values():
                cache.clear()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches"""
        with self._lock:
            return {name: cache.get_stats() for name, cache in self.caches.items()}
    
    def cleanup_expired_all(self) -> Dict[str, int]:
        """Cleanup expired entries in all caches"""
        with self._lock:
            results = {}
            for name, cache in self.caches.items():
                expired_count = cache.cleanup_expired()
                results[name] = expired_count
            return results
    
    def start_auto_cleanup(self) -> None:
        """Start automatic cleanup thread"""
        if self.cleanup_running:
            return
        
        self.cleanup_running = True
        self.cleanup_thread = threading.Thread(target=self._auto_cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def stop_auto_cleanup(self) -> None:
        """Stop automatic cleanup"""
        self.cleanup_running = False
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=1.0)
    
    def _auto_cleanup_loop(self) -> None:
        """Auto cleanup loop"""
        while self.cleanup_running:
            try:
                self.cleanup_expired_all()
                time.sleep(30.0)  # Cleanup every 30 seconds
            except Exception as e:
                print(f"Error in cache auto cleanup: {e}")
                time.sleep(60.0)  # Wait longer on error
    
    def __del__(self):
        """Cleanup when manager is destroyed"""
        self.stop_auto_cleanup()

# Decorators for easy caching
def cached(cache_name: str, ttl: Optional[float] = None, 
          key_func: Optional[Callable] = None):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_data = f"{func.__name__}_{args}_{sorted(kwargs.items())}"
                cache_key = hashlib.md5(str(key_data).encode()).hexdigest()
            
            # Get cache
            cache = get_cache_manager().get_cache(cache_name)
            if cache is None:
                # Create cache if it doesn't exist
                cache = get_cache_manager().create_cache(cache_name, default_ttl=ttl)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Compute and cache result
            result = func(*args, **kwargs)
            cache.put(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
