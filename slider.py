from __future__ import annotations

import pygame
from pygame.event import Event
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface, SurfaceType
from pygame.math import Vector2

from rect_utils import interp_inside_rect, rect_from_center_size

SLIDER_RAIL_COLOR = (127, 127, 0)
SLIDER_KNOB_COLOR = (255, 255, 0)
SLIDER_TEXT_COLOR = (255, 255, 255)


class VerticalSlider:
    rail: Rect
    knob: Rect
    min_value: float
    max_value: float
    _value: float
    _ratio: float
    font: Font
    label: str

    def __init__(self, font: Font, label: str, rail: Rect, value: float = 0, min_value: float = 0,
                 max_value: float = 100):
        self.font = font
        self.label = label
        self.rail = rail
        self.min_value = float(min_value)
        self.max_value = float(max_value)
        self.value = float(value)
        self.dragging = False

    def _calculate_knob(self):
        center = interp_inside_rect(self.rail, 0.5, 1 - self._ratio)
        self.knob = rect_from_center_size(center, self.rail.width * 5, self.rail.height / 50)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = min(self.max_value, max(self.min_value, value))
        self._ratio = (value - self.min_value) / (self.max_value - self.min_value)
        self._calculate_knob()

    @property
    def ratio(self):
        return self._ratio

    @ratio.setter
    def ratio(self, u):
        self._ratio = min(1.0, max(0.0, float(u)))
        self._value = self.min_value + self._ratio * (self.max_value - self.min_value)
        self._calculate_knob()

    def draw(self, surface: Surface):
        pygame.draw.rect(surface, SLIDER_RAIL_COLOR, self.rail, 1)
        pygame.draw.rect(surface, SLIDER_KNOB_COLOR, self.knob)
        text_surf: Surface = self.font.render(f"{self._value:.1f}", True, SLIDER_TEXT_COLOR)
        surface.blit(text_surf, Vector2(self.rail.midbottom) - Vector2(text_surf.get_width() / 2, 0))
        splitlines = self.label.splitlines(False)
        for (row_num, text) in enumerate(splitlines):
            text_surf = self.font.render(text, True, SLIDER_TEXT_COLOR)
            delta_x: float = text_surf.get_width() / 2
            delta_y: float = self.font.get_linesize() * (len(splitlines) - row_num)
            surface.blit(text_surf, Vector2(self.rail.midtop) - Vector2(delta_x, delta_y))

    def process_event(self, event: Event) -> str:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.knob.collidepoint(event.pos):
                self.dragging = True
                self.drag_start_delta = Vector2(event.pos) - Vector2(self.knob.center)
                return "LockMouse"
            elif self.rail.collidepoint(event.pos):
                self.ratio = (self.rail.bottom - event.pos[1]) / self.rail.height
                return ""
        elif self.dragging and event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            adjusted_pos: Vector2 = Vector2(event.pos) - self.drag_start_delta
            self.ratio = (self.rail.bottom - adjusted_pos.y) / self.rail.height
            self.dragging = False
            return "ReleaseMouse"
        elif self.dragging and event.type == pygame.MOUSEMOTION:
            if event.buttons[0]:
                adjusted_pos: Vector2 = Vector2(event.pos) - self.drag_start_delta
                self.ratio = (self.rail.bottom - adjusted_pos.y) / self.rail.height
                return ""
            else:
                self.dragging = False
                return "ReleaseMouse"
