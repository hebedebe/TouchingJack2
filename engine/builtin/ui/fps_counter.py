import pygame
from engine.core.ui import UIElement
from engine.core.game import Game

class FPSCounter(UIElement):
    def __init__(self, position=(0,0), font_size=24, color=(255, 255, 255)):
        super().__init__(position, 0, 0)  # Width and height are dynamic based on text
        self.font = pygame.font.Font(None, font_size)
        self.color = color

    def render(self, screen):
        fps = int(Game().clock.get_fps())
        text_surface = self.font.render(f"FPS: {fps}", True, self.color)
        self.rect.width, self.rect.height = text_surface.get_size()
        screen.blit(text_surface, (self.rect.x, self.rect.y))
