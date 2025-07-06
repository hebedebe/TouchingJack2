import pygame
from typing import Optional, Tuple

from engine.core.world.component import Component

class TextComponent(Component):
    """
    Component for rendering text using asset references.
    Stores font names rather than font objects directly for better memory management.
    """
    
    # Exclude cached objects from serialization
    __serialization_exclude__ = ["_rendered_surface", "_font_object", "_cache_dirty"]
    
    def __init__(self, text: str = "", font_name: str = None, font_size: int = 24):
        super().__init__()
        
        # Text content
        self.text: str = text
        
        # Font properties
        self.font_name: Optional[str] = font_name
        self.font_size: int = font_size
        
        # Visual properties
        self.color: pygame.Color = pygame.Color(255, 255, 255)  # White by default
        self.background_color: Optional[pygame.Color] = None  # Transparent by default
        self.antialias: bool = True
        self.visible: bool = True
        
        # Text alignment relative to actor position
        self.align_x: str = 'center'  # 'left', 'center', 'right'
        self.align_y: str = 'center'  # 'top', 'center', 'bottom'
        
        # Transform modifiers (relative to actor's transform)
        self.offset: pygame.Vector2 = pygame.Vector2(0, 0)
        self.rotation_offset: float = 0.0
        
        # Multi-line text support
        self.word_wrap: bool = False
        self.max_width: Optional[int] = None
        self.line_spacing: int = 0  # Additional spacing between lines
        
        # Cached rendered surface and font object
        self._rendered_surface: Optional[pygame.Surface] = None
        self._font_object: Optional[pygame.font.Font] = None
        self._cache_dirty: bool = True
        self._last_text: str = ""
        self._last_color: pygame.Color = pygame.Color(0, 0, 0)
        
    def set_text(self, text: str) -> None:
        """Set the text content."""
        if self.text != text:
            self.text = text
            self._invalidate_cache()
            
    def set_font(self, font_name: str, font_size: int = None) -> None:
        """Set the font name and optionally size."""
        changed = False
        if self.font_name != font_name:
            self.font_name = font_name
            changed = True
        if font_size is not None and self.font_size != font_size:
            self.font_size = font_size
            changed = True
        if changed:
            self._font_object = None  # Reset cached font
            self._invalidate_cache()
            
    def set_color(self, color: pygame.Color) -> None:
        """Set the text color."""
        if self.color != color:
            self.color = color
            self._invalidate_cache()
            
    def set_background_color(self, color: Optional[pygame.Color]) -> None:
        """Set the background color (None for transparent)."""
        if self.background_color != color:
            self.background_color = color
            self._invalidate_cache()
            
    def set_alignment(self, align_x: str = 'center', align_y: str = 'center') -> None:
        """Set text alignment."""
        if self.align_x != align_x or self.align_y != align_y:
            self.align_x = align_x
            self.align_y = align_y
            # Alignment doesn't affect the rendered surface, only positioning
            
    def _invalidate_cache(self) -> None:
        """Mark the cached surface as dirty."""
        self._cache_dirty = True
        self._rendered_surface = None
        
    def _get_asset_manager(self):
        """Get the asset manager from the game instance."""
        from engine import Game
        game = Game()
        return game.assetManager
        
    def _get_font_object(self) -> pygame.font.Font:
        """Get the font object from the asset manager."""
        # Return cached font if available
        if self._font_object:
            return self._font_object
            
        asset_manager = self._get_asset_manager()
        
        if self.font_name:
            # Try to get/load the specified font
            font = asset_manager.getFont(self.font_name, self.font_size)
            if not font:
                font = asset_manager.loadFont(self.font_name, self.font_size)
            
            if font:
                self._font_object = font
                return self._font_object
        
        # Fall back to default font
        self._font_object = asset_manager.getDefaultFont(self.font_size)
        return self._font_object
        
    def _render_text_lines(self, lines: list) -> pygame.Surface:
        """Render multiple lines of text to a surface."""
        font = self._get_font_object()
        
        if not lines:
            # Create a minimal surface for empty text
            surface = pygame.Surface((1, font.get_height()), pygame.SRCALPHA)
            return surface
            
        # Calculate total dimensions
        line_heights = []
        line_surfaces = []
        max_width = 0
        
        for line in lines:
            if line.strip():  # Non-empty line
                line_surface = font.render(line, self.antialias, self.color, self.background_color)
            else:  # Empty line
                line_surface = pygame.Surface((1, font.get_height()), pygame.SRCALPHA)
            
            line_surfaces.append(line_surface)
            line_heights.append(line_surface.get_height())
            max_width = max(max_width, line_surface.get_width())
            
        # Calculate total height with line spacing
        total_height = sum(line_heights) + self.line_spacing * (len(lines) - 1)
        
        # Create the final surface
        final_surface = pygame.Surface((max_width, total_height), pygame.SRCALPHA)
        
        # Blit each line
        y_offset = 0
        for line_surface, line_height in zip(line_surfaces, line_heights):
            final_surface.blit(line_surface, (0, y_offset))
            y_offset += line_height + self.line_spacing
            
        return final_surface
        
    def _wrap_text(self, text: str) -> list:
        """Wrap text to fit within max_width."""
        if not self.word_wrap or not self.max_width:
            return text.split('\n')
            
        font = self._get_font_object()
        lines = []
        
        for paragraph in text.split('\n'):
            if not paragraph.strip():
                lines.append('')
                continue
                
            words = paragraph.split(' ')
            current_line = ''
            
            for word in words:
                test_line = current_line + (' ' if current_line else '') + word
                test_width = font.size(test_line)[0]
                
                if test_width <= self.max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                        current_line = word
                    else:
                        # Single word is too wide, add it anyway
                        lines.append(word)
                        current_line = ''
                        
            if current_line:
                lines.append(current_line)
                
        return lines
        
    def _get_rendered_surface(self) -> Optional[pygame.Surface]:
        """Get the rendered text surface with caching."""
        if not self.text:
            return None
            
        # Check if we need to rebuild the cache
        if (not self._cache_dirty and self._rendered_surface and 
            self._last_text == self.text and self._last_color == self.color):
            return self._rendered_surface
            
        # Wrap text if needed
        lines = self._wrap_text(self.text)
        
        # Render the text
        self._rendered_surface = self._render_text_lines(lines)
        
        # Update cache state
        self._cache_dirty = False
        self._last_text = self.text
        self._last_color = pygame.Color(self.color.r, self.color.g, self.color.b, self.color.a)
        
        return self._rendered_surface
        
    def get_text_rect(self) -> Optional[pygame.Rect]:
        """Get the rectangle of the text in world coordinates."""
        surface = self._get_rendered_surface()
        if not surface or not self.actor:
            return None
            
        # Calculate final position with offset and alignment
        final_pos = self.actor.transform.position + self.offset
        
        # Create rect and apply alignment
        rect = surface.get_rect()
        
        # Apply horizontal alignment
        if self.align_x == 'left':
            rect.left = int(final_pos.x)
        elif self.align_x == 'right':
            rect.right = int(final_pos.x)
        else:  # center
            rect.centerx = int(final_pos.x)
            
        # Apply vertical alignment
        if self.align_y == 'top':
            rect.top = int(final_pos.y)
        elif self.align_y == 'bottom':
            rect.bottom = int(final_pos.y)
        else:  # center
            rect.centery = int(final_pos.y)
            
        return rect
        
    def render(self, surface: pygame.Surface) -> None:
        """Render the text component."""
        if not self.visible or not self.text or not self.actor:
            return
            
        # Get the rendered text surface
        text_surface = self._get_rendered_surface()
        if not text_surface:
            return
            
        # Calculate final position with offset
        final_pos = self.actor.screenPosition + self.offset
        
        # Apply rotation if needed
        final_rotation = self.actor.transform.rotation + self.rotation_offset
        if final_rotation != 0:
            text_surface = pygame.transform.rotate(text_surface, -final_rotation)
            
        # Create rect and apply alignment
        render_rect = text_surface.get_rect()
        
        # Apply horizontal alignment
        if self.align_x == 'left':
            render_rect.left = int(final_pos.x)
        elif self.align_x == 'right':
            render_rect.right = int(final_pos.x)
        else:  # center
            render_rect.centerx = int(final_pos.x)
            
        # Apply vertical alignment
        if self.align_y == 'top':
            render_rect.top = int(final_pos.y)
        elif self.align_y == 'bottom':
            render_rect.bottom = int(final_pos.y)
        else:  # center
            render_rect.centery = int(final_pos.y)
            
        # Render to the target surface
        surface.blit(text_surface, render_rect)
        
    def start(self) -> None:
        """Initialize the text component when attached to an actor."""
        super().start()
        
        # Preload the font if specified
        if self.font_name:
            self._get_font_object()
            
    def serialize(self) -> dict:
        """Serialize the text component data."""
        data = super().serialize()
        
        # Convert pygame.Color to tuple for serialization
        data['color'] = (self.color.r, self.color.g, self.color.b, self.color.a)
        if self.background_color:
            data['background_color'] = (self.background_color.r, self.background_color.g, 
                                       self.background_color.b, self.background_color.a)
        
        return data
        
    def deserialize(self, data: dict):
        """Deserialize the text component data."""
        super().deserialize(data)
        
        # Convert color tuples back to pygame.Color
        if 'color' in data and data['color']:
            self.color = pygame.Color(*data['color'])
        if 'background_color' in data and data['background_color']:
            self.background_color = pygame.Color(*data['background_color'])
            
        # Invalidate cache after deserialization
        self._invalidate_cache()
        
        return self