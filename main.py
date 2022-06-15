from __future__ import annotations

import pygame
from pygame.event import Event
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface
from pygame.time import Clock
from pygame.math import Vector2
import numpy as np

from rect_utils import interp_inside_rect, rect_from_endpoints, rect_from_center_size, rect_inside_rect
from slider import VerticalSlider

BACKGROUND_COLOR = (0, 0, 0)
BORDER_COLOR = (255, 255, 255)
HISTORY_LINE_COLOR = (0, 0, 255)
HISTORY_PTS_COLOR = (0, 255, 255)
BALL_COLOR = (0, 0, 255)
BALL_VEL_COLOR = (0, 255, 0)
TARGET_COLOR = (255, 255, 0)
TEXT_COLOR = (255, 255, 255)

print("numpy: ", np.version.version)
pygame.init()

screen_size = (1000, 750)
screen: Surface = pygame.display.set_mode(screen_size)
pygame.display.set_caption("Seeker")

clock: Clock = pygame.time.Clock()

font_file: str = "fonts/Noto_Sans_Mono/NotoSansMono-VariableFont_wdth,wght.ttf"
font: Font = Font(font_file, 12)

ui_area: Rect = rect_from_endpoints(Vector2(0, 0), Vector2(screen_size[0] * .25, screen_size[1] * .75))

kp_slider = VerticalSlider(font, "Position\nGain",
                           rect_inside_rect(ui_area, Vector2(1 / 3, .54), .02, .85),
                           0, 0, 125)

kv_slider = VerticalSlider(font, "Velocity\nGain",
                           rect_inside_rect(ui_area, Vector2(2 / 3, .54), .02, .85),
                           0, 0, 125)

eig_area: Rect = rect_from_endpoints(Vector2(0, screen_size[1] * .75), Vector2(screen_size[0] * .25, screen_size[1]))

arena: Rect = rect_from_endpoints(Vector2(screen_size[0] / 4, 0), Vector2(screen_size))
arena_topleft: Vector2 = Vector2(arena.topleft)
arena_bottomright: Vector2 = Vector2(arena.bottomright)

ball_pos: Vector2 = Vector2(arena.center)
ball_vel: Vector2 = Vector2(0, 0)
ball_radius: float = 20

ball_history_length: int = 240  # iterations
ball_history: list[Vector2] = [ball_pos.copy()]

targets: list[Vector2] = [
    interp_inside_rect(arena, u, v)
    for (u, v) in [(.25, .25), (.75, .25), (.75, .75), (.25, .75)]
]

k_p: float = 50.0
k_v: float = 3.0

kp_slider.value = k_p
kv_slider.value = k_v

target_num: int = 0
target_change_period: float = 1.0  # seconds - how often to change the target
target_pos: Vector2 = targets[target_num]
last_target_change: float = 0.0

ui_mouse_target = None

current_t: float = 0.0
delta_t: float = 0.0
running: bool = True
while running:
    # elapsed_ticks: int = pygame.time.get_ticks()

    event: Event
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # print(f"{elapsed_ticks:7} Quit event.")
            running = False

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # print(f"{elapsed_ticks:7} Escape pressed.")
            running = False

        elif event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION}:
            response: str
            if ui_mouse_target is None:
                for item in [kp_slider, kv_slider]:
                    response = item.process_event(event)
                    if response == "LockMouse":
                        ui_mouse_target = item
                        break
            else:
                response = ui_mouse_target.process_event(event)
                if response == "ReleaseMouse":
                    ui_mouse_target = None

    # Update the target
    if last_target_change + target_change_period <= current_t:
        target_num = (target_num + 1) % len(targets)
        target_pos = targets[target_num]
        last_target_change = current_t

    # Read the sliders
    k_p = kp_slider.value
    k_v = kv_slider.value

    # Build discrete state space matrices
    matrix_a = np.array([
        [1, delta_t],
        [0, 1]
    ])
    matrix_b = np.array([
        [.5 * delta_t * delta_t],
        [delta_t]
    ])
    matrix_k = np.array([
        [k_p, k_v]
    ])
    eig_system = np.linalg.eig(matrix_a - matrix_b * matrix_k)[0]

    # Update the ball
    if delta_t > 0:
        # Apply the control law for the ball's acceleration
        ball_acc: Vector2 = k_p * (target_pos - ball_pos) - k_v * ball_vel

        # Update the ball position and velocity
        ball_pos += (ball_vel + 0.5 * ball_acc * delta_t) * delta_t
        ball_vel += ball_acc * delta_t

        # Bounce off the walls
        if ball_pos.x - ball_radius < arena.left + 1 and ball_vel.x < 0:
            ball_pos.x = arena.left + ball_radius + 1
            ball_vel.x *= -0.1
        if ball_pos.y - ball_radius < arena.top + 1 and ball_vel.y < 0:
            ball_pos.y = arena.top + ball_radius + 1
            ball_vel.y *= -0.1
        if ball_pos.x + ball_radius > arena.right - 1 and ball_vel.x > 0:
            ball_pos.x = arena.right - ball_radius - 1
            ball_vel.x *= -0.1
        if ball_pos.y + ball_radius > arena.bottom - 1 and ball_vel.y > 0:
            ball_pos.y = arena.bottom - ball_radius - 1
            ball_vel.y *= -0.1

        # record the ball's history
        ball_history.append(ball_pos.copy())
        ball_history = ball_history[-ball_history_length:]

    # Start drawing
    screen.fill(BACKGROUND_COLOR)

    # Draw the borders for the ui area and the arena
    pygame.draw.rect(screen, BORDER_COLOR, ui_area, 1)
    pygame.draw.rect(screen, BORDER_COLOR, arena, 1)
    pygame.draw.rect(screen, BORDER_COLOR, eig_area, 1)

    # Draw sliders
    kp_slider.draw(screen)
    kv_slider.draw(screen)

    # Draw eigenvalues
    axis_size = min(eig_area.width, eig_area.height) * .4
    axis_scale = axis_size * .9
    axis_center: Vector2 = Vector2(eig_area.center)
    axis_left: Vector2 = axis_center + Vector2(-axis_size, 0)
    axis_right: Vector2 = axis_center + Vector2(axis_size, 0)
    axis_top: Vector2 = axis_center + Vector2(0, -axis_size)
    axis_bottom: Vector2 = axis_center + Vector2(0, axis_size)
    pygame.draw.line(screen, (255, 255, 255), axis_left, axis_right)
    pygame.draw.line(screen, (255, 255, 255), axis_top, axis_bottom)
    pygame.draw.circle(screen, (127, 127, 127), axis_center, axis_scale, 1)
    for (e_num, e) in enumerate(eig_system):
        e_vec: Vector2 = Vector2(e.real, e.imag)
        e_pt: Vector2 = e_vec * axis_scale + axis_center
        eig_pt_color = (0, 255, 0) if abs(e) < 1 else (255, 0, 0)
        pygame.draw.circle(screen, eig_pt_color, e_pt, 3)
        eig_text_color = TEXT_COLOR if abs(e) < 1 else (255, 0, 0)
        text_surf = font.render(f"{e_vec.x:.3f} + {e_vec.y:.3f} i", True, eig_text_color)
        screen.blit(text_surf, Vector2(eig_area.topleft) + Vector2(0, e_num * font.get_linesize()))

    # Draw the ball's history
    if len(ball_history) >= 2:
        pygame.draw.lines(screen, HISTORY_LINE_COLOR, False, ball_history)
    for b in ball_history:
        pygame.draw.circle(screen, HISTORY_PTS_COLOR, center=b, radius=2)

    # Draw the ball and its velocity
    pygame.draw.circle(screen, BALL_COLOR, ball_pos, ball_radius)
    pygame.draw.line(screen, BALL_VEL_COLOR, ball_pos, (ball_pos + ball_vel / 10).xy)

    # Draw the target
    pygame.draw.line(screen, TARGET_COLOR, (target_pos.x - 10, target_pos.y), (target_pos.x + 10, target_pos.y))
    pygame.draw.line(screen, TARGET_COLOR, (target_pos.x, target_pos.y - 10), (target_pos.x, target_pos.y + 10))

    # Display the current simulation time
    text_surf = font.render(f"t = {current_t:.3f}", True, TEXT_COLOR)
    screen.blit(text_surf, (0, 0))

    # Display the current fps
    fps: float = clock.get_fps()
    text_surf = font.render(f"{fps:.1f} fps", True, TEXT_COLOR)
    screen.blit(text_surf, (0, 12))

    # Finish drawing
    pygame.display.flip()

    clock.tick(60)
    delta_t = 1 / 60  # Decouple the simulation from the actual frame rate
    current_t += delta_t

pygame.quit()
