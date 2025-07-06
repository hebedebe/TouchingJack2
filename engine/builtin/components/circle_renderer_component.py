import pygame

from ...core.world.component import Component
from ...core.game import Game

class CircleRendererComponent(Component):
    def __init__(self, radius=25, color=(255,255,255,255)):
        super().__init__()
        self.radius = radius
        self.color = color
        

    def render(self):
        pygame.draw.circle(Game().buffer, self.color, self.actor.screenPosition, self.radius)