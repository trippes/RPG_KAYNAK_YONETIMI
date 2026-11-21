"""Lightweight directional fantasy actor sprites generated from vector primitives."""
from __future__ import annotations

import math

from game_ui.assets.animation import Animation
from .character_animation import CharacterAnimator


_PALETTES = {
    "player": {
        "cloth": (53, 82, 108), "cloth_shadow": (27, 45, 67),
        "armor": (142, 151, 154), "armor_light": (205, 190, 145),
        "trim": (190, 147, 70), "skin": (196, 148, 111),
        "hair": (66, 43, 31), "boots": (61, 43, 34),
        "weapon": (205, 211, 208), "shield": (116, 71, 43),
    },
    "npc": {
        "cloth": (111, 93, 58), "cloth_shadow": (59, 54, 36),
        "armor": (104, 119, 91), "armor_light": (166, 157, 111),
        "trim": (171, 127, 62), "skin": (190, 143, 105),
        "hair": (73, 48, 31), "boots": (62, 44, 32),
        "weapon": (176, 181, 164), "shield": (79, 92, 59),
    },
}


class ProceduralCharacterSpriteFactory:
    """Build cached 8-direction idle/walk/run sprite animations."""

    DIRECTIONS = (
        "south", "south_west", "west", "north_west",
        "north", "north_east", "east", "south_east",
    )
    STATE_CONFIG = {
        "idle": (2, 0.34),
        # Eight frames give the leg cycle smaller, smoother pose changes.
        # The complete walk/run cycles remain close to the intended cadence.
        "walk": (8, 0.075),
        "run": (8, 0.055),
    }

    def __init__(self):
        self._frame_cache = {}

    def create_animator(self, pygame_module, *, palette="player") -> CharacterAnimator:
        if palette not in _PALETTES:
            raise ValueError(f"Unknown character sprite palette: {palette}")
        colors = _PALETTES[palette]
        animations = {}
        for direction in self.DIRECTIONS:
            states = {}
            for state, (frame_count, duration) in self.STATE_CONFIG.items():
                frames = tuple(
                    self._get_frame(
                        pygame_module, palette, colors,
                        direction, state, index, frame_count,
                    )
                    for index in range(frame_count)
                )
                states[state] = Animation(frames, duration, loop=True)
            animations[direction] = states
        return CharacterAnimator(animations)

    def _get_frame(
        self, pg, palette, colors, direction, state, frame_index, frame_count,
    ):
        key = (id(pg), palette, direction, state, frame_index)
        frame = self._frame_cache.get(key)
        if frame is None:
            frame = self._draw_frame(
                pg, colors, direction, state, frame_index, frame_count,
            )
            self._frame_cache[key] = frame
        return frame

    @staticmethod
    def _draw_frame(pg, colors, direction, state, frame_index, frame_count):
        surface = pg.Surface((48, 64), pg.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        phase = (frame_index / frame_count) * math.tau
        is_walking = state in {"walk", "run"}
        stride_amplitude = 0.0
        lift_amplitude = 0.0
        if state == "walk":
            stride_amplitude, lift_amplitude = 4.5, 2.4
        elif state == "run":
            stride_amplitude, lift_amplitude = 6.5, 4.2

        side = -1 if direction in {"west", "north_west", "south_west"} else 1
        back = direction in {"north", "north_east", "north_west"}
        profile = direction in {
            "east", "west", "north_east", "south_east",
            "north_west", "south_west",
        }
        center_x = 24 + (side * 2 if profile else 0)

        pg.draw.ellipse(surface, (12, 18, 17, 95), (10, 55, 28, 7))

        # Rear cloak and articulated legs are drawn before the torso.
        pg.draw.polygon(
            surface, colors["cloth_shadow"],
            ((center_x - 9, 27), (center_x + 8, 27),
             (center_x + 11, 48), (center_x - 10, 49)),
        )

        leg_poses = []
        for leg_phase in (phase, phase + math.pi):
            swing = math.sin(leg_phase) * stride_amplitude
            lift = max(0.0, math.cos(leg_phase)) * lift_amplitude
            leg_poses.append((swing, lift))

        # Draw the far leg first so the near leg naturally overlaps it.
        for leg_index in (1, 0):
            swing, lift = leg_poses[leg_index]
            hip_x = center_x + (-4 if leg_index == 0 else 4)
            knee_x = round(hip_x + swing * 0.48)
            knee_y = round(51 - lift * 0.45)
            foot_x = round(hip_x + swing)
            foot_y = round(57 - lift)
            pg.draw.line(
                surface, colors["boots"],
                (hip_x, 44), (knee_x, knee_y), 5,
            )
            pg.draw.line(
                surface, colors["boots"],
                (knee_x, knee_y), (foot_x, foot_y), 4,
            )
            pg.draw.circle(surface, colors["cloth_shadow"], (knee_x, knee_y), 2)
            pg.draw.ellipse(
                surface, colors["boots"],
                (foot_x - 5, foot_y - 2, 10, 5),
            )

        # Arms counter-swing against the legs while the torso stays grounded.
        arm_swing = round(
            math.sin(phase + math.pi) * stride_amplitude * 0.62
        ) if is_walking else 0
        pg.draw.line(
            surface, colors["cloth_shadow"],
            (center_x - 8, 30), (center_x - 13 - arm_swing, 43), 5,
        )
        pg.draw.line(
            surface, colors["cloth_shadow"],
            (center_x + 8, 30), (center_x + 13 + arm_swing, 42), 5,
        )
        pg.draw.circle(
            surface, colors["skin"],
            (round(center_x - 13 - arm_swing), 44), 3,
        )
        pg.draw.circle(
            surface, colors["skin"],
            (round(center_x + 13 + arm_swing), 43), 3,
        )

        torso = (
            (center_x - 9, 25), (center_x + 9, 25),
            (center_x + 8, 44), (center_x - 8, 44),
        )
        pg.draw.polygon(surface, colors["armor"], torso)
        pg.draw.polygon(surface, colors["cloth"], (
            (center_x - 6, 28), (center_x + 6, 28),
            (center_x + 5, 42), (center_x - 5, 42),
        ))
        pg.draw.line(surface, colors["trim"], (center_x - 6, 39), (center_x + 6, 39), 2)
        pg.draw.circle(surface, colors["armor_light"], (center_x - 8, 28), 4)
        pg.draw.circle(surface, colors["armor_light"], (center_x + 8, 28), 4)

        # A small shield and weapon make the silhouette read as an adventurer.
        pg.draw.polygon(
            surface, colors["shield"],
            ((center_x - 14, 32), (center_x - 8, 34),
             (center_x - 9, 45), (center_x - 15, 42)),
        )
        pg.draw.line(
            surface, colors["weapon"],
            (center_x + 14, 43), (center_x + 17, 23), 2,
        )
        pg.draw.circle(surface, colors["trim"], (center_x + 17, 22), 2)

        # Head, hair and a low-profile helm.
        head_x = center_x + (side * 2 if profile else 0)
        pg.draw.circle(surface, colors["skin"], (head_x, 17), 8)
        pg.draw.arc(surface, colors["hair"], (head_x - 8, 8, 16, 15), 3.14, 6.28, 3)
        pg.draw.polygon(
            surface, colors["armor_light"],
            ((head_x - 8, 14), (head_x, 7), (head_x + 8, 14),
             (head_x + 6, 17), (head_x - 6, 17)),
        )
        if not back:
            eye_x = head_x + (2 if side > 0 else -2)
            pg.draw.circle(surface, (34, 29, 25), (eye_x, 18), 1)
        else:
            pg.draw.arc(surface, colors["hair"], (head_x - 6, 13, 12, 9), 0, 3.14, 2)

        # Tiny highlights provide readable armor planes at low resolution.
        pg.draw.line(
            surface, colors["armor_light"],
            (center_x - 5, 29), (center_x - 2, 35), 1,
        )
        pg.draw.line(
            surface, colors["trim"],
            (center_x - 4, 46), (center_x + 4, 46), 1,
        )
        return surface
