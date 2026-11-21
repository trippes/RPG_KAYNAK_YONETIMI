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
        "east": (0.0, 1.0),
        "south_east": (-math.sqrt(0.5), math.sqrt(0.5)),
        "south": (-1.0, 0.0),
        "south_west": (-math.sqrt(0.5), -math.sqrt(0.5)),
        "west": (0.0, -1.0),
        "north_west": (math.sqrt(0.5), -math.sqrt(0.5)),
        "north": (1.0, 0.0),
        "north_east": (math.sqrt(0.5), math.sqrt(0.5)),
    }
    DEPTH_PROJECTION = 0.45

    DEFAULT_PALETTE = {
        "outline": (35, 29, 27),
        "skin": (194, 145, 105),
        "hair": (65, 43, 31),
        "tunic": (68, 112, 79),
        "trousers": (62, 66, 79),
        "boots": (85, 57, 39),
        "far_limb": (48, 75, 59),
        "near_limb": (82, 125, 87),
        "tunic_shadow": (43, 79, 55),
        "tunic_highlight": (91, 137, 96),
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

        lateral_x, lateral_y = cls._DIRECTION_PROJECTION[facing]
        anchor_x, anchor_y = skeleton.ground_anchor
        positions = skeleton.joint_positions(local_rotations)
        scale = float(world_scale)
        foot_x, foot_y = float(foot_position[0]), float(foot_position[1])
        return {
            name: (
                foot_x + (point[0] - anchor_x) * scale * lateral_x,
                foot_y - (point[1] - anchor_y) * scale
                + (point[0] - anchor_x) * scale * lateral_y * cls.DEPTH_PROJECTION,
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
        _, lateral_y = self._DIRECTION_PROJECTION[facing]
        near_side = (
            "right" if lateral_y > 1e-8
            else "left" if lateral_y < -1e-8
            else "right" if facing == "south"
            else "left"
        )
        far_side = "left" if near_side == "right" else "right"
        bone_by_name = {bone.name: bone for bone in skeleton.bones}

        self._draw_limb_group(
            renderer, positions, bone_by_name, far_side, scale, colors, near=False
        )
        self._draw_torso(renderer, positions, scale, colors)
        self._draw_neck(renderer, positions, bone_by_name, scale, colors)
        self._draw_limb_group(
            renderer, positions, bone_by_name, near_side, scale, colors, near=True
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
            width = bone.thickness * scale
            self._draw_segment(
                draw, renderer.surface, positions[start_name], positions[end_name],
                width, color, colors["outline"],
            )

        # Small, color-matched joint transitions hide seams without reading as
        # large mechanical ball joints.
        for joint_name, radius_factor, fill in (
            (f"{side}_elbow", 0.027, limb_color),
            (f"{side}_hand", 0.034, colors["skin"]),
            (f"{side}_knee", 0.034, colors["trousers"]),
            (f"{side}_ankle", 0.026, colors["trousers"]),
        ):
            self._draw_joint(
                draw, renderer.surface, positions[joint_name],
                max(2, round(scale * radius_factor)), fill, colors["outline"],
            )

    def _draw_torso(self, renderer, positions, scale, colors):
        draw = renderer.pg.draw
        left_shoulder = positions["left_shoulder"]
        right_shoulder = positions["right_shoulder"]
        left_hip = positions["left_hip"]
        right_hip = positions["right_hip"]
        center_chest = positions["chest"]

        # A shaped tunic silhouette: broad shoulders, gently tapered waist,
        # and a slightly wider hem instead of a flat four-point rectangle.
        points = [
            self._point((left_shoulder[0] - scale * 0.018, left_shoulder[1] + scale * 0.018)),
            self._point((center_chest[0], center_chest[1] + scale * 0.045)),
            self._point((right_shoulder[0] + scale * 0.018, right_shoulder[1] + scale * 0.018)),
            self._point((right_hip[0] + scale * 0.025, right_hip[1] - scale * 0.025)),
            self._point((center_chest[0], (left_hip[1] + right_hip[1]) * 0.5 - scale * 0.035)),
            self._point((left_hip[0] - scale * 0.025, left_hip[1] - scale * 0.025)),
        ]
        draw.polygon(renderer.surface, colors["tunic"], points)
        draw.polygon(
            renderer.surface, colors["outline"], points,
            max(1, round(scale * 0.014)),
        )

        # Subtle side shading and a narrow belt give the tunic some volume.
        side_shadow = [
            self._point(right_shoulder),
            self._point((center_chest[0] + scale * 0.025, center_chest[1] - scale * 0.02)),
            self._point((right_hip[0] + scale * 0.012, right_hip[1] - scale * 0.02)),
            self._point((right_hip[0], right_hip[1] + scale * 0.015)),
        ]
        draw.polygon(renderer.surface, colors["tunic_shadow"], side_shadow)
        belt_y = round((left_hip[1] + right_hip[1]) * 0.5 - scale * 0.025)
        draw.line(
            renderer.surface, colors["outline"],
            (round(left_hip[0]), belt_y), (round(right_hip[0]), belt_y),
            max(2, round(scale * 0.025)),
        )
        draw.line(
            renderer.surface, colors["tunic_highlight"],
            self._point(left_shoulder), self._point(left_hip),
            max(1, round(scale * 0.012)),
        )

    def _draw_neck(self, renderer, positions, bone_by_name, scale, colors):
        bone = bone_by_name.get("chest_neck")
        if bone is not None:
            self._draw_segment(
                renderer.pg.draw, renderer.surface, positions["chest"], positions["neck"],
                max(scale * 0.075, bone.thickness * scale),
                colors["skin"], colors["outline"],
            )

    def _draw_head(self, renderer, center, scale, colors):
        draw = renderer.pg.draw
        # The head is an oval silhouette rather than a circular joint marker.
        width = scale * 0.105
        height = scale * 0.125
        head_points = [
            self._point((
                center[0] + math.cos(index * math.tau / 16) * width,
                center[1] + math.sin(index * math.tau / 16) * height,
            ))
            for index in range(16)
        ]
        draw.polygon(renderer.surface, colors["skin"], head_points)
        draw.polygon(
            renderer.surface, colors["outline"], head_points,
            max(1, round(scale * 0.012)),
        )

        # Hair follows the upper contour as a shaped cap, not a second ball.
        hair_points = [
            self._point((
                center[0] + math.cos(math.pi + index * math.pi / 10) * width * 1.02,
                center[1] + math.sin(math.pi + index * math.pi / 10) * height * 1.02,
            ))
            for index in range(11)
        ]
        hair_points.extend([
            self._point((center[0] + width * 0.78, center[1] - height * 0.22)),
            self._point((center[0], center[1] - height * 0.38)),
        ])
        draw.polygon(renderer.surface, colors["hair"], hair_points)

    @staticmethod
    def _draw_segment(draw, surface, start, end, thickness, fill, outline):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        radius = max(1.0, thickness * 0.5)
        if length <= 1e-6:
            CharacterRigRenderer._draw_joint(
                draw, surface, start, max(1, round(radius)), fill, outline
            )
            return

        perpendicular = (-dy / length, dx / length)
        start_radius = radius * 0.94
        end_radius = radius * 0.82
        points = [
            CharacterRigRenderer._point((start[0] + perpendicular[0] * start_radius,
                                          start[1] + perpendicular[1] * start_radius)),
            CharacterRigRenderer._point((end[0] + perpendicular[0] * end_radius,
                                          end[1] + perpendicular[1] * end_radius)),
            CharacterRigRenderer._point((end[0] - perpendicular[0] * end_radius,
                                          end[1] - perpendicular[1] * end_radius)),
            CharacterRigRenderer._point((start[0] - perpendicular[0] * start_radius,
                                          start[1] - perpendicular[1] * start_radius)),
        ]
        draw.polygon(surface, fill, points)
        draw.polygon(surface, outline, points, max(1, round(radius * 0.16)))
        # Only a small end cap remains visible; this softens the connection
        # without creating the oversized circular joints of the first preview.
        CharacterRigRenderer._draw_joint(
            draw, surface, end, max(1, round(end_radius * 0.68)), fill, outline
        )

    @staticmethod
    def _draw_joint(draw, surface, center, radius, fill, outline):
        point = CharacterRigRenderer._point(center)
        draw.circle(surface, outline, point, radius + 1)
        draw.circle(surface, fill, point, radius)

    @staticmethod
    def _point(position):
        return (round(position[0]), round(position[1]))
