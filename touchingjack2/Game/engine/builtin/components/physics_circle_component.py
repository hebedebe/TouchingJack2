import pymunk

from .physics_component import PhysicsComponent

class PhysicsCircleComponent(PhysicsComponent):
    """
    A component that represents a circular physics body.
    It extends the PhysicsComponent to handle circular shapes.
    """

    def __init__(self, radius=25, mass=1, bodyType=pymunk.Body.DYNAMIC):
        """
        Initializes the PhysicsCircleComponent with a body and radius.
        
        :param body: The pymunk.Body object representing the physics body.
        :param radius: The radius of the circle.
        """
        self.radius = radius
        body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius), bodyType)
        super().__init__(body, [pymunk.Circle(body, radius)])