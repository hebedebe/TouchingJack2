import pygame
from ...core.world.component import Component

class BasicMovementComponent(Component):
    def __init__(self, speed: float = 100):
        super().__init__()
        self.speed = speed  # Pixels per second

    def update(self, dt: float) -> None:
        super().update(dt)

        move = pygame.Vector2(0, 0)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move.y += 1

        if move.length_squared() > 0:
            move = move.normalize() * self.speed * dt
            self.actor.transform.position += move