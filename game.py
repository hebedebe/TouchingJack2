import pygame
from copy import copy
import math
import random

from engine.core.scene import Scene
from engine.core.game import Game
from engine.core.world.actor import Actor
from engine.core.world.component import Component
from engine.core.asset_manager import AssetManager

from engine.builtin.ui.button import Button
from engine.builtin.ui.label import Label
from engine.builtin.ui.fps_counter import FPSCounter
from engine.builtin.ui.panel import Panel
from engine.builtin.ui.progress_bar import ProgressBar

from engine.builtin.components.sprite_component import SpriteComponent
from engine.builtin.components.camera_component import CameraComponent
from engine.builtin.components.clickable_component import ClickableComponent
from engine.builtin.components.audio_component import AudioComponent

class GameScene(Scene):
    def __init__(self):
        super().__init__("Game")
        self.position = 1
        self.positions = [
            pygame.Vector2(-640, 0),  # Left position
            pygame.Vector2(0, 0),     # Middle position
            pygame.Vector2(640, 0)    # Right position
        ]
        self.monitor_on = False
        self.current_camera = 0
        self.cameras = ["cam_basement", "cam_lockerroom", "cam_hotel"]

        self.jack_pos = 0  # -1 means outside, 0 means cam_1, 1 means cam_2, 2 means cam_3
        self.jack_positions = ["jack_cam_1", "jack_cam_2", "jack_cam_3", "jack_outside"]
        self.jack_locations = [(20, 70), (0, 0), (0, 0), (640,0)]
        self.jack_sizes = [0.05, 0.1, 0.1, 0.9]
        self.jack_move_timer = random.randint(20, 30)
        self.jack_jumpscare_timer_min = 5
        self.jack_jumpscare_timer_max = 6
        self.jack_noticed = False

        self._sound = 0
        self.sound = 0
        self.max_sound = 4
        self.target_sound = 0
        self.sound_smoothing = 10
        self.passive_monitor_sound = 0.7
        self.monitor_turn_on_sound = 2
        self.move_sound = 0.7
        self.switch_camera_sound = 1
        self.sound_aggression = 2
        self.passive_sound_aggression = 1
        self.sound_fade_rate = 1

        self.touch_o_meter = 0
        self.touch_o_meter_max = 1

        self.power = 100
        self.power_drain_rate = 1.2

        self.time = 0
        self.hour_length = 60  # Length of an hour in seconds

        self.sleep = 100
        self.sleep_drain_rate = 1  # Rate at which sleep decreases
        self.asleep = False
        self.sleep_timer = 0
        self.sleep_timer_max = 8  # Maximum time before waking up in seconds

        self.max_wait_time_params = [40, 3, 0.9, 10, 1.5]
        self.min_wait_time_params = [5, 3, 0.9, 0.65, 3.7]

    def calc_wait_time(self, base_time, aggression, offset, ramp, ramp2):
        return max(4,int(base_time - math.log(aggression * ((self.time/self.hour_length) + offset)**ramp)**ramp2 - self.sound * self.sound_aggression))

    def on_enter(self):
        pygame.mixer.music.load("assets/sounds/ambient_game.mp3")
        pygame.mixer.music.play(-1)

        interior_brightness = 200  # Adjust this value to change the brightness of the interior

        outside = Actor("outside")
        outside_sprite = SpriteComponent("outside", tint_color=(100, 100, 100))
        outside.transform.scale = pygame.Vector2(0.9)  # Adjust scale as needed
        outside.transform.position = self.positions[2]
        outside.transform.rotation = 90
        outside.addComponent(outside_sprite)
        self.add_actor(outside)

        monitor = Actor("monitor")
        monitor_sprite = SpriteComponent("monitor", tint_color=(interior_brightness, interior_brightness, interior_brightness))
        monitor.transform.scale = pygame.Vector2(1)  # Adjust scale as needed
        monitor.transform.position = self.positions[1]
        monitor.addComponent(monitor_sprite)
        self.add_actor(monitor)

        monitor_background = Actor("monitor_background")
        monitor_background_sprite = SpriteComponent(self.cameras[self.current_camera])
        monitor_background.transform.scale = pygame.Vector2(0.32)  # Adjust scale as needed
        monitor_background.transform.position = self.positions[1] + pygame.Vector2(10, 5)
        monitor_background.addComponent(monitor_background_sprite)
        self.add_actor(monitor_background)

        monitor_jack = Actor("monitor_jack")
        monitor_jack_sprite = SpriteComponent(self.jack_positions[self.jack_pos])
        monitor_jack.transform.scale = pygame.Vector2(0.1)  # Adjust scale as needed
        monitor_jack.transform.position = self.positions[1]
        monitor_jack.addComponent(monitor_jack_sprite)
        self.add_actor(monitor_jack)

        power_button = Actor("power_button")
        power_button_sprite = SpriteComponent("power_button", tint_color=(interior_brightness, interior_brightness, interior_brightness))
        power_button_click = ClickableComponent(20, 20, (0, 0))
        power_button_click_audio = AudioComponent("click")
        power_button_start_audio = AudioComponent("startup", volume=2)
        def toggle_monitor():
            if (self.power <= 0):
                return
            power_button_click_audio.play()
            self.monitor_on = not self.monitor_on
            if self.monitor_on:
                self.power -= 1
                power_button_start_audio.play()
                self.target_sound += self.monitor_turn_on_sound
            else:
                power_button_start_audio.stop()
        power_button_click.set_click_callback(lambda: toggle_monitor())
        power_button.transform.scale = pygame.Vector2(0.03)  # Adjust scale as needed
        power_button.transform.position = pygame.Vector2(self.positions[1].x+125, 102)
        power_button.addComponent(power_button_sprite)
        power_button.addComponent(power_button_click)
        self.add_actor(power_button)

        fireman_poster = Actor("fireman_poster")
        fireman_poster_sprite = SpriteComponent("fireman_poster", tint_color=(interior_brightness, interior_brightness, interior_brightness))
        fireman_poster_click = ClickableComponent(70, 100, (5, 0))
        fireman_poster_audio = AudioComponent("grunt")
        fireman_poster_click.set_click_callback(lambda: fireman_poster_audio.play())
        fireman_poster.transform.scale = pygame.Vector2(0.2)  # Adjust scale as needed
        fireman_poster.transform.position = pygame.Vector2(self.positions[1].x+230, -150)
        fireman_poster.addComponent(fireman_poster_sprite)
        fireman_poster.addComponent(fireman_poster_click)
        fireman_poster.addComponent(fireman_poster_audio)
        self.add_actor(fireman_poster)

        bed = Actor("bed")
        bed_sprite = SpriteComponent("bed", tint_color=(interior_brightness, interior_brightness, interior_brightness))
        bed.transform.scale = pygame.Vector2(1.5)  # Adjust scale as needed
        bed.transform.position = self.positions[0]
        bed.transform.position.x -= 130
        bed.addComponent(bed_sprite)
        self.add_actor(bed)

        window = Actor("window")
        window_sprite = SpriteComponent("window", tint_color=(interior_brightness, interior_brightness, interior_brightness))
        window.transform.scale = pygame.Vector2(1)  # Adjust scale as needed
        window.transform.position = self.positions[2]
        window.addComponent(window_sprite)
        self.add_actor(window)

        camera = Actor("camera")
        camera.addComponent(CameraComponent(interpolate=True, smoothing=20))
        self.sleep_overlay = SpriteComponent("asleep")
        self.sleep_overlay.enabled = False
        camera.transform.scale = pygame.Vector2(1.3)  # Adjust scale as needed
        camera.addComponent(self.sleep_overlay)
        camera.transform.position = self.positions[1]
        self.add_actor(camera)

        self.look_left_button = Button([0, Game().height//2-70], 50, 150, "<<<", font_size=24, on_click_callback=self.look_left)
        self.look_right_button = Button([Game().width - 50, Game().height//2-70], 50, 150, ">>>", font_size=24, on_click_callback=self.look_right)
        self.lower_panel = Panel((0,430), Game().width, 100)
        self.time_label = Label([Game().width//2+200, 440], 1000, text=f"Time: ", font_size=24, color=(255, 255, 255))
        self.sound_label = Label([Game().width//2+140, 460], 1000, text=f"Sound: ", font_size=24, color=(255, 255, 255))
        self.sound_bar = ProgressBar([Game().width//2+200, 460], 100, 20, 0, color=(255, 0, 0), background_color=(50, 50, 50))
        self.power_label = Label([Game().width//2-310, 440], 1000, text=f"Power: {self.power}", font_size=24, color=(200, 0, 0))
        self.sleep_label = Label([Game().width//2-310, 460], 1000, text=f"Sleep: {self.sleep}", font_size=24, color=(200, 0, 0))
        self.lower_panel.add_child(self.power_label)
        self.lower_panel.add_child(self.sleep_label)
        self.lower_panel.add_child(self.time_label)
        self.lower_panel.add_child(self.sound_label)
        self.lower_panel.add_child(self.sound_bar)

        def _sleep():
            if self.sleep > 40:
                print("You are too awake to sleep!")
                return
            self.asleep = True
            self.sleep_timer = 0
            self.sleep_timer -= random.randint(1, 3)
            print("Sleeping...")

        self.sleep_button = Button((Game().width//2-100, 440), 200, 50, "Sleep", font_size=24, on_click_callback=_sleep)

        def prev_cam():
            self.current_camera = max(self.current_camera - 1, 0)
            AssetManager().getSound("switch_cam").play()
            self.target_sound += self.switch_camera_sound

        def next_cam():
            self.current_camera = min(self.current_camera + 1, len(self.cameras) - 1)
            AssetManager().getSound("switch_cam").play()
            self.target_sound += self.switch_camera_sound

        self.next_cam_button = Button((Game().width//2-55, 440), 50, 50, "<", font_size=24, on_click_callback=prev_cam)
        self.previous_cam_button = Button((Game().width//2+55, 440), 50, 50, ">", font_size=24, on_click_callback=next_cam)

        def touch_jack():
            self.touch_o_meter += 0.1
            AssetManager().getSound("squish").play()
            self.touch_o_meter = min(self.touch_o_meter, self.touch_o_meter_max+0.05)
            if self.touch_o_meter >= self.touch_o_meter_max:
                self.jack_noticed = False
                self.jack_pos = 0
                self.jack_move_timer = random.randint(self.calc_wait_time(*self.min_wait_time_params), self.calc_wait_time(*self.max_wait_time_params))
                AssetManager().getSound("yowch").play()


        self.touch_jack_button = Button((Game().width//2, 440), 100, 50, "Touch Jack", font_size=24, on_click_callback=touch_jack)
        self.touch_jack_bar = ProgressBar((Game().width//2-110, 440), 100, 50, self.touch_o_meter, (255, 0, 0), (50, 50, 50))

        self.lower_panel.add_child(self.sleep_button)
        self.lower_panel.add_child(self.next_cam_button)
        self.lower_panel.add_child(self.previous_cam_button)
        self.lower_panel.add_child(self.touch_jack_button)
        self.lower_panel.add_child(self.touch_jack_bar)

        self.look_left_button.visible = False
        self.ui_manager.add_element(self.look_left_button)
        self.ui_manager.add_element(self.look_right_button)
        self.ui_manager.add_element(FPSCounter())
        self.ui_manager.add_element(self.lower_panel)


    def on_exit(self):
        pygame.mixer.music.stop()
        return super().on_exit()
    
    def update(self, delta_time):
        # Update camera position based on the current position
        self.get_actor("camera").transform.position = self.positions[self.position]

        if self.time >= self.hour_length * 6:  # 6 AM
            Game().load_scene("Win")

        # Show or hide camera buttons based on position
        self.look_left_button.set_active(self.position > 0 and not self.asleep)
        self.look_right_button.set_active(self.position < 2 and not self.asleep)

        if self.sleep > 40:
            self.sleep_button.text = "Can't sleep yet"
        else:
            self.sleep_button.text = "Sleep"

        if self.power <= 0:
            self.monitor_on = False

        if self.position == 2 and self.jack_pos == -1 and not self.jack_noticed:
            AssetManager().getSound("sting").play()
            self.jack_noticed = True

        self.sleep_button.set_active(self.position == 0 and not self.asleep)
        self.next_cam_button.set_active(self.position == 1 and not self.asleep and self.monitor_on)
        self.previous_cam_button.set_active(self.position == 1 and not self.asleep and self.monitor_on)
        self.touch_jack_button.set_active(self.position == 2 and not self.asleep and self.jack_pos == -1)
        self.touch_jack_bar.visible = self.position == 2 and not self.asleep and self.jack_pos == -1
        self.touch_jack_bar.set_progress(self.touch_o_meter / self.touch_o_meter_max)
        self.sound_bar.set_progress(self.sound / self.max_sound)

        monitor_background = self.get_actor("monitor_background")
        monitor_background.getComponent(SpriteComponent).set_sprite(self.cameras[self.current_camera])
        monitor_jack = self.get_actor("monitor_jack")
        monitor_jack.transform.scale = pygame.Vector2(self.jack_sizes[self.jack_pos])
        monitor_jack.getComponent(SpriteComponent).set_sprite(self.jack_positions[self.jack_pos])
        monitor_jack.transform.position = self.positions[1] + self.jack_locations[self.jack_pos]

        monitor_background.getComponent(SpriteComponent).enabled = self.monitor_on
        # Show jack when monitor is on and either jack is on current camera or jack is outside (pos -1) on camera 2
        jack_visible = (self.monitor_on and (self.current_camera == self.jack_pos)) or self.jack_pos == -1
        monitor_jack.getComponent(SpriteComponent).enabled = jack_visible
        monitor_jack.getComponent(SpriteComponent).set_tint((100, 100, 100) if self.jack_pos == -1 else (255, 255, 255))

        self.sleep_overlay.enabled = self.asleep

        if self.monitor_on:
            self.power -= delta_time * self.power_drain_rate

        if self.asleep:
            self.sleep_timer += delta_time
            if self.sleep_timer >= self.sleep_timer_max:
                self.asleep = False
                self.sleep_timer = 0
                self.sleep = 100
        else:
            self.sleep -= delta_time * self.sleep_drain_rate

        self.sleep = max(0, self.sleep)
        self.power = max(0, self.power)

        self.time += delta_time
        time = (self.time // self.hour_length)
        if time <= 0:
            time = 12
        self.time_label.text = f"{int(time)} AM"
        self.power_label.text = f"Power: {math.ceil(self.power)}%"
        self.sleep_label.text = f"Sleep: {math.ceil(self.sleep)}%"

        self.touch_o_meter -= delta_time * 0.2
        self.touch_o_meter = max(0, self.touch_o_meter)

        if self.sleep <= 0:
            Game().load_scene("NoSleep")

        self.target_sound = min(max(0, self.target_sound - (self.sound_fade_rate * delta_time)), self.max_sound)
        self._sound = min(self._sound + ((self.target_sound - self._sound) * (self.sound_smoothing * delta_time)), self.max_sound)

        self.sound = self._sound + self.passive_monitor_sound * self.monitor_on

        self.jack_move_timer -= delta_time
        if self.jack_move_timer - (self.sound * self.passive_sound_aggression) <= 0:
            mintime = self.calc_wait_time(*self.min_wait_time_params)
            maxtime = self.calc_wait_time(*self.max_wait_time_params)
            self.jack_move_timer = random.randint(mintime, maxtime)
            print(f"min wait time: {mintime}, max wait time: {maxtime}")
            if self.jack_pos == -1:
                Game().load_scene("Jumpscare")
            else:
                self.jack_pos += 1
                if self.jack_pos > 2:
                    self.jack_pos = -1 if random.random() < 0.5 else random.choice([0, 1, 2])
                if self.jack_pos == -1:
                    self.jack_move_timer = random.randint(self.jack_jumpscare_timer_min, self.jack_jumpscare_timer_max)
            print(f"Set wait time to {self.jack_move_timer:.2f} seconds")

        super().update(delta_time)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F4:
                Game().toggle_fullscreen()
            if event.key == pygame.K_ESCAPE:
                Game().load_scene("MainMenu")
        return super().handle_event(event)

    def look_left(self):
        self.position = max(0, self.position - 1)
        AssetManager().getSound("woosh").play()
        self.target_sound += self.move_sound

    def look_right(self):
        self.position = min(2, self.position + 1)
        AssetManager().getSound("woosh").play()
        self.target_sound += self.move_sound
