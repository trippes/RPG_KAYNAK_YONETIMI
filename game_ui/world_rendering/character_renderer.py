"""Procedural and sprite-backed character drawing with a shared foot anchor."""
from __future__ import annotations
import math

class HexCharacterRenderer:
    """Draw a placeholder humanoid or an authored sprite anchored at its feet."""

    @staticmethod
    def draw_sprite(renderer, sprite, foot_position, world_scale, anchor=(0.5, 1.0)):
        """Draw a sprite with normalized pivot; runtime position is never mutated."""
        if len(anchor) != 2 or any(not 0 <= value <= 1 for value in anchor):
            raise ValueError("anchor must contain two normalized coordinates.")
        scale = max(1, round(float(world_scale)))
        source_width, source_height = sprite.get_size()
        width = max(1, round(source_width * scale / 64))
        height = max(1, round(source_height * scale / 64))
        image = sprite
        if image.get_size() != (width, height):
            image = renderer.pg.transform.smoothscale(image, (width, height))
        x = round(foot_position[0] - width * anchor[0])
        y = round(foot_position[1] - height * anchor[1])
        renderer.surface.blit(image, (x, y))

    @staticmethod
    def draw(renderer, foot_position, world_scale, elapsed_seconds=0.0, moving=False):
        pg = renderer.pg
        x, y = foot_position
        scale = max(14.0, float(world_scale))
        foot_y = y + scale * 0.28
        phase = float(elapsed_seconds) * 12.0 if moving else 0.0
        stride = math.sin(phase) * scale * 0.12
        line_width = max(2, round(scale * 0.075))
        pg.draw.circle(renderer.surface, (27, 34, 28),
                       (round(x), round(foot_y)), max(4, round(scale * 0.22)))
        hip = (round(x), round(foot_y - scale * 0.34))
        left_foot = (round(x - scale * 0.12 + stride), round(foot_y))
        right_foot = (round(x + scale * 0.12 - stride), round(foot_y))
        pg.draw.line(renderer.surface, (48, 43, 39), hip, left_foot, line_width)
        pg.draw.line(renderer.surface, (48, 43, 39), hip, right_foot, line_width)
        pg.draw.circle(renderer.surface, (83, 61, 45), left_foot, max(2, line_width))
        pg.draw.circle(renderer.surface, (83, 61, 45), right_foot, max(2, line_width))
        shoulder_y = foot_y - scale * 0.68
        shoulder_left = (round(x - scale * 0.13), round(shoulder_y))
        shoulder_right = (round(x + scale * 0.13), round(shoulder_y))
        hand_left = (round(x - scale * 0.23 - stride * 0.45), round(foot_y - scale * 0.34))
        hand_right = (round(x + scale * 0.23 + stride * 0.45), round(foot_y - scale * 0.34))
        pg.draw.line(renderer.surface, (119, 83, 55), shoulder_left, hand_left, line_width)
        pg.draw.line(renderer.surface, (119, 83, 55), shoulder_right, hand_right, line_width)
        torso = (
            (round(x - scale * 0.15), round(foot_y - scale * 0.70)),
            (round(x + scale * 0.15), round(foot_y - scale * 0.70)),
            (round(x + scale * 0.12), round(foot_y - scale * 0.34)),
            (round(x - scale * 0.12), round(foot_y - scale * 0.34)),
        )
        pg.draw.polygon(renderer.surface, (73, 111, 82), torso)
        pg.draw.polygon(renderer.surface, (35, 57, 43), torso, max(1, line_width // 2))
        head = (round(x), round(foot_y - scale * 0.82))
        pg.draw.circle(renderer.surface, (196, 151, 111), head, max(3, round(scale * 0.12)))
        pg.draw.circle(renderer.surface, (83, 57, 42),
                       (head[0], head[1] - max(1, round(scale * 0.035))),
                       max(3, round(scale * 0.125)), max(1, line_width // 2))
