import math
import logging
import arcade
import pymunk

from game_object import Bird, Column, Pig, YellowBird, BlueBird
from game_logic import get_impulse_vector, Point2D, get_distance

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("arcade").setLevel(logging.WARNING)
logging.getLogger("pymunk").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

logger = logging.getLogger("main")

WIDTH = 1800
HEIGHT = 800
TITLE = "Angry birds"
GRAVITY = -900


MIN_DRAG_DISTANCE = 10
BOUNDS_MARGIN = 10


SCORE_VALUES = {
    Pig: 1000,
    Column: 250,
}

SLINGSHOT_X = 200
SLINGSHOT_Y = 150
SLINGSHOT_IMG = "assets/img/sling-3.png"

LEVELS = [
    {
        "min_score": 1500,
        "columns": [(x, 50) for x in range(WIDTH // 2, WIDTH, 400)],
        "pigs": [(WIDTH // 2, 100)],
    },
    {
        "min_score": 2500,
        "columns": [(x, 50) for x in range(WIDTH // 2, WIDTH, 300)],
        "pigs": [(WIDTH // 2, 100), (WIDTH // 2 + 220, 100)],
    },
    {
        "min_score": 0,
        "columns": [(x, 50) for x in range(WIDTH // 2, WIDTH, 250)],
        "pigs": [
            (WIDTH // 2 - 150, 100),
            (WIDTH // 2 + 100, 100),
            (WIDTH // 2 + 350, 100),
        ],
    },
]


class App(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture("assets/img/background3.png")
        self.slingshot = arcade.load_texture(SLINGSHOT_IMG)
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)

        floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        floor_shape = pymunk.Segment(floor_body, [0, 15], [WIDTH, 15], 0.0)
        floor_shape.friction = 10
        self.space.add(floor_body, floor_shape)

        bounds_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        left_wall = pymunk.Segment(
            bounds_body,
            [BOUNDS_MARGIN, 15],
            [BOUNDS_MARGIN, HEIGHT - BOUNDS_MARGIN],
            0.0,
        )
        right_wall = pymunk.Segment(
            bounds_body,
            [WIDTH - BOUNDS_MARGIN, 15],
            [WIDTH - BOUNDS_MARGIN, HEIGHT - BOUNDS_MARGIN],
            0.0,
        )
        top_wall = pymunk.Segment(
            bounds_body,
            [BOUNDS_MARGIN, HEIGHT - BOUNDS_MARGIN],
            [WIDTH - BOUNDS_MARGIN, HEIGHT - BOUNDS_MARGIN],
            0.0,
        )
        for wall in (left_wall, right_wall, top_wall):
            wall.friction = 10
            wall.elasticity = 0.8
        self.space.add(bounds_body, left_wall, right_wall, top_wall)

        self.sprites = arcade.SpriteList()
        self.birds = arcade.SpriteList()
        self.world = arcade.SpriteList()
        self.score = 0
        self.level_score = 0
        self.level_index = 0
        self._load_level(self.level_index)

        self.start_point = Point2D()
        self.end_point = Point2D()
        self.distance = 0
        self.draw_line = False
        self.is_dragging = False

        self.handler = self.space.add_default_collision_handler()
        self.handler.post_solve = self.collision_handler

    def collision_handler(self, arbiter, space, data):
        impulse_norm = arbiter.total_impulse.length
        if impulse_norm < 100:
            return True
        logger.debug(impulse_norm)
        if impulse_norm > 1200:
            for obj in list(self.world):
                if obj.shape in arbiter.shapes:
                    self._add_score(obj)
                    self._remove_sprite(obj)
        return True

    def _add_score(self, obj):
        for obj_type, points in SCORE_VALUES.items():
            if isinstance(obj, obj_type):
                self.score += points
                self.level_score += points
                return

    def _remove_sprite(self, sprite):
        items_to_remove = []
        if hasattr(sprite, "shape") and sprite.shape in self.space.shapes:
            items_to_remove.append(sprite.shape)
        if hasattr(sprite, "body") and sprite.body in self.space.bodies:
            items_to_remove.append(sprite.body)
        if items_to_remove:
            self.space.remove(*items_to_remove)
        sprite.remove_from_sprite_lists()

    def _clear_dynamic_objects(self):
        for sprite in list(self.birds) + list(self.world):
            self._remove_sprite(sprite)
        self.sprites = arcade.SpriteList()
        self.birds = arcade.SpriteList()
        self.world = arcade.SpriteList()

    def _load_level(self, level_index: int):
        self._clear_dynamic_objects()
        level = LEVELS[level_index]

        for x, y in level["columns"]:
            column = Column(x, y, self.space)
            self.sprites.append(column)
            self.world.append(column)

        for x, y in level["pigs"]:
            pig = Pig(x, y, self.space)
            self.sprites.append(pig)
            self.world.append(pig)

        self.level_score = 0
        self.start_point = Point2D()
        self.end_point = Point2D()
        self.draw_line = False
        self.is_dragging = False

    def _check_level_progress(self):
        if self.level_index >= len(LEVELS) - 1:
            return
        target = LEVELS[self.level_index]["min_score"]
        if self.level_score >= target:
            self.level_index += 1
            self._load_level(self.level_index)

    def _get_flying_bird(self):
        """Retorna el primer pájaro especial en vuelo con habilidad disponible, o None."""
        for bird in self.birds:
            if isinstance(bird, (YellowBird, BlueBird)):
                if isinstance(bird, YellowBird) and not bird.ability_used:
                    return bird
                if isinstance(bird, BlueBird) and not bird.ability_used:
                    return bird
        return None

    def on_update(self, delta_time: float):
        self.space.step(1 / 60.0)
        self.sprites.update(delta_time)
        self._check_level_progress()

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.start_point = Point2D(x, y)
            self.end_point = Point2D(x, y)
            self.draw_line = True
            self.is_dragging = False
            logger.debug(f"Start Point: {self.start_point}")

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons == arcade.MOUSE_BUTTON_LEFT:
            self.end_point = Point2D(x, y)
            dist = get_distance(self.start_point, self.end_point)
            if dist > MIN_DRAG_DISTANCE:
                self.is_dragging = True
            logger.debug(f"Dragging to: {self.end_point}")

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.draw_line = False

            if self.is_dragging:
                logger.debug(f"Launching from drag, end: {self.end_point}")
                impulse_vector = get_impulse_vector(self.start_point, self.end_point)

                bird_type = len(self.birds) % 3

                if bird_type == 1:
                    bird = YellowBird(impulse_vector, SLINGSHOT_X, SLINGSHOT_Y, self.space)
                elif bird_type == 2:
                    bird = BlueBird(impulse_vector, SLINGSHOT_X, SLINGSHOT_Y, self.space)
                else:
                    bird = Bird("assets/img/red-bird3.png", impulse_vector, SLINGSHOT_X, SLINGSHOT_Y, self.space)

                self.sprites.append(bird)
                self.birds.append(bird)

            else:
                flying_bird = self._get_flying_bird()
                if flying_bird is not None:
                    if isinstance(flying_bird, YellowBird):
                        logger.debug("YellowBird: activando turbo")
                        flying_bird.activate_power()

                    elif isinstance(flying_bird, BlueBird):
                        logger.debug("BlueBird: dividiendo en 3")
                        new_birds = flying_bird.split()
                        for nb in new_birds:
                            self.sprites.append(nb)
                            self.birds.append(nb)
                        self._remove_sprite(flying_bird)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background, arcade.LRBT(0, WIDTH, 0, HEIGHT))
        self.sprites.draw()
        arcade.draw_text(
            f"Score: {self.score}",
            10,
            HEIGHT - 25,
            arcade.color.BLACK,
            16,
        )
        arcade.draw_text(
            f"Level: {self.level_index + 1}/{len(LEVELS)}",
            10,
            HEIGHT - 50,
            arcade.color.BLACK,
            16,
        )
        if self.level_index < len(LEVELS) - 1:
            target = LEVELS[self.level_index]["min_score"]
            arcade.draw_text(
                f"Level goal: {self.level_score}/{target}",
                10,
                HEIGHT - 75,
                arcade.color.BLACK,
                16,
            )
        arcade.draw_texture_rect(
            self.slingshot,
            arcade.LRBT(
                SLINGSHOT_X - 60, SLINGSHOT_X + 60,
                SLINGSHOT_Y - 80, SLINGSHOT_Y + 80,
            )
        )
        if self.draw_line:
            arcade.draw_line(
                SLINGSHOT_X, SLINGSHOT_Y, 
                self.end_point.x, self.end_point.y,    
                arcade.color.BLACK, 3
            )
            


def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    game = App()
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()