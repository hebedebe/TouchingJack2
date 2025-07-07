"""
Performance monitoring and debugging dashboard
"""
import pygame
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from engine.core.performance.memory_manager import get_memory_manager
from engine.core.performance.cache_manager import get_cache_manager
from engine.core.performance.sprite_cache import get_sprite_cache

@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring"""
    fps: float
    frame_time_ms: float
    memory_usage_mb: float
    cache_hit_rate: float
    draw_calls: int
    sprites_rendered: int
    timestamp: float

class PerformanceMonitor:
    """Real-time performance monitoring system"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.metrics_history: List[PerformanceMetrics] = []
        
        # Performance managers
        self.memory_manager = get_memory_manager()
        self.cache_manager = get_cache_manager()
        self.sprite_cache = get_sprite_cache()
        
        # Timing
        self.last_frame_time = time.time()
        self.frame_count = 0
        
        # Dashboard UI
        self.font = None
        self.show_dashboard = False
        self.dashboard_toggle_key = pygame.K_F1
        
    def initialize_ui(self):
        """Initialize UI components"""
        try:
            self.font = pygame.font.Font(None, 20)
        except:
            self.font = pygame.font.SysFont("Arial", 16)
    
    def update(self, clock: pygame.time.Clock, draw_calls: int = 0, sprites_rendered: int = 0):
        """Update performance metrics"""
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        self.frame_count += 1
        
        # Get performance data
        fps = clock.get_fps() if clock else 0.0
        memory_stats = self.memory_manager.get_performance_stats()
        cache_stats = self.sprite_cache.get_cache_stats()
        
        # Create metrics
        metrics = PerformanceMetrics(
            fps=fps,
            frame_time_ms=frame_time * 1000,
            memory_usage_mb=memory_stats['current_memory_mb'],
            cache_hit_rate=cache_stats['hit_rate'],
            draw_calls=draw_calls,
            sprites_rendered=sprites_rendered,
            timestamp=current_time
        )
        
        # Store in history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle dashboard toggle events"""
        if event.type == pygame.KEYDOWN:
            if event.key == self.dashboard_toggle_key:
                self.show_dashboard = not self.show_dashboard
                return True
        return False
    
    def render_dashboard(self, screen: pygame.Surface):
        """Render performance dashboard overlay"""
        if not self.show_dashboard or not self.font:
            return
        
        # Get latest metrics
        if not self.metrics_history:
            return
        
        latest = self.metrics_history[-1]
        
        # Dashboard background
        dashboard_rect = pygame.Rect(10, 10, 300, 200)
        dashboard_surface = pygame.Surface((dashboard_rect.width, dashboard_rect.height))
        dashboard_surface.set_alpha(200)
        dashboard_surface.fill((0, 0, 0))
        screen.blit(dashboard_surface, dashboard_rect)
        
        # Performance text
        y_offset = 20
        line_height = 22
        
        perf_lines = [
            f"=== PERFORMANCE MONITOR ===",
            f"FPS: {latest.fps:.1f}",
            f"Frame Time: {latest.frame_time_ms:.2f}ms",
            f"Memory: {latest.memory_usage_mb:.1f}MB",
            f"Cache Hit Rate: {latest.cache_hit_rate:.1f}%",
            f"Draw Calls: {latest.draw_calls}",
            f"Sprites: {latest.sprites_rendered}",
            f"Frame #{self.frame_count}",
            f"Press F1 to toggle"
        ]
        
        for i, line in enumerate(perf_lines):
            color = (255, 255, 255)
            if "FPS:" in line and latest.fps < 30:
                color = (255, 100, 100)  # Red for low FPS
            elif "Memory:" in line and latest.memory_usage_mb > 200:
                color = (255, 200, 100)  # Orange for high memory
            
            text_surface = self.font.render(line, True, color)
            screen.blit(text_surface, (20, y_offset + i * line_height))
    
    def get_average_fps(self, seconds: float = 1.0) -> float:
        """Get average FPS over the last N seconds"""
        if not self.metrics_history:
            return 0.0
        
        current_time = time.time()
        cutoff_time = current_time - seconds
        
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        if not recent_metrics:
            return 0.0
        
        return sum(m.fps for m in recent_metrics) / len(recent_metrics)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.metrics_history:
            return {}
        
        latest = self.metrics_history[-1]
        avg_fps = self.get_average_fps(5.0)
        
        memory_stats = self.memory_manager.get_performance_stats()
        cache_stats = self.sprite_cache.get_cache_stats()
        all_cache_stats = self.cache_manager.get_all_stats()
        
        return {
            'current_metrics': {
                'fps': latest.fps,
                'avg_fps_5s': avg_fps,
                'frame_time_ms': latest.frame_time_ms,
                'memory_mb': latest.memory_usage_mb,
                'cache_hit_rate': latest.cache_hit_rate
            },
            'memory_info': memory_stats,
            'sprite_cache': cache_stats,
            'all_caches': all_cache_stats,
            'frame_count': self.frame_count,
            'uptime_seconds': time.time() - (self.metrics_history[0].timestamp if self.metrics_history else time.time())
        }
    
    def log_performance_warning(self, message: str):
        """Log performance warnings"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] PERFORMANCE WARNING: {message}")
    
    def check_performance_health(self):
        """Check for performance issues and log warnings"""
        if not self.metrics_history:
            return
        
        latest = self.metrics_history[-1]
        
        # Check FPS
        if latest.fps < 30 and latest.fps > 0:
            self.log_performance_warning(f"Low FPS: {latest.fps:.1f}")
        
        # Check memory usage
        if latest.memory_usage_mb > 300:
            self.log_performance_warning(f"High memory usage: {latest.memory_usage_mb:.1f}MB")
        
        # Check cache hit rate
        if latest.cache_hit_rate < 80 and self.frame_count > 100:
            self.log_performance_warning(f"Low cache hit rate: {latest.cache_hit_rate:.1f}%")

# Global performance monitor
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
