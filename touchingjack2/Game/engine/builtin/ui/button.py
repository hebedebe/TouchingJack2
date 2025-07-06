import pygame
from engine.core.ui import UIElement
from engine.core.asset_manager import AssetManager

class Button(UIElement):
    def __init__(self, position, width, height, text, font=None, font_size=24, on_click_callback=None, on_start_hover_callback=None, on_stop_hover_callback=None):
        super().__init__(position, width, height)
        self.text = text
        
        self.on_click_callback = on_click_callback
        self.on_start_hover_callback = on_start_hover_callback
        self.on_stop_hover_callback = on_stop_hover_callback

        self.font = AssetManager().getFont(font, font_size) if font is not None else AssetManager().getDefaultFont(size=font_size)
        self.hovered = False

        self.enabled = True
        self.visible = True

    def set_active(self, active):
        """Set the button active or inactive."""
        self.enabled = active
        self.visible = active

    def render(self, screen):
        super().render(screen)
        if self.visible:
            color = (200, 200, 200) if self.hovered else (255, 255, 255)
            text_surface = self.font.render(self.text, True, color)
            pygame.draw.rect(screen, (100, 100, 100) if self.hovered else (50, 50, 50), self.rect)
            screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))

    def handle_event(self, event):
        if not self.enabled:
            return
        if event.type == pygame.MOUSEMOTION:
            is_hovered = self.rect.collidepoint(event.pos)
            if is_hovered and not self.hovered:
                self.hovered = True
                if self.on_start_hover_callback:
                    self.on_start_hover_callback()
            elif not is_hovered and self.hovered:
                self.hovered = False
                if self.on_stop_hover_callback:
                    self.on_stop_hover_callback()

        elif event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.on_click_callback:
                self.on_click_callback()
