"""Runtime extraction of independently authored tree sprites from a transparent atlas."""
from __future__ import annotations

import json
from pathlib import Path


class TreeAtlasError(ValueError):
    """Raised when a tree atlas manifest is malformed."""


class TreePartsAtlas:
    """Loads atlas regions as independent, cached Pygame surfaces."""

    def __init__(self, source, components, rig_layers=()):
        self.source = source
        self.components = dict(components)
        self.rig_layers = tuple(rig_layers)

    @classmethod
    def load(cls, pygame_module, atlas_path, manifest_path):
        atlas_path = Path(atlas_path)
        manifest_path = Path(manifest_path)
        with manifest_path.open("r", encoding="utf-8") as stream:
            manifest = json.load(stream)
        if manifest.get("schema_version") != 1:
            raise TreeAtlasError("Unsupported tree atlas schema version.")
        image = pygame_module.image.load(str(atlas_path)).convert_alpha()
        expected_size = tuple(manifest.get("source_size", ()))
        if expected_size and image.get_size() != expected_size:
            raise TreeAtlasError(
                f"Atlas size {image.get_size()} does not match manifest {expected_size}."
            )
        components = {}
        for entry in manifest.get("components", ()):
            component_id = entry.get("id")
            rect = entry.get("rect")
            if not isinstance(component_id, str) or not component_id:
                raise TreeAtlasError("Every atlas component needs a non-empty id.")
            if component_id in components:
                raise TreeAtlasError(f"Duplicate tree component id: {component_id}.")
            if (
                not isinstance(rect, list) or len(rect) != 4
                or any(type(value) is not int for value in rect)
            ):
                raise TreeAtlasError(f"Invalid rectangle for tree component {component_id}.")
            x, y, width, height = rect
            if x < 0 or y < 0 or width <= 0 or height <= 0:
                raise TreeAtlasError(f"Invalid rectangle for tree component {component_id}.")
            if x + width > image.get_width() or y + height > image.get_height():
                raise TreeAtlasError(f"Tree component {component_id} exceeds atlas bounds.")
            components[component_id] = {
                "type": entry.get("type", "unknown"),
                "rect": tuple(rect),
                "surface": image.subsurface(tuple(rect)).copy(),
            }
        if not components:
            raise TreeAtlasError("Tree atlas manifest contains no components.")
        rig_layers = manifest.get("rig_layers", ())
        if not isinstance(rig_layers, list):
            raise TreeAtlasError("Tree atlas rig_layers must be a list.")
        validated_layers = []
        for layer in rig_layers:
            if not isinstance(layer, dict):
                raise TreeAtlasError("Every tree rig layer must be an object.")
            component_id = layer.get("component_id")
            if component_id not in components:
                raise TreeAtlasError(
                    f"Tree rig layer references missing component: {component_id}."
                )
            for field in ("anchor", "pivot", "size"):
                value = layer.get(field)
                if (
                    not isinstance(value, list) or len(value) != 2
                    or any(
                        isinstance(number, bool)
                        or not isinstance(number, (int, float))
                        or not 0.0 <= number <= 1.0
                        for number in value
                    )
                ):
                    raise TreeAtlasError(
                        f"Tree rig layer {component_id} has invalid {field}."
                    )
            if any(number <= 0 for number in layer["size"]):
                raise TreeAtlasError(
                    f"Tree rig layer {component_id} must have positive size."
                )
            order = layer.get("order", 0)
            if isinstance(order, bool) or not isinstance(order, int):
                raise TreeAtlasError(
                    f"Tree rig layer {component_id} has invalid order."
                )
            motion = layer.get("motion", {"kind": "none"})
            if not isinstance(motion, dict) or motion.get(
                "kind", "none"
            ) not in {"none", "trunk", "branch", "leaf"}:
                raise TreeAtlasError(
                    f"Tree rig layer {component_id} has invalid motion."
                )
            motion_index = motion.get("index")
            if motion.get("kind") in {"branch", "leaf"} and (
                isinstance(motion_index, bool)
                or not isinstance(motion_index, int)
                or motion_index < 0
            ):
                raise TreeAtlasError(
                    f"Tree rig layer {component_id} has invalid motion index."
                )
            motion_weight = motion.get("weight", 1.0)
            if (
                isinstance(motion_weight, bool)
                or not isinstance(motion_weight, (int, float))
                or not 0.0 <= motion_weight <= 1.0
            ):
                raise TreeAtlasError(
                    f"Tree rig layer {component_id} has invalid motion weight."
                )
            validated_layers.append(dict(layer))
        return cls(image, components, validated_layers)

    def get(self, component_id):
        entry = self.components.get(component_id)
        return None if entry is None else entry["surface"]

    def component(self, component_id):
        return self.components.get(component_id)

    def by_type(self, component_type):
        return {
            key: value["surface"]
            for key, value in self.components.items()
            if value["type"] == component_type
        }

    @property
    def component_ids(self):
        return tuple(self.components)

    def __len__(self):
        return len(self.components)
