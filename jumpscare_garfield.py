import pygame
from engine.core.game import Game
from engine.core.scene import Scene
from engine.core.asset_manager import AssetManager

class JumpscareGarfieldScene(Scene):
    def __init__(self):
        super().__init__("Jumpscare Garfield")
        self.background_color = (0, 0, 0)
        self.jumpscare_image = AssetManager().getImage("jumpscare_garfield")
        self.jumpscare_rect = self.jumpscare_image.get_rect(center=(Game().width // 2, Game().height // 2))
        self.timer = 2

    def on_enter(self):
        AssetManager().getSound("jumpscare_sound").play()
        AssetManager().getSound("meow").play()
        return super().on_enter()
    
    def on_exit(self):
        return super().on_exit()

    def render(self):
        surface = Game().buffer
        surface.fill(self.background_color)
        surface.blit(self.jumpscare_image, self.jumpscare_rect)
    
    def update(self, delta_time):
        self.timer -= delta_time
        if self.timer <= 0:
            Game().load_scene("GameOver")
        self.jumpscare_image.set_alpha(int(255 * (self.timer / 2)))  # Fade out effect
        return super().update(delta_time)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F4:
                Game().toggle_fullscreen()
            if event.key == pygame.K_ESCAPE:
                Game().load_scene("MainMenu")
        return super().handle_event(event)