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
        # A strict side projection collapses the character's shoulder span
        # to a single vertical line. Retain a small profile width so the torso,
        # shoulder caps and limbs still read as a body rather than a stick.
        apparent_lateral_x = lateral_x
        if abs(apparent_lateral_x) < 0.28:
            apparent_lateral_x = math.copysign(0.28, lateral_y or 1.0)

        projected = {
            name: (
                foot_x + (point[0] - anchor_x) * scale * apparent_lateral_x,
                foot_y - (point[1] - anchor_y) * scale
                + (point[0] - anchor_x) * scale * lateral_y * cls.DEPTH_PROJECTION,
            )
            for name, point in positions.items()
        }

        # The shoulder girdle is a single visual crossbar. The raw depth
        # projection can otherwise make one shoulder appear noticeably higher
        # than the other in diagonal views. Keep both arm roots on one screen
        # line; their horizontal separation and all elbow/hand articulation
        # remain direction- and pose-driven.
        shoulder_y = (
            projected["left_shoulder"][1] + projected["right_shoulder"][1]
        ) * 0.5
        for name in ("left_shoulder", "right_shoulder"):
            projected[name] = (projected[name][0], shoulder_y)

        return projected

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

        for suffix in ("upper_arm", "forearm", "thigh", "shin"):
            bone_name = f"{side}_{suffix}"
            bone = bone_by_name.get(bone_name)
            if bone is None:
                continue
            start_name, end_name, kind = self._LIMB_BONES[bone_name]
            color = colors["trousers"] if kind == "leg" else limb_color
            self._draw_segment(
                draw, renderer.surface, positions[start_name], positions[end_name],
                bone.thickness * scale, color, colors["outline"],
            )

        # Hands are small tapered palms with a thumb hint, not circular joint
        # markers. Their orientation follows the forearm-to-wrist direction.
        self._draw_hand(
            draw, renderer.surface, positions[f"{side}_elbow"],
            positions[f"{side}_hand"], scale, colors
        )

        # Boots overlap the ankle joint and extend forward from the foot pivot.
        foot_bone = bone_by_name.get(f"{side}_foot")
        if foot_bone is not None:
            self._draw_foot(
                draw, renderer.surface, positions[f"{side}_ankle"],
                positions[f"{side}_foot"], scale, colors
            )

        # Elbows and knees are blended into their adjoining shapes. Only a
        # restrained seam mark remains at the knee; no large ball-joint circles.
        self._draw_joint(
            draw, renderer.surface, positions[f"{side}_knee"],
            max(1, round(scale * 0.018)), colors["trousers"], colors["outline"],
        )

    def _draw_hand(self, draw, surface, elbow, hand, scale, colors):
        dx, dy = hand[0] - elbow[0], hand[1] - elbow[1]
        length = max(1.0, math.hypot(dx, dy))
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        cx, cy = hand
        palm_length = scale * 0.035
        palm_width = scale * 0.025
        points = [
            self._point((cx - ux * palm_length + px * palm_width,
                         cy - uy * palm_length + py * palm_width)),
            self._point((cx + ux * palm_length * 0.55 + px * palm_width * 0.72,
                         cy + uy * palm_length * 0.55 + py * palm_width * 0.72)),
            self._point((cx + ux * palm_length * 0.72 - px * palm_width * 0.72,
                         cy + uy * palm_length * 0.72 - py * palm_width * 0.72)),
            self._point((cx - ux * palm_length - px * palm_width,
                         cy - uy * palm_length - py * palm_width)),
        ]
        draw.polygon(surface, colors["skin"], points)
        draw.polygon(surface, colors["outline"], points, max(1, round(scale * 0.006)))

    def _draw_foot(self, draw, surface, ankle, foot, scale, colors):
        dx, dy = foot[0] - ankle[0], foot[1] - ankle[1]
        length = max(1.0, math.hypot(dx, dy))
        ux, uy = dx / length, dy / length
        # The rig's foot offset is short; extend the toe along its local axis
        # to give the boot a readable sole and toe instead of a tiny endpoint.
        px, py = -uy, ux
        heel_x, heel_y = ankle
        toe_x = foot[0] + ux * scale * 0.055
        toe_y = foot[1] + uy * scale * 0.055
        half_width = scale * 0.027
        points = [
            self._point((heel_x - px * half_width * 0.72,
                         heel_y - py * half_width * 0.72)),
            self._point((toe_x - px * half_width,
                         toe_y - py * half_width)),
            self._point((toe_x + px * half_width,
                         toe_y + py * half_width)),
            self._point((heel_x + px * half_width * 0.72,
                         heel_y + py * half_width * 0.72)),
        ]
        draw.polygon(surface, colors["boots"], points)
        draw.polygon(surface, colors["outline"], points, max(1, round(scale * 0.007)))

    def _draw_torso(self, renderer, positions, scale, colors):
        draw = renderer.pg.draw
        left_shoulder = positions["left_shoulder"]
        right_shoulder = positions["right_shoulder"]
        left_hip = positions["left_hip"]
        right_hip = positions["right_hip"]
        chest = positions["chest"]
        spine = positions["spine"]

        shoulder_mid = (
            (left_shoulder[0] + right_shoulder[0]) * 0.5,
            (left_shoulder[1] + right_shoulder[1]) * 0.5,
        )
        hip_mid = (
            (left_hip[0] + right_hip[0]) * 0.5,
            (left_hip[1] + right_hip[1]) * 0.5,
        )

        # A softer six-point tunic silhouette: rounded shoulder line, fuller
        # chest, inward waist and a modestly flared hem. The upper edge overlaps
        # the arm roots so sleeves appear attached to the torso.
        points = [
            self._point((left_shoulder[0] - scale * 0.018,
                         left_shoulder[1] + scale * 0.035)),
            self._point((shoulder_mid[0] - scale * 0.055,
                         shoulder_mid[1] + scale * 0.052)),
            self._point((chest[0], chest[1] + scale * 0.052)),
            self._point((shoulder_mid[0] + scale * 0.055,
                         shoulder_mid[1] + scale * 0.052)),
            self._point((right_shoulder[0] + scale * 0.018,
                         right_shoulder[1] + scale * 0.035)),
            self._point((right_hip[0] + scale * 0.018,
                         right_hip[1] - scale * 0.012)),
            self._point((hip_mid[0] + scale * 0.035,
                         hip_mid[1] - scale * 0.025)),
            self._point((hip_mid[0], hip_mid[1] - scale * 0.012)),
            self._point((hip_mid[0] - scale * 0.035,
                         hip_mid[1] - scale * 0.025)),
            self._point((left_hip[0] - scale * 0.018,
                         left_hip[1] - scale * 0.012)),
        ]
        draw.polygon(renderer.surface, colors["tunic"], points)
        draw.polygon(
            renderer.surface, colors["outline"], points,
            max(1, round(scale * 0.012)),
        )

        # Chest plane and side plane add volume without drawing a hard stripe
        # down the center of every facing direction.
        chest_plane = [
            self._point((left_shoulder[0] + scale * 0.012,
                         left_shoulder[1] + scale * 0.005)),
            self._point((chest[0] - scale * 0.035, chest[1] + scale * 0.025)),
            self._point((chest[0] + scale * 0.025, chest[1] + scale * 0.018)),
            self._point((right_shoulder[0] - scale * 0.012,
                         right_shoulder[1] + scale * 0.005)),
            self._point((hip_mid[0] + scale * 0.012, hip_mid[1] + scale * 0.015)),
            self._point((hip_mid[0] - scale * 0.018, hip_mid[1] + scale * 0.015)),
        ]
        draw.polygon(renderer.surface, colors["tunic_highlight"], chest_plane)

        side_plane = [
            self._point((right_shoulder[0], right_shoulder[1])),
            self._point((chest[0] + scale * 0.025, chest[1] - scale * 0.015)),
            self._point((hip_mid[0] + scale * 0.025, hip_mid[1] + scale * 0.005)),
            self._point((right_hip[0], right_hip[1])),
        ]
        draw.polygon(renderer.surface, colors["tunic_shadow"], side_plane)

        belt_y = round(hip_mid[1] + scale * 0.012)
        draw.line(
            renderer.surface, colors["outline"],
            (round(left_hip[0]), belt_y), (round(right_hip[0]), belt_y),
            max(1, round(scale * 0.012)),
        )

        # A small collar visually bridges neck and chest.
        collar = [
            self._point((chest[0] - scale * 0.052, chest[1] + scale * 0.035)),
            self._point((chest[0], chest[1] - scale * 0.005)),
            self._point((chest[0] + scale * 0.052, chest[1] + scale * 0.035)),
        ]
        draw.polygon(renderer.surface, colors["outline"], collar)

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
        width = scale * 0.105
        height = scale * 0.125
        head_points = [
            self._point((
                center[0] + math.cos(index * math.tau / 20) * width,
                center[1] + math.sin(index * math.tau / 20) * height,
            ))
            for index in range(20)
        ]
        draw.polygon(renderer.surface, colors["skin"], head_points)
        draw.polygon(
            renderer.surface, colors["outline"], head_points,
            max(1, round(scale * 0.010)),
        )

        # Hair cap follows the skull contour and leaves the lower face clear.
        hair_points = [
            self._point((
                center[0] + math.cos(math.pi + index * math.pi / 12) * width * 1.04,
                center[1] + math.sin(math.pi + index * math.pi / 12) * height * 1.04,
            ))
            for index in range(13)
        ]
        hair_points.extend([
            self._point((center[0] + width * 0.82, center[1] - height * 0.18)),
            self._point((center[0] + width * 0.45, center[1] - height * 0.43)),
            self._point((center[0], center[1] - height * 0.49)),
            self._point((center[0] - width * 0.48, center[1] - height * 0.40)),
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
