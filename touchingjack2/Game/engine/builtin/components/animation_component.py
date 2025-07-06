import pygame
from copy import copy

from ...core.game import Game
from ...core.world.component import Component

from ...animation.animation import Animation

class AnimationComponent(Component):
    def __init__(self, frames, tint=(255, 255, 255)):
        super().__init__()
        self.animation = Animation(frames)
        self.tint = tint
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
        if (self.tint != (255, 255, 255)):
            frame.fill(self.tint, special_flags=pygame.BLEND_MULT)
        Game().buffer.blit(frame, self.actor.screenPosition)
