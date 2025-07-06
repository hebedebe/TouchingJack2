from ...core.world.component import Component
from ...core.game import Game

class PhysicsComponent(Component):
    def __init__(self, body=None, shapes=[]):
        super().__init__()
        self.body = body
        self.shapes = [*shapes]

    def start(self):
        Game().current_scene.add_physics(self.actor)
        self.body.position = (*self.actor.transform.position,)
        self.body.rotation = self.actor.transform.rotation
        return super().start()

    def update(self, delta_time):
        self.body.position = (*self.actor.transform.position,)
        self.body.rotation = self.actor.transform.rotation
        return super().update(delta_time)
    
    def lateUpdate(self, delta_time):
        self.actor.transform.setPosition(self.body.position.x, self.body.position.y)
        self.actor.transform.setRotation(self.body.angle)
        return super().lateUpdate(delta_time)