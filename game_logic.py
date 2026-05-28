import math
from dataclasses import dataclass


@dataclass
class ImpulseVector:
    angle: float
    impulse: float


@dataclass
class Point2D:
    x: float = 0
    y: float = 0


def get_angle_radians(point_a: Point2D, point_b: Point2D) -> float:
    dx = point_b.x - point_a.x
    dy = point_b.y - point_a.y

    return math.atan2(dy, dx)


def get_distance(point_a: Point2D, point_b: Point2D) -> float:
    dx = point_b.x - point_a.x
    dy = point_b.y - point_a.y

    return math.sqrt(dx * dx + dy * dy)


def get_impulse_vector(start_point: Point2D, end_point: Point2D) -> ImpulseVector:
    angle = get_angle_radians(end_point, start_point)

    impulse = get_distance(start_point, end_point)

    return ImpulseVector(angle, impulse)