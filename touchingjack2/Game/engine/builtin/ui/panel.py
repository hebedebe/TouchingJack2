import pygame
from engine.core.ui import UIElement

class Panel(UIElement):
    def __init__(self, position, width, height):
        super().__init__(position, width, height)
        self.children = []
        self.background_color = (30, 30, 30)

    def add_child(self, child):
        self.children.append(child)

    def render(self, screen):
        if self.visible:
            pygame.draw.rect(screen, self.background_color, self.rect)
        super().render(screen)
        for child in self.children:
            child.render(screen)

    def handle_event(self, event):
        for child in self.children:
            child.handle_event(event)