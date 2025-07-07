import pygame
import hashlib
from engine.core.ui import UIElement
from engine.core.performance.sprite_cache import get_sprite_cache

class Label(UIElement):
    """Optimized label with text surface caching"""
    
    def __init__(self, position, width, text, font=None, font_size=24, color=(255, 255, 255)):
        super().__init__(position, width, 0)
        self.text = text
        self.font = pygame.font.Font(font, font_size) if font else pygame.font.Font(None, font_size)
        self.color = color
        self.font_size = font_size
        
        # Caching
        self._sprite_cache = get_sprite_cache()
        self._cached_text_surface = None
        self._cached_text_key = None
        self._text_dirty = True

    def render(self, screen):
        if not self.visible:
            return
            
        # Generate cache key for current text state
        text_key = self._generate_text_key()
        
        # Check if we need to re-render text
        if self._text_dirty or self._cached_text_key != text_key:
            self._render_text_to_cache()
            self._cached_text_key = text_key
            self._text_dirty = False
        
        # Render cached text surface
        if self._cached_text_surface:
            screen.blit(self._cached_text_surface, (self.rect.x, self.rect.y))

    def _generate_text_key(self) -> str:
        """Generate unique key for current text state"""
        key_data = f"{self.text}_{self.font_size}_{self.color}_{self.rect.width}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _render_text_to_cache(self):
        """Render text to cached surface with word wrapping"""
        if not self.text:
            self._cached_text_surface = None
            return
            
        # Try to get from sprite cache first
        cached_surface = self._sprite_cache.cache_text(
            self.text, 
            "default",  # font name - could be improved
            self.font_size,
            self.color
        )
        
        if cached_surface and cached_surface.get_width() <= self.rect.width:
            self._cached_text_surface = cached_surface
            return
        
        # Render with word wrapping if not in cache or too wide
        words = self.text.split(' ')
        lines = []
        current_line = ''
        
        for word in words:
            test_line = current_line + word + ' '
            test_surface = self.font.render(test_line.strip(), True, self.color)
            
            if test_surface.get_width() > self.rect.width and current_line:
                lines.append(current_line.strip())
                current_line = word + ' '
            else:
                current_line = test_line
        
        if current_line:
            lines.append(current_line.strip())

        # Calculate total height
        line_height = self.font.get_height()
        total_height = len(lines) * line_height
        
        if not lines:
            self._cached_text_surface = None
            return
        
        # Create surface for all lines
        max_width = max(self.font.render(line, True, self.color).get_width() for line in lines)
        text_surface = pygame.Surface((max_width, total_height), pygame.SRCALPHA)
        
        # Render each line
        y_offset = 0
        for line in lines:
            line_surface = self.font.render(line, True, self.color)
            text_surface.blit(line_surface, (0, y_offset))
            y_offset += line_height
        
        self._cached_text_surface = text_surface

    def set_text(self, text):
        """Set text and mark for re-rendering"""
        if self.text != text:
            self.text = text
            self._text_dirty = True
    
    def set_color(self, color):
        """Set color and mark for re-rendering"""
        if self.color != color:
            self.color = color
            self._text_dirty = True
