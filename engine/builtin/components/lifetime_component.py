from ...core.world.component import Component

class LifetimeComponent(Component):
    def __init__(self, lifetime: float):
        super().__init__()
        self.remaining_time = lifetime

    def update(self, dt):
        self.remaining_time -= dt
        if self.remaining_time <= 0:
            if self.actor and self.actor.scene:
                self.actor.scene.remove_actor(self.actor)
