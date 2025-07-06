# engine/component/builtin/boxRendererComponent.py

from ...core.world.component import Component
import pygame

class BoxRendererComponent(Component):
    def __init__(self, size=(50, 50), color=(255, 255, 255)):
        super().__init__()
        self.size = size
        self.color = color

    def render(self, screen):
        if not self.actor or not self.actor.physics:
            return

        width, height = self.size
        center = self.actor.screenPosition

        # Create and rotate rectangle surface
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill(self.color)
        rotated = pygame.transform.rotate(surf, -self.actor.transform.rotation * 57.2958)  # Radians to degrees
        rect = rotated.get_rect(center=center)

        screen.blit(rotated, rect.topleft)
