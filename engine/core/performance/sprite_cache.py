"""
High-performance sprite caching system to avoid expensive pygame transformations
"""
import pygame
import hashlib
from typing import Dict, Tuple, Optional, Any
from collections import OrderedDict
import weakref
import psutil
import gc

class LRUCache:
    """Simple LRU cache implementation"""
    def __init__(self, maxsize: int):
        self.cache = OrderedDict()
        self.maxsize = maxsize
    
    def get(self, key):
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def __setitem__(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.maxsize:
            self.cache.popitem(last=False)  # Remove least recently used
        self.cache[key] = value
    
    def __len__(self):
        return len(self.cache)
    
    def clear(self):
        self.cache.clear()
    
    def popitem(self):
        return self.cache.popitem(last=False)

class SpriteCache:
    """Advanced sprite caching system with memory management"""
    
    def __init__(self, max_memory_mb: int = 512):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.current_memory_usage = 0
        
        # LRU cache for transformed sprites
        self.transform_cache: LRUCache = LRUCache(2048)
        
        # Cache for original surfaces by name
        self.surface_cache: Dict[str, pygame.Surface] = {}
        
        # Cache for text surfaces
        self.text_cache: LRUCache = LRUCache(512)
        
        # Weak references for cleanup
        self.surface_refs = weakref.WeakSet()
        
        # Performance metrics
        self.cache_hits = 0
        self.cache_misses = 0
        
    def _generate_transform_key(self, sprite_name: str, scale: Tuple[float, float], 
                                rotation: float, tint: Tuple[int, int, int, int],
                                opacity: int) -> str:
        """Generate a unique key for transformed sprite"""
        key_data = f"{sprite_name}_{scale[0]:.3f}_{scale[1]:.3f}_{rotation:.1f}_{tint}_{opacity}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_surface(self, sprite_name: str) -> Optional[pygame.Surface]:
        """Get original surface by name"""
        return self.surface_cache.get(sprite_name)
    
    def cache_surface(self, sprite_name: str, surface: pygame.Surface) -> None:
        """Cache original surface"""
        if sprite_name not in self.surface_cache:
            self.surface_cache[sprite_name] = surface.copy()
            self.surface_refs.add(self.surface_cache[sprite_name])
            self.current_memory_usage += surface.get_width() * surface.get_height() * 4
    
    def get_transformed_sprite(self, sprite_name: str, scale: Tuple[float, float] = (1.0, 1.0),
                              rotation: float = 0.0, tint: Tuple[int, int, int, int] = (255, 255, 255, 255),
                              opacity: int = 255) -> Optional[pygame.Surface]:
        """Get cached transformed sprite or create and cache it"""
        
        # Generate cache key
        cache_key = self._generate_transform_key(sprite_name, scale, rotation, tint, opacity)
        
        # Try to get from cache
        cached_surface = self.transform_cache.get(cache_key)
        if cached_surface is not None:
            self.cache_hits += 1
            return cached_surface
        
        # Cache miss - create transformed sprite
        self.cache_misses += 1
        
        original_surface = self.get_surface(sprite_name)
        if original_surface is None:
            return None
        
        # Apply transformations
        transformed = self._apply_transformations(original_surface.copy(), scale, rotation, tint, opacity)
        
        # Cache the result
        self.transform_cache[cache_key] = transformed
        self.surface_refs.add(transformed)
        
        # Update memory usage
        surface_size = transformed.get_width() * transformed.get_height() * 4
        self.current_memory_usage += surface_size
        
        # Check memory limits
        self._check_memory_usage()
        
        return transformed
    
    def _apply_transformations(self, surface: pygame.Surface, scale: Tuple[float, float],
                              rotation: float, tint: Tuple[int, int, int, int],
                              opacity: int) -> pygame.Surface:
        """Apply all transformations to surface"""
        
        # Apply tint
        if tint != (255, 255, 255, 255):
            surface.fill(tint[:3], special_flags=pygame.BLEND_MULT)
        
        # Apply opacity
        if opacity != 255:
            surface.set_alpha(opacity)
        
        # Apply scaling (only if needed)
        if scale != (1.0, 1.0):
            new_size = (
                max(1, int(surface.get_width() * scale[0])),
                max(1, int(surface.get_height() * scale[1]))
            )
            surface = pygame.transform.scale(surface, new_size)
        
        # Apply rotation (only if needed)
        if rotation != 0.0:
            surface = pygame.transform.rotate(surface, rotation)
        
        return surface
    
    def cache_text(self, text: str, font_name: str, size: int, color: Tuple[int, int, int],
                   antialiasing: bool = True) -> pygame.Surface:
        """Cache rendered text surfaces"""
        
        text_key = f"{text}_{font_name}_{size}_{color}_{antialiasing}"
        cached_text = self.text_cache.get(text_key)
        
        if cached_text is not None:
            self.cache_hits += 1
            return cached_text
        
        self.cache_misses += 1
        
        # Create text surface (assuming font is loaded elsewhere)
        font = pygame.font.Font(None, size)  # This should be optimized with font caching
        text_surface = font.render(text, antialiasing, color)
        
        self.text_cache[text_key] = text_surface
        self.surface_refs.add(text_surface)
        
        return text_surface
    
    def _check_memory_usage(self) -> None:
        """Check and manage memory usage"""
        if self.current_memory_usage > self.max_memory_bytes:
            self._cleanup_cache()
    
    def _cleanup_cache(self) -> None:
        """Clean up cache to free memory"""
        # Force garbage collection
        gc.collect()
        
        # Clear some LRU entries
        entries_to_remove = len(self.transform_cache) // 4
        for _ in range(entries_to_remove):
            if len(self.transform_cache) > 0:
                self.transform_cache.popitem()
        
        # Update memory usage estimate
        self.current_memory_usage = int(self.current_memory_usage * 0.75)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': hit_rate,
            'memory_usage_mb': self.current_memory_usage / (1024 * 1024),
            'transform_cache_size': len(self.transform_cache),
            'text_cache_size': len(self.text_cache),
            'surface_cache_size': len(self.surface_cache)
        }
    
    def clear_cache(self) -> None:
        """Clear all caches"""
        self.transform_cache.clear()
        self.text_cache.clear()
        self.current_memory_usage = 0
        gc.collect()

# Global instance
_sprite_cache = None

def get_sprite_cache() -> SpriteCache:
    """Get global sprite cache instance"""
    global _sprite_cache
    if _sprite_cache is None:
        _sprite_cache = SpriteCache()
    return _sprite_cache
