"""Draw a layered tree skin attached to normalized articulated skeleton joints."""
from __future__ import annotations

import math


class TreeRigRenderer:
    """Compose atlas components around stable pivots and animate them from TreeSkeleton."""

    def __init__(self):
        self._scaled_cache = {}

    def draw(self, renderer, atlas, skeleton, world_anchor, tree_size, zoom, elapsed):
        layers = getattr(atlas, "rig_layers", ())
        if not layers:
            return False
        width = max(1.0, float(tree_size[0]) * float(zoom))
        height = max(1.0, float(tree_size[1]) * float(zoom))
        left = float(world_anchor[0]) - width * skeleton.ground_anchor[0]
        top = float(world_anchor[1]) - height * skeleton.ground_anchor[1]
        for layer in sorted(layers, key=lambda item: item["order"]):
            component_id = layer["component_id"]
            source = atlas.get(component_id)
            if source is None:
                continue
            normalized_size = layer["size"]
            target_size = (
                max(1, round(width * normalized_size[0])),
                max(1, round(height * normalized_size[1])),
            )
            cache_key = (component_id, target_size)
            scaled = self._scaled_cache.get(cache_key)
            if scaled is None:
                scaled = renderer.pg.transform.smoothscale(source, target_size)
                self._scaled_cache[cache_key] = scaled
            pivot = (
                target_size[0] * layer["pivot"][0],
                target_size[1] * layer["pivot"][1],
            )
            target = (
                left + width * layer["anchor"][0],
                top + height * layer["anchor"][1],
            )
            offset, angle = self._motion_pose(
                skeleton, layer.get("motion", {}), elapsed, width, height
            )
            target = (target[0] + offset[0], target[1] + offset[1])
            angle += float(layer.get("rotation", 0.0))
            image = scaled
            if abs(angle) > 0.01:
                image = renderer.pg.transform.rotate(scaled, angle)
                radians = math.radians(angle)
                center_to_pivot = (
                    pivot[0] - target_size[0] * 0.5,
                    pivot[1] - target_size[1] * 0.5,
                )
                rotated_center_to_pivot = (
                    math.cos(radians) * center_to_pivot[0]
                    + math.sin(radians) * center_to_pivot[1],
                    -math.sin(radians) * center_to_pivot[0]
                    + math.cos(radians) * center_to_pivot[1],
                )
                destination = (
                    round(target[0] - rotated_center_to_pivot[0] - image.get_width() * 0.5),
                    round(target[1] - rotated_center_to_pivot[1] - image.get_height() * 0.5),
                )
            else:
                destination = (
                    round(target[0] - pivot[0]),
                    round(target[1] - pivot[1]),
                )
            renderer.surface.blit(image, destination)
        return True

    @staticmethod
    def _motion_pose(skeleton, motion, elapsed, width, height):
        kind = motion.get("kind", "none")
        index = motion.get("index")
        weight = float(motion.get("weight", 1.0))
        if kind == "trunk":
            start, end = skeleton.animated_trunk_points(elapsed)
            base = skeleton.trunk
            angle = TreeRigRenderer._angle_delta(base.start, base.end, start, end)
            return (0.0, 0.0), angle * weight
        if kind == "branch":
            if index is None or not 0 <= index < len(skeleton.branches):
                return (0.0, 0.0), 0.0
            start, end = skeleton.animated_branch_points(index, elapsed)
            base = skeleton.branches[index]
            angle = TreeRigRenderer._angle_delta(base.start, base.end, start, end)
            return (0.0, 0.0), angle * weight
        if kind == "leaf":
            if index is None or not 0 <= index < len(skeleton.leaf_clusters):
                return (0.0, 0.0), 0.0
            cluster = skeleton.leaf_clusters[index]
            animated = skeleton.animated_leaf_anchor(index, elapsed)
            return (
                (animated[0] - cluster.anchor[0]) * width * weight,
                (animated[1] - cluster.anchor[1]) * height * weight,
            ), math.sin(elapsed * skeleton.sway_frequency + cluster.phase) * 2.0 * weight
        return (0.0, 0.0), 0.0

    @staticmethod
    def _angle_delta(base_start, base_end, current_start, current_end):
        base_angle = math.atan2(
            base_end[1] - base_start[1], base_end[0] - base_start[0]
        )
        current_angle = math.atan2(
            current_end[1] - current_start[1],
            current_end[0] - current_start[0],
        )
        return -math.degrees(current_angle - base_angle)
