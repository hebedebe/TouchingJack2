import pygame
import math
import pymunk

from .physics_component import PhysicsComponent
from .input_component import InputComponent

class PhysicsDragComponent(InputComponent):
    def __init__(self, force=1000):
        super().__init__()
        self.dragging = False
        self.mouse_joint = None
        self.mouse_body = None
        self.force = force

    def start(self):
        self.bind_mouse(1, self.on_mouse_down, on_press=True)
        self.bind_mouse(1, self.on_mouse_up, on_press=False, on_release=True)

    def on_mouse_down(self):
        mouse_pos = self.getScene.tMousePos()
        actor_pos = self.actor.transform.position
        dx = mouse_pos[0] - actor_pos[0]
        dy = mouse_pos[1] - actor_pos[1]
        if dx*dx + dy*dy < 400:  # within 20px
            self.dragging = True
            # Create a kinematic body at the mouse position
            self.mouse_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
            self.mouse_body.position = mouse_pos
            # Create a pivot joint between mouse and actor
            phys = self.actor.getComponent(PhysicsComponent, allow_inheritance=True)
            if phys:
                self.mouse_joint = pymunk.PivotJoint(self.mouse_body, phys.body, (0,0), (0,0))
                self.mouse_joint.max_force = self.force
                self.actor.scene.physicsSpace.add(self.mouse_body, self.mouse_joint)

    def on_mouse_up(self):
        self.dragging = False
        if self.mouse_joint:
            self.actor.scene.physicsSpace.remove(self.mouse_joint)
            self.mouse_joint = None
        if self.mouse_body:
            self.actor.scene.physicsSpace.remove(self.mouse_body)
            self.mouse_body = None

    def update(self, delta_time):
        if self.dragging and self.mouse_body:
            mouse_pos = self.getScene.tMousePos()
            self.mouse_body.position = mouse_pos
            self.mouse_joint.max_force = abs(self.force*math.log(pygame.Vector2.distance_to(pygame.Vector2(mouse_pos), pygame.Vector2(self.actor.screenPosition))))