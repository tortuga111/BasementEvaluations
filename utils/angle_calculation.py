import math

from shapely.geometry import Point


def angle_between_two_points(pt1: Point, pt2: Point) -> float:
    x_diff = pt2.x - pt1.x
    y_diff = pt2.y - pt1.y
    return math.degrees(math.atan2(y_diff, x_diff))
