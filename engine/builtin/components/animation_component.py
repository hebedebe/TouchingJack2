import pygame
from copy import copy

from ...core.game import Game
from ...core.world.component import Component

from ...animation.animation import Animation

class AnimationComponent(Component):
    def __init__(self, frames, tint=(255, 255, 255), opacity=255):
        super().__init__()
        self.animation = Animation(frames)
        self.tint = tint
        self.opacity = opacity
        self.timer = 0
        self.frame_index = 0
    
    def update(self, delta_time):
        super().update(delta_time)
        self.timer += delta_time
        self.frame_index = int(self.timer // self.animation.frame_time)%self.animation.numFrames

    @property
    def currentFrame(self):
        return self.animation.frames[self.frame_index].surface

    def render(self):
        super().render()
        frame = copy(self.currentFrame)
        if (self.tint != (255, 255, 255, 255)):
            frame.fill(self.tint, special_flags=pygame.BLEND_MULT)
        frame.set_alpha(self.opacity)
        
        # Apply actor's transform (scale and rotation)
        final_scale = self.actor.transform.scale
        final_rotation = self.actor.transform.rotation
        
        # Apply scaling if needed
        if final_scale.x != 1 or final_scale.y != 1:
            new_size = (
                int(frame.get_width() * final_scale.x),
                int(frame.get_height() * final_scale.y)
            )
            if new_size[0] > 0 and new_size[1] > 0:
                frame = pygame.transform.scale(frame, new_size)
        
        # Apply rotation if needed
        if final_rotation != 0:
            frame = pygame.transform.rotate(frame, -final_rotation)  # Negative for clockwise
        
        # Calculate render position (center the frame)
        render_rect = frame.get_rect()
        render_rect.center = (int(self.actor.screenPosition.x), int(self.actor.screenPosition.y))
        
        Game().buffer.blit(frame, render_rect)
