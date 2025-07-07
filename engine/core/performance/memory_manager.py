"""
Memory management and monitoring system
"""
import gc
import psutil
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import weakref
import threading

@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_memory_mb: float
    used_memory_mb: float
    available_memory_mb: float
    percent_used: float
    gc_collections: Dict[int, int] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class MemoryManager:
    """Advanced memory management system"""
    
    def __init__(self, gc_threshold_mb: int = 100, auto_cleanup: bool = True):
        self.gc_threshold_bytes = gc_threshold_mb * 1024 * 1024
        self.auto_cleanup = auto_cleanup
        
        # Memory tracking
        self.tracked_objects: weakref.WeakSet = weakref.WeakSet()
        self.memory_history: List[MemoryStats] = []
        self.max_history_size = 100
        
        # GC settings optimization
        self._optimize_gc_settings()
        
        # Auto cleanup thread
        self.cleanup_thread: Optional[threading.Thread] = None
        self.cleanup_running = False
        
        if auto_cleanup:
            self.start_auto_cleanup()
        
        # Performance counters
        self.cleanup_count = 0
        self.bytes_freed = 0
        
    def _optimize_gc_settings(self) -> None:
        """Optimize garbage collection settings for better performance"""
        # Increase GC thresholds to reduce frequency of collections
        gc.set_threshold(1000, 20, 20)  # Default is (700, 10, 10)
        
        # Enable debug flags for monitoring if needed
        # gc.set_debug(gc.DEBUG_STATS)
    
    def track_object(self, obj: Any) -> None:
        """Track an object for memory management"""
        self.tracked_objects.add(obj)
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()
        virtual_memory = psutil.virtual_memory()
        
        # Get GC statistics
        gc_stats = {}
        for i in range(3):
            gc_stats[i] = gc.get_count()[i]
        
        stats = MemoryStats(
            total_memory_mb=virtual_memory.total / (1024 * 1024),
            used_memory_mb=memory_info.rss / (1024 * 1024),
            available_memory_mb=virtual_memory.available / (1024 * 1024),
            percent_used=virtual_memory.percent,
            gc_collections=gc_stats
        )
        
        # Store in history
        self.memory_history.append(stats)
        if len(self.memory_history) > self.max_history_size:
            self.memory_history.pop(0)
        
        return stats
    
    def should_cleanup(self) -> bool:
        """Check if memory cleanup is needed"""
        stats = self.get_memory_stats()
        return (stats.used_memory_mb * 1024 * 1024) > self.gc_threshold_bytes
    
    def cleanup_memory(self, force: bool = False) -> int:
        """Perform memory cleanup and return bytes freed"""
        if not force and not self.should_cleanup():
            return 0
        
        # Get memory before cleanup
        before_stats = self.get_memory_stats()
        
        # Clear weak references to deleted objects
        tracked_count_before = len(self.tracked_objects)
        
        # Force garbage collection
        collected_objects = 0
        for generation in range(3):
            collected_objects += gc.collect(generation)
        
        # Get memory after cleanup
        after_stats = self.get_memory_stats()
        bytes_freed = (before_stats.used_memory_mb - after_stats.used_memory_mb) * 1024 * 1024
        
        # Update counters
        self.cleanup_count += 1
        self.bytes_freed += max(0, bytes_freed)
        
        tracked_count_after = len(self.tracked_objects)
        print(f"Memory cleanup: {bytes_freed / (1024 * 1024):.2f} MB freed, "
              f"{collected_objects} objects collected, "
              f"{tracked_count_before - tracked_count_after} tracked objects cleaned")
        
        return int(bytes_freed)
    
    def start_auto_cleanup(self) -> None:
        """Start automatic memory cleanup thread"""
        if self.cleanup_running:
            return
        
        self.cleanup_running = True
        self.cleanup_thread = threading.Thread(target=self._auto_cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def stop_auto_cleanup(self) -> None:
        """Stop automatic memory cleanup"""
        self.cleanup_running = False
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=1.0)
    
    def _auto_cleanup_loop(self) -> None:
        """Auto cleanup loop"""
        while self.cleanup_running:
            try:
                if self.should_cleanup():
                    self.cleanup_memory()
                time.sleep(5.0)  # Check every 5 seconds
            except Exception as e:
                print(f"Error in auto cleanup: {e}")
                time.sleep(10.0)  # Wait longer on error
    
    def get_memory_usage_trend(self) -> str:
        """Get memory usage trend over time"""
        if len(self.memory_history) < 2:
            return "insufficient_data"
        
        recent = self.memory_history[-5:]  # Last 5 measurements
        if len(recent) < 2:
            return "insufficient_data"
        
        first_usage = recent[0].used_memory_mb
        last_usage = recent[-1].used_memory_mb
        
        change_mb = last_usage - first_usage
        change_percent = (change_mb / first_usage) * 100 if first_usage > 0 else 0
        
        if change_percent > 10:
            return "increasing_rapidly"
        elif change_percent > 2:
            return "increasing"
        elif change_percent < -10:
            return "decreasing_rapidly"
        elif change_percent < -2:
            return "decreasing"
        else:
            return "stable"
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get memory management performance statistics"""
        current_stats = self.get_memory_stats()
        trend = self.get_memory_usage_trend()
        
        return {
            'current_memory_mb': current_stats.used_memory_mb,
            'memory_percent': current_stats.percent_used,
            'available_memory_mb': current_stats.available_memory_mb,
            'cleanup_count': self.cleanup_count,
            'total_bytes_freed_mb': self.bytes_freed / (1024 * 1024),
            'tracked_objects': len(self.tracked_objects),
            'memory_trend': trend,
            'gc_collections': current_stats.gc_collections,
            'auto_cleanup_running': self.cleanup_running
        }
    
    def optimize_for_game(self) -> None:
        """Apply game-specific memory optimizations"""
        # Disable automatic garbage collection during gameplay
        gc.disable()
        
        # Perform manual cleanup
        self.cleanup_memory(force=True)
        
        # Re-enable with optimized settings
        gc.enable()
        
        print("Applied game-specific memory optimizations")
    
    def __del__(self):
        """Cleanup when manager is destroyed"""
        self.stop_auto_cleanup()

# Global memory manager instance
_memory_manager = None

def get_memory_manager() -> MemoryManager:
    """Get global memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager

# Convenience functions
def cleanup_memory(force: bool = False) -> int:
    """Cleanup memory using global manager"""
    return get_memory_manager().cleanup_memory(force)

def get_memory_stats() -> MemoryStats:
    """Get memory stats using global manager"""
    return get_memory_manager().get_memory_stats()

def track_object(obj: Any) -> None:
    """Track object using global manager"""
    get_memory_manager().track_object(obj)
