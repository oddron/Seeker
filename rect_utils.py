from __future__ import annotations

from pygame.math import Vector2
from pygame.rect import Rect


def rect_from_endpoints(topleft: Vector2, bottomright: Vector2) -> Rect:
    return Rect(topleft, bottomright - topleft)


def rect_from_center_size(center: Vector2, width: float, height: float) -> Rect:
    size = Vector2(float(width), float(height))
    return Rect(center - size / 2, size)


def interp_inside_rect(r: Rect, u: float, v: float) -> Vector2:
    return Vector2(r.left * (1 - u) + r.right * u, r.top * (1 - v) + r.bottom * v)


def rect_inside_rect(r: Rect, uv_center: Vector2, width: float, height: float) -> Rect:
    return rect_from_center_size(interp_inside_rect(r, *uv_center), width * r.width, height * r.height)
