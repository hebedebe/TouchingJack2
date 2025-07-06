import pygame
from engine.core.ui import UIElement

class Label(UIElement):
    def __init__(self, position, width, text, font=None, font_size=24, color=(255, 255, 255)):
        super().__init__(position, width, 0)
        self.text = text
        self.font = pygame.font.Font(font, font_size) if font else pygame.font.Font(None, font_size)
        self.color = color

    def render(self, screen):
        if self.visible:
            words = self.text.split(' ')
            lines = []
            current_line = ''
            for word in words:
                test_line = current_line + word + ' '
                text_surface = self.font.render(test_line.strip(), True, self.color)
                if text_surface.get_width() > self.rect.width:
                    lines.append(current_line.strip())
                    current_line = word + ' '
                else:
                    current_line = test_line
            lines.append(current_line.strip())

            y_offset = self.rect.y
            for line in lines:
                text_surface = self.font.render(line, True, self.color)
                screen.blit(text_surface, (self.rect.x, y_offset))
                y_offset += text_surface.get_height()

    def set_text(self, text):
        self.text = text
