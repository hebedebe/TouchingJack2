import pygame
from engine.core.ui import UIElement

class ProgressBar(UIElement):
    def __init__(self, position, width, height, progress=0.0, color=(0, 255, 0), background_color=(50, 50, 50)):
        super().__init__(position, width, height)
        self.progress = max(0.0, min(1.0, progress))  # Clamp between 0.0 and 1.0
        self.color = color
        self.background_color = background_color

    def render(self, screen):
        if self.visible:
            pygame.draw.rect(screen, self.background_color, self.rect)
            progress_width = int(self.rect.width * self.progress)
            progress_rect = pygame.Rect(self.rect.x, self.rect.y, progress_width, self.rect.height)
            pygame.draw.rect(screen, self.color, progress_rect)

    def set_progress(self, progress):
        self.progress = max(0.0, min(1.0, progress))
