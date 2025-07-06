import pygame
from typing import Callable, Optional, Tuple

from engine.core.game import Game
from engine.core.world.component import Component

class ClickableComponent(Component):
    """
    ClickableComponent enables mouse interaction for actors.
    Supports click, hover, and drag events with customizable bounds.
    """
    
    # Exclude callback functions from serialization
    __serialization_exclude__ = ["on_click", "on_hover_start", "on_hover_end", "on_drag_start", "on_drag", "on_drag_end"]
    
    def __init__(self, 
                 bounds_width: float = None, 
                 bounds_height: float = None,
                 bounds_offset: Tuple[float, float] = (0, 0)):
        super().__init__()
        
        # Clickable area configuration
        self.bounds_width = bounds_width  # If None, will try to get from sprite
        self.bounds_height = bounds_height  # If None, will try to get from sprite
        self.bounds_offset = pygame.Vector2(bounds_offset)  # Offset from actor position
        
        # Mouse interaction state
        self.is_hovered = False
        self.is_clicked = False
        self.is_dragging = False
        self.drag_start_pos = None
        self.last_mouse_pos = pygame.Vector2(0, 0)
        
        # Event callbacks
        self.on_click: Optional[Callable] = None
        self.on_hover_start: Optional[Callable] = None
        self.on_hover_end: Optional[Callable] = None
        self.on_drag_start: Optional[Callable] = None
        self.on_drag: Optional[Callable] = None  # Called with (delta_x, delta_y)
        self.on_drag_end: Optional[Callable] = None
        
        # Configuration
        self.enabled = True
        self.consume_events = False  # Whether to prevent event propagation
        self.drag_threshold = 5  # Minimum pixels to move before starting drag
        
    def set_bounds(self, width: float, height: float, offset: Tuple[float, float] = (0, 0)) -> None:
        """Set the clickable bounds."""
        self.bounds_width = width
        self.bounds_height = height
        self.bounds_offset = pygame.Vector2(offset)
        
    def set_click_callback(self, callback: Callable) -> None:
        """Set the callback function for click events."""
        self.on_click = callback
        
    def set_hover_callbacks(self, on_start: Callable = None, on_end: Callable = None) -> None:
        """Set the callback functions for hover events."""
        if on_start:
            self.on_hover_start = on_start
        if on_end:
            self.on_hover_end = on_end
            
    def set_drag_callbacks(self, on_start: Callable = None, on_drag: Callable = None, on_end: Callable = None) -> None:
        """Set the callback functions for drag events."""
        if on_start:
            self.on_drag_start = on_start
        if on_drag:
            self.on_drag = on_drag
        if on_end:
            self.on_drag_end = on_end
    
    def get_bounds_rect(self) -> pygame.Rect:
        """Get the clickable bounds as a pygame Rect."""
        if not self.actor:
            return pygame.Rect(0, 0, 0, 0)
            
        # Try to get bounds from explicit size or sprite component
        width = self.bounds_width
        height = self.bounds_height
        
        if width is None or height is None:
            # Try to get dimensions from sprite component
            sprite_comp = self.actor.getComponent("SpriteComponent")
            if sprite_comp and sprite_comp.sprite_name:
                from engine.core.asset_manager import AssetManager
                try:
                    surface = AssetManager().getSprite(sprite_comp.sprite_name)
                    if surface:
                        if width is None:
                            width = surface.get_width() * self.actor.transform.scale.x
                        if height is None:
                            height = surface.get_height() * self.actor.transform.scale.y
                except:
                    pass
                    
        # Default to small bounds if nothing else is available
        if width is None:
            width = 32
        if height is None:
            height = 32
            
        # Calculate position with offset
        pos = self.actor.screenPosition + self.bounds_offset
        
        # Center the bounds on the actor position
        rect = pygame.Rect(
            pos.x - width / 2,
            pos.y - height / 2,
            width,
            height
        )
        
        return rect
    
    def contains_point(self, point: Tuple[float, float]) -> bool:
        """Check if a point is within the clickable bounds."""
        if not self.enabled:
            return False
            
        rect = self.get_bounds_rect()
        return rect.collidepoint(point)
    
    def handle_event(self, event) -> bool:
        """Handle mouse events for clicking and hovering."""
        if not self.enabled:
            return False
            
        handled = False
        
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.Vector2(event.pos)
            self.last_mouse_pos = mouse_pos
            
            # Check hover state
            is_over = self.contains_point(event.pos)
            
            if is_over and not self.is_hovered:
                # Started hovering
                self.is_hovered = True
                if self.on_hover_start:
                    self.on_hover_start()
                handled = self.consume_events
                
            elif not is_over and self.is_hovered:
                # Stopped hovering
                self.is_hovered = False
                if self.on_hover_end:
                    self.on_hover_end()
                handled = self.consume_events
                
            # Handle dragging
            if self.is_dragging and self.on_drag:
                if self.drag_start_pos:
                    delta = mouse_pos - self.drag_start_pos
                    self.on_drag(delta.x, delta.y)
                    handled = self.consume_events
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.contains_point(event.pos):
                if event.button == 1:  # Left mouse button
                    self.is_clicked = True
                    self.drag_start_pos = pygame.Vector2(event.pos)
                    handled = self.consume_events
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button
                if self.is_clicked:
                    # Check if it's a click (not a drag)
                    if self.contains_point(event.pos):
                        if not self.is_dragging:
                            # Simple click
                            if self.on_click:
                                self.on_click()
                            handled = self.consume_events
                        else:
                            # End drag
                            if self.on_drag_end:
                                self.on_drag_end()
                            handled = self.consume_events
                            
                    # Reset states
                    self.is_clicked = False
                    self.is_dragging = False
                    self.drag_start_pos = None
                    
        return handled
    
    def update(self, delta_time):
        """Update the clickable component."""
        if not self.enabled:
            return
            
        # Check if we should start dragging
        if (self.is_clicked and not self.is_dragging and 
            self.drag_start_pos and self.drag_threshold > 0):
            
            current_distance = self.last_mouse_pos.distance_to(self.drag_start_pos)
            if current_distance >= self.drag_threshold:
                self.is_dragging = True
                if self.on_drag_start:
                    self.on_drag_start()
    
    # def render(self):
    #     """Debug method to visualize the clickable bounds."""
    #     if not self.enabled or not self.actor:
    #         return
        
    #     screen = Game().buffer
            
    #     rect = self.get_bounds_rect()
    #     color = (0, 255, 0) if self.is_hovered else (255, 0, 0)
    #     if self.is_clicked:
    #         color = (0, 0, 255)
            
    #     pygame.draw.rect(screen, color, rect, 2)