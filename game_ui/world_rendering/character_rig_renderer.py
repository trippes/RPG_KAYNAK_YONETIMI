"""Articulated Pygame character renderer for the shared character rig."""

from __future__ import annotations

import math
from collections.abc import Mapping


class CharacterRigRenderer:
    """Draw a solid, joint-driven character while preserving its foot anchor.

    The renderer owns presentation only. It never changes the runtime position,
    skeleton definition, or supplied pose mapping.
    """

    DIRECTIONS = (
        "east", "south_east", "south", "south_west",
        "west", "north_west", "north", "north_east",
    )

    _DIRECTION_PROJECTION = {
        "east": (1.0, 0.58),
        "south_east": (1.0, 0.82),
        "south": (1.0, 1.0),
        "south_west": (-1.0, 0.82),
        "west": (-1.0, 0.58),
        "north_west": (-1.0, 0.82),
        "north": (1.0, 1.0),
        "north_east": (1.0, 0.82),
    }

    DEFAULT_PALETTE = {
        "outline": (35, 29, 27),
        "skin": (194, 145, 105),
        "hair": (65, 43, 31),
        "tunic": (68, 112, 79),
        "trousers": (62, 66, 79),
        "boots": (85, 57, 39),
        "far_limb": (48, 75, 59),
        "near_limb": (82, 125, 87),
    }

    _LIMB_BONES = {
        "left_upper_arm": ("left_shoulder", "left_elbow", "arm"),
        "left_forearm": ("left_elbow", "left_hand", "arm"),
        "right_upper_arm": ("right_shoulder", "right_elbow", "arm"),
        "right_forearm": ("right_elbow", "right_hand", "arm"),
        "left_thigh": ("left_hip", "left_knee", "leg"),
        "left_shin": ("left_knee", "left_ankle", "leg"),
        "left_foot": ("left_ankle", "left_foot", "foot"),
        "right_thigh": ("right_hip", "right_knee", "leg"),
        "right_shin": ("right_knee", "right_ankle", "leg"),
        "right_foot": ("right_ankle", "right_foot", "foot"),
    }

    @classmethod
    def project_joint_positions(
        cls, skeleton, foot_position, world_scale, local_rotations=None, facing="south"
    ):
        """Project normalized rig joints into screen coordinates around the feet."""
        if facing not in cls._DIRECTION_PROJECTION:
            raise ValueError(f"Unsupported character facing direction: {facing!r}.")
        if (
            not isinstance(world_scale, (int, float))
            or isinstance(world_scale, bool)
            or not math.isfinite(world_scale)
            or world_scale <= 0
        ):
            raise ValueError("world_scale must be a finite positive number.")
        if len(foot_position) != 2 or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in foot_position
        ):
            raise ValueError("foot_position must contain two finite coordinates.")

        mirror_x, horizontal_scale = cls._DIRECTION_PROJECTION[facing]
        anchor_x, anchor_y = skeleton.ground_anchor
        positions = skeleton.joint_positions(local_rotations)
        scale = float(world_scale)
        foot_x, foot_y = float(foot_position[0]), float(foot_position[1])
        return {
            name: (
                foot_x + (point[0] - anchor_x) * scale * horizontal_scale * mirror_x,
                foot_y - (point[1] - anchor_y) * scale,
            )
            for name, point in positions.items()
        }

    def draw(
        self,
        renderer,
        skeleton,
        foot_position,
        world_scale,
        local_rotations=None,
        facing="south",
        palette=None,
    ):
        """Draw articulated body parts and return their projected joint positions."""
        positions = self.project_joint_positions(
            skeleton, foot_position, world_scale, local_rotations, facing
        )
        colors = dict(self.DEFAULT_PALETTE)
        if palette is not None:
            if not isinstance(palette, Mapping):
                raise ValueError("palette must be a mapping of color names to RGB values.")
            unknown = set(palette) - set(colors)
            if unknown:
                raise ValueError(f"Unknown character palette keys: {', '.join(sorted(unknown))}.")
            colors.update(palette)

        scale = float(world_scale)
        near_side = "right" if facing in {
            "east", "south_east", "south", "north_east"
        } else "left"
        far_side = "left" if near_side == "right" else "right"
        bone_by_name = {bone.name: bone for bone in skeleton.bones}

        # Far limbs sit behind the torso; near limbs are drawn over it.
        self._draw_limb_group(
            renderer, positions, bone_by_name, far_side, scale, colors, near=True
        )
        self._draw_torso(renderer, positions, scale, colors)
        self._draw_neck(renderer, positions, bone_by_name, scale, colors)
        self._draw_limb_group(
            renderer, positions, bone_by_name, near_side, scale, colors, near=False
        )
        self._draw_head(renderer, positions["head"], scale, colors)
        return positions

    def _draw_limb_group(
        self, renderer, positions, bone_by_name, side, scale, colors, near
    ):
        draw = renderer.pg.draw
        limb_color = colors["near_limb"] if near else colors["far_limb"]
        for suffix in ("upper_arm", "forearm", "thigh", "shin", "foot"):
            bone_name = f"{side}_{suffix}"
            bone = bone_by_name.get(bone_name)
            if bone is None:
                continue
            start_name, end_name, kind = self._LIMB_BONES[bone_name]
            color = colors["boots"] if kind == "foot" else (
                colors["trousers"] if kind == "leg" else limb_color
            )
            self._draw_segment(
                draw, positions[start_name], positions[end_name],
                max(2.0, bone.thickness * scale), color, colors["outline"],
            )
        # Hands and knees receive a small joint cap to avoid visible seams.
        for joint_name, radius_factor in (
            (f"{side}_hand", 0.043),
            (f"{side}_knee", 0.047),
            (f"{side}_ankle", 0.038),
        ):
            self._draw_joint(
                draw, positions[joint_name], max(2, round(scale * radius_factor)),
                colors["skin"] if joint_name.endswith("hand") else colors["trousers"],
                colors["outline"],
            )

    def _draw_torso(self, renderer, positions, scale, colors):
        draw = renderer.pg.draw
        points = [
            self._point(positions["left_shoulder"]),
            self._point(positions["right_shoulder"]),
            self._point(positions["right_hip"]),
            self._point(positions["left_hip"]),
        ]
        draw.polygon(renderer.surface, colors["tunic"], points)
        draw.polygon(
            renderer.surface, colors["outline"], points,
            max(1, round(scale * 0.018)),
        )
        # A narrow belt separates the tunic from the trousers.
        left_hip = positions["left_hip"]
        right_hip = positions["right_hip"]
        belt_y = round((left_hip[1] + right_hip[1]) * 0.5 - scale * 0.025)
        draw.line(
            renderer.surface, colors["outline"],
            (round(left_hip[0]), belt_y), (round(right_hip[0]), belt_y),
            max(2, round(scale * 0.035)),
        )

    def _draw_neck(self, renderer, positions, bone_by_name, scale, colors):
        bone = bone_by_name.get("chest_neck")
        if bone is not None:
            self._draw_segment(
                renderer.pg.draw, positions["chest"], positions["neck"],
                max(2.0, bone.thickness * scale),
                colors["skin"], colors["outline"],
            )

    def _draw_head(self, renderer, center, scale, colors):
        draw = renderer.pg.draw
        radius = max(4, round(scale * 0.105))
        self._draw_joint(draw, center, radius, colors["skin"], colors["outline"])
        hair_center = (round(center[0]), round(center[1] - radius * 0.48))
        self._draw_joint(
            draw, hair_center, max(2, round(radius * 0.78)),
            colors["hair"], colors["outline"],
        )

    @staticmethod
    def _draw_segment(draw, start, end, thickness, fill, outline):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        radius = max(1.0, thickness * 0.5)
        if length <= 1e-6:
            CharacterRigRenderer._draw_joint(
                draw, start, max(1, round(radius)), fill, outline
            )
            return
        perpendicular = (-dy / length * radius, dx / length * radius)
        points = [
            CharacterRigRenderer._point((start[0] + perpendicular[0], start[1] + perpendicular[1])),
            CharacterRigRenderer._point((end[0] + perpendicular[0], end[1] + perpendicular[1])),
            CharacterRigRenderer._point((end[0] - perpendicular[0], end[1] - perpendicular[1])),
            CharacterRigRenderer._point((start[0] - perpendicular[0], start[1] - perpendicular[1])),
        ]
        draw.polygon(None, fill, points)
        draw.polygon(None, outline, points, max(1, round(radius * 0.22)))
        cap_radius = max(1, round(radius))
        CharacterRigRenderer._draw_joint(draw, start, cap_radius, fill, outline)
        CharacterRigRenderer._draw_joint(draw, end, cap_radius, fill, outline)

    @staticmethod
    def _draw_joint(draw, center, radius, fill, outline):
        point = CharacterRigRenderer._point(center)
        draw.circle(None, outline, point, radius + 1)
        draw.circle(None, fill, point, radius)

    @staticmethod
    def _point(position):
        return (round(position[0]), round(position[1]))
