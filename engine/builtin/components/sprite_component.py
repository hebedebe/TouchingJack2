import pygame
from typing import Optional, Tuple

from ...core.world.component import Component
from ...core.asset_manager import AssetManager
from ...core.game import Game
from ...core.performance.sprite_cache import get_sprite_cache
from ...core.performance.fast_math import FastMath

class SpriteComponent(Component):
    """
    Optimized component for rendering sprites with advanced caching and performance features.
    """
    
    # Exclude cache-related fields from serialization
    __serialization_exclude__ = ["_cached_surface", "_cache_dirty", "_last_transform_key"]
    
    def __init__(self, sprite_name: str = None, tint_color: pygame.Color = None):
        super().__init__()
        
        # Asset reference
        self.sprite_name: Optional[str] = sprite_name
        
        # Visual properties - normalize tint_color to pygame.Color
        if tint_color is None:
            self.tint_color = pygame.Color(255, 255, 255, 255)
        elif isinstance(tint_color, pygame.Color):
            self.tint_color = tint_color
        elif isinstance(tint_color, (tuple, list)):
            if len(tint_color) == 3:
                self.tint_color = pygame.Color(*tint_color, 255)
            elif len(tint_color) >= 4:
                self.tint_color = pygame.Color(*tint_color[:4])
            else:
                self.tint_color = pygame.Color(255, 255, 255, 255)
        else:
            self.tint_color = pygame.Color(255, 255, 255, 255)
        self.alpha: int = 255  # 0-255 transparency
        self.visible: bool = True
        
        # Transform modifiers (relative to actor's transform)
        self.offset: pygame.Vector2 = pygame.Vector2(0, 0)
        self.scale_modifier: pygame.Vector2 = pygame.Vector2(1, 1)
        self.rotation_offset: float = 0.0
        
        # Rendering options
        self.flip_horizontal: bool = False
        self.flip_vertical: bool = False
        
        # Performance optimizations
        self._cached_surface: Optional[pygame.Surface] = None
        self._cache_dirty: bool = True
        self._last_transform_key: Optional[str] = None
        self._sprite_cache = get_sprite_cache()
        
        # Fast math for calculations
        self._fast_math = FastMath()
        
    def set_sprite(self, sprite_name: str) -> None:
        """Set the sprite asset name with cache invalidation."""
        if self.sprite_name != sprite_name:
            self.sprite_name = sprite_name
            self._invalidate_cache()
            
    def set_tint(self, color) -> None:
        """Set the tint color for the sprite with cache invalidation."""
        # Normalize color to pygame.Color
        if isinstance(color, pygame.Color):
            new_color = color
        elif isinstance(color, (tuple, list)):
            if len(color) == 3:
                new_color = pygame.Color(*color, 255)
            elif len(color) >= 4:
                new_color = pygame.Color(*color[:4])
            else:
                new_color = pygame.Color(255, 255, 255, 255)
        else:
            new_color = pygame.Color(255, 255, 255, 255)
            
        if self.tint_color != new_color:
            self.tint_color = new_color
            self._invalidate_cache()
            
    def set_alpha(self, alpha: int) -> None:
        """Set the alpha transparency (0-255)."""
        alpha = max(0, min(255, alpha))
        if self.alpha != alpha:
            self.alpha = alpha
            self._invalidate_cache()
            
    def set_flip(self, horizontal: bool = False, vertical: bool = False) -> None:
        """Set horizontal and/or vertical flipping."""
        if self.flip_horizontal != horizontal or self.flip_vertical != vertical:
            self.flip_horizontal = horizontal
            self.flip_vertical = vertical
            self._invalidate_cache()
            
    def _invalidate_cache(self) -> None:
        """Mark the cached surface as dirty."""
        self._cache_dirty = True
        self._cached_surface = None
        
    def _get_base_surface(self) -> Optional[pygame.Surface]:
        """Get the base surface from the asset manager."""
        if not self.sprite_name:
            return None

        return AssetManager().getImage(self.sprite_name)

    def _get_processed_surface(self) -> Optional[pygame.Surface]:
        """Get the processed surface with all transformations applied."""
        if not self.sprite_name:
            return None
            
        # Check if we need to rebuild the cache
        if not self._cache_dirty and self._cached_surface:
            return self._cached_surface
            
        # Get base surface
        base_surface = self._get_base_surface()
        if not base_surface:
            # Try to load the image if it's not cached
            asset_manager = AssetManager()
            base_surface = asset_manager.loadImage(self.sprite_name)
            if not base_surface:
                return None
                
        # Start with a copy of the base surface
        processed_surface = base_surface.copy()
        
        # Apply flipping
        if self.flip_horizontal or self.flip_vertical:
            processed_surface = pygame.transform.flip(
                processed_surface, 
                self.flip_horizontal, 
                self.flip_vertical
            )
            
        # Apply tinting
        if self.tint_color:
            # Create a colored surface to blend with
            tint_surface = pygame.Surface(processed_surface.get_size(), pygame.SRCALPHA)
            tint_surface.fill((*self.tint_color[:3], 128))  # Use semi-transparent tint
            processed_surface.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_MULT)
            
        # Apply alpha
        if self.alpha < 255:
            processed_surface.set_alpha(self.alpha)
            
        # Cache the result
        self._cached_surface = processed_surface
        self._cache_dirty = False
        
        return processed_surface
        
    def get_sprite_rect(self) -> Optional[pygame.Rect]:
        """Get the rectangle of the sprite in world coordinates."""
        surface = self._get_processed_surface()
        if not surface or not self.actor:
            return None
            
        # Calculate final position with offset
        final_pos = self.actor.transform.position + self.offset
        
        # Get surface dimensions (potentially scaled)
        sprite_size = surface.get_size()
        if self.scale_modifier.x != 1 or self.scale_modifier.y != 1:
            sprite_size = (
                int(sprite_size[0] * self.scale_modifier.x * self.actor.transform.scale.x),
                int(sprite_size[1] * self.scale_modifier.y * self.actor.transform.scale.y)
            )
        else:
            sprite_size = (
                int(sprite_size[0] * self.actor.transform.scale.x),
                int(sprite_size[1] * self.actor.transform.scale.y)
            )
            
        # Create rect centered on position
        rect = pygame.Rect(0, 0, *sprite_size)
        rect.center = (int(final_pos.x), int(final_pos.y))
        
        return rect
        
    def render(self) -> None:
        """Optimized render method using sprite cache and fast math."""
        if not self.visible or not self.sprite_name or not self.actor:
            return
        
        # Calculate final position with offset using fast math
        final_pos_x = self.actor.screenPosition.x + self.offset.x
        final_pos_y = self.actor.screenPosition.y + self.offset.y
        
        # Calculate final transforms
        final_scale = (
            self.actor.transform.scale.x * self.scale_modifier.x,
            self.actor.transform.scale.y * self.scale_modifier.y
        )
        final_rotation = self.actor.transform.rotation + self.rotation_offset
        
        # Generate transform key for caching
        if self.tint_color:
            if hasattr(self.tint_color, 'r'):
                # pygame.Color object
                tint_tuple = (self.tint_color.r, self.tint_color.g, self.tint_color.b, self.tint_color.a)
            elif isinstance(self.tint_color, (tuple, list)) and len(self.tint_color) >= 3:
                # Tuple/list format
                if len(self.tint_color) == 3:
                    tint_tuple = (*self.tint_color, 255)  # Add alpha if missing
                else:
                    tint_tuple = tuple(self.tint_color[:4])
            else:
                tint_tuple = (255, 255, 255, 255)
        else:
            tint_tuple = (255, 255, 255, 255)
        
        # Try to get cached transformed sprite
        sprite_surface = self._sprite_cache.get_transformed_sprite(
            self.sprite_name,
            final_scale,
            final_rotation,
            tint_tuple,
            self.alpha
        )
        
        if not sprite_surface:
            # Fallback to asset manager if not in cache
            original_surface = AssetManager().getSprite(self.sprite_name)
            if not original_surface:
                return
            
            # Cache the original surface
            self._sprite_cache.cache_surface(self.sprite_name, original_surface)
            
            # Get transformed version
            sprite_surface = self._sprite_cache.get_transformed_sprite(
                self.sprite_name,
                final_scale,
                final_rotation,
                tint_tuple,
                self.alpha
            )
        
        if not sprite_surface:
            return
        
        # Apply flipping if needed (not cached as it's rare)
        if self.flip_horizontal or self.flip_vertical:
            sprite_surface = pygame.transform.flip(sprite_surface, self.flip_horizontal, self.flip_vertical)
        
        # Calculate render position using fast math
        render_rect = sprite_surface.get_rect()
        render_rect.center = (int(final_pos_x), int(final_pos_y))
        
        # Render to the target surface
        Game().buffer.blit(sprite_surface, render_rect)
        
    def start(self) -> None:
        """Initialize the sprite component when attached to an actor."""
        super().start()
        # Preload the sprite if specified
        if self.sprite_name:
            AssetManager().loadImage(self.sprite_name)
            
    def serialize(self) -> dict:
        """Serialize the sprite component data."""
        data = super().serialize()
        
        # Convert pygame.Color to tuple for serialization
        if self.tint_color:
            data['tint_color'] = (self.tint_color.r, self.tint_color.g, self.tint_color.b, self.tint_color.a)
        
        return data
        
    def deserialize(self, data: dict):
        """Deserialize the sprite component data."""
        super().deserialize(data)
        
        # Convert tint_color tuple back to pygame.Color
        if 'tint_color' in data and data['tint_color']:
            self.tint_color = pygame.Color(*data['tint_color'])
            
        # Invalidate cache after deserialization
        self._invalidate_cache()
        
        return self