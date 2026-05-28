import math
import arcade
import pymunk
from game_logic import ImpulseVector

BIRD_SPEED_FACTOR = 0.8


class Bird(arcade.Sprite):
    def __init__(
        self,
        image_path: str,
        impulse_vector: ImpulseVector,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 5,
        radius: float = 12,
        max_impulse: float = 300,
        power_multiplier: float = 50,
        elasticity: float = 0.8,
        friction: float = 1,
        collision_layer: int = 0,
    ):
        super().__init__(image_path, 1)
        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)

        impulse = min(max_impulse, impulse_vector.impulse) * power_multiplier
        impulse *= BIRD_SPEED_FACTOR
        impulse_pymunk = impulse * pymunk.Vec2d(1, 0)
        body.apply_impulse_at_local_point(impulse_pymunk.rotated(impulse_vector.angle))

        shape = pymunk.Circle(body, radius)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer

        space.add(body, shape)

        self.body = body
        self.shape = shape

    def update(self, delta_time):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class Pig(arcade.Sprite):
    def __init__(
        self,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2,
        elasticity: float = 0.8,
        friction: float = 0.4,
        collision_layer: int = 0,
    ):
        super().__init__("assets/img/pig_failed.png", 0.1)
        moment = pymunk.moment_for_circle(mass, 0, self.width / 2 - 3)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Circle(body, self.width / 2 - 3)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape

    def update(self, delta_time):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class PassiveObject(arcade.Sprite):
    def __init__(
        self,
        image_path: str,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2,
        elasticity: float = 0.8,
        friction: float = 1,
        collision_layer: int = 0,
    ):
        super().__init__(image_path, 1)
        moment = pymunk.moment_for_box(mass, (self.width, self.height))
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Poly.create_box(body, (self.width, self.height))
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape

    def update(self, delta_time):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class Column(PassiveObject):
    def __init__(self, x, y, space):
        super().__init__("assets/img/column.png", x, y, space)


class YellowBird(Bird):
    def __init__(self, impulse_vector, x, y, space, power_multiplier=2):
        super().__init__("assets/img/yellow.png", impulse_vector, x, y, space)
        self.ability_used = False
        self.power_multiplier = power_multiplier

    def activate_power(self):
        if self.ability_used:
            return
        velocity = self.body.velocity
        if velocity.length == 0:
            return
        self.body.velocity = velocity * self.power_multiplier
        self.ability_used = True


class BlueBird(Bird):
    def __init__(self, impulse_vector, x, y, space):
        super().__init__("assets/img/blue.png", impulse_vector, x, y, space)
        self.space = space
        self.ability_used = False

    def split(self):
        if self.ability_used:
            return []
        velocity = self.body.velocity
        speed = velocity.length
        if speed == 0:
            return []

        angle = velocity.angle
        birds = []

        for offset_deg in [-30, 0, 30]:
            offset_rad = math.radians(offset_deg)
            new_velocity = pymunk.Vec2d(speed, 0).rotated(angle + offset_rad)

            
            bird = BlueBird(ImpulseVector(0, 0), self.center_x, self.center_y, self.space)
             
            bird.body.velocity = new_velocity
            birds.append(bird)

        self.ability_used = True
        return birds