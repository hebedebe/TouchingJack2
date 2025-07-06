import pygame

class UIElement:
    def __init__(self, position, width, height):
        self.rect = pygame.Rect(position[0], position[1], width, height)
        self.visible = True

    def update(self, delta_time):
        """Update the UI element. Override in subclasses if needed."""
        pass

    def render(self, screen):
        if self.visible:
            pygame.draw.rect(screen, (255, 255, 255), self.rect, 1)

    def handle_event(self, event):
        pass

class UIManager:
    def __init__(self):
        self.elements = []

    def add_element(self, element):
        self.elements.append(element)

    def render(self, screen):
        for element in self.elements:
            element.render(screen)

    def handle_event(self, event):
        for element in self.elements:
            element.handle_event(event)