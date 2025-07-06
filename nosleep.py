import pygame
from engine.core.game import Game
from engine.core.scene import Scene
from engine.builtin.ui.label import Label

class NoSleepScene(Scene):
    def __init__(self):
        super().__init__("NoSleep")
        self.background_color = (0, 0, 0)
        self.ui_manager.add_element(Label([Game().width // 2, Game().height // 2 - 50], 1000, text="Died of no sleep", font_size=48, color=(255, 255, 255)))
        self.ui_manager.add_element(Label([Game().width // 2, Game().height // 2 + 20], 1000, text="Press ESC to return to Main Menu", font_size=24, color=(255, 255, 255)))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                Game().load_scene("MainMenu")
        return super().handle_event(event)
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F4:
                Game().toggle_fullscreen()
            if event.key == pygame.K_ESCAPE:
                Game().load_scene("MainMenu")
        return super().handle_event(event)