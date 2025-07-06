import pygame

from ...core.world.component import Component
from ...core.game import Game

class CameraComponent(Component):
    """Camera component"""
    def __init__(self, interpolate=False, smoothing=10):
        super().__init__()
        self.position = pygame.Vector2()
        self.interpolate = interpolate
        self.smoothing = smoothing

    def lateUpdate(self, delta_time):
        if self.interpolate:
            self.position = pygame.Vector2.lerp(self.position, self.actor.transform.position, min(max(self.smoothing * delta_time, 0), 1))
        else:
            self.position = self.actor.transform.position

        Game().current_scene.worldOffset = self.position - pygame.Vector2(Game().width//2, Game().height//2) # type: ignore
        return super().lateUpdate(delta_time)