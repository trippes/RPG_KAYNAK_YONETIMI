"""Data contract for content-defined local maps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class MapDefinitionError(ValueError):
    """Raised when a local map definition is structurally invalid."""


def _coordinate(value: Any, field_name: str) -> tuple[int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise MapDefinitionError(f"{field_name} must be a two-item coordinate.")
    x, y = value
    if type(x) is not int or type(y) is not int:
        raise MapDefinitionError(f"{field_name} coordinates must be integers.")
    return x, y


@dataclass(frozen=True)
class MapSize:
    width: int
    height: int

    def __post_init__(self) -> None:
        if type(self.width) is not int or self.width <= 0:
            raise MapDefinitionError("Map width must be a positive integer.")
        if type(self.height) is not int or self.height <= 0:
            raise MapDefinitionError("Map height must be a positive integer.")


@dataclass(frozen=True)
class TerrainDefinition:
    default_tile: str

    def __post_init__(self) -> None:
        if not isinstance(self.default_tile, str) or not self.default_tile.strip():
            raise MapDefinitionError("terrain.default_tile must be a non-empty string.")


@dataclass(frozen=True)
class MapFeature:
    feature_id: str
    feature_type: str
    tiles: tuple[tuple[int, int], ...] = ()
    walkable: bool = True


@dataclass(frozen=True)
class LandmarkDefinition:
    landmark_id: str
    name: str
    position: tuple[int, int]
    landmark_type: str = "generic"
    visual_type: str = "generic"
    walkable: bool = True
    interactable: bool = False
    activities: tuple[str, ...] = ()
    resource_node_id: str | None = None
    description: str = ""


@dataclass(frozen=True)
class MapTransition:
    transition_id: str
    from_tiles: tuple[tuple[int, int], ...]
    target_map_id: str
    target_tiles: tuple[tuple[int, int], ...] = ()
    direction: str | None = None


@dataclass(frozen=True)
class MapDefinition:
    schema_version: int
    map_id: str
    name: str
    description: str
    size: MapSize
    terrain: TerrainDefinition
    blocked_tiles: tuple[tuple[int, int], ...] = ()
    features: tuple[MapFeature, ...] = ()
    landmarks: tuple[LandmarkDefinition, ...] = ()
    transitions: tuple[MapTransition, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MapDefinition":
        if not isinstance(data, dict):
            raise MapDefinitionError("Map definition must be an object.")
        if data.get("schema_version") != 1:
            raise MapDefinitionError("Unsupported map definition schema version.")
        required = {"schema_version", "map_id", "name", "description", "size", "terrain"}
        missing = sorted(required - data.keys())
        if missing:
            raise MapDefinitionError("Map definition is missing fields: " + ", ".join(missing))
        size_data, terrain_data = data["size"], data["terrain"]
        if not isinstance(size_data, dict) or not isinstance(terrain_data, dict):
            raise MapDefinitionError("size and terrain must be objects.")
        definition = cls(
            schema_version=1,
            map_id=_string(data["map_id"], "map_id"),
            name=_string(data["name"], "name"),
            description=_string(data["description"], "description", allow_empty=True),
            size=MapSize(size_data.get("width"), size_data.get("height")),
            terrain=TerrainDefinition(terrain_data.get("default_tile")),
            blocked_tiles=tuple(_coordinate(item, "blocked_tiles item") for item in data.get("blocked_tiles", ())),
            features=tuple(_feature(item) for item in data.get("features", ())),
            landmarks=tuple(_landmark(item) for item in data.get("landmarks", ())),
            transitions=tuple(_transition(item) for item in data.get("transitions", ())),
        )
        definition._validate_coordinates()
        definition._validate_unique_ids()
        return definition

    def _validate_coordinates(self) -> None:
        coordinates = list(self.blocked_tiles)
        for feature in self.features:
            coordinates.extend(feature.tiles)
        for landmark in self.landmarks:
            coordinates.append(landmark.position)
        for transition in self.transitions:
            coordinates.extend(transition.from_tiles)
        for x, y in coordinates:
            if not (0 <= x < self.size.width and 0 <= y < self.size.height):
                raise MapDefinitionError(
                    f"Coordinate ({x}, {y}) is outside map '{self.map_id}' bounds."
                )

    def _validate_unique_ids(self) -> None:
        for label, values in (
            ("feature", [item.feature_id for item in self.features]),
            ("landmark", [item.landmark_id for item in self.landmarks]),
            ("transition", [item.transition_id for item in self.transitions]),
        ):
            if len(values) != len(set(values)):
                raise MapDefinitionError(f"Duplicate {label} IDs are not allowed.")


def _string(value: Any, field_name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise MapDefinitionError(f"{field_name} must be a {'string' if allow_empty else 'non-empty string'}.")
    return value


def _feature(data: Any) -> MapFeature:
    if not isinstance(data, dict):
        raise MapDefinitionError("Feature must be an object.")
    return MapFeature(
        _string(data.get("id"), "feature.id"),
        _string(data.get("type"), "feature.type"),
        tuple(_coordinate(item, "feature tile") for item in data.get("tiles", ())),
        _bool(data.get("walkable", True), "feature.walkable"),
    )


def _landmark(data: Any) -> LandmarkDefinition:
    if not isinstance(data, dict):
        raise MapDefinitionError("Landmark must be an object.")
    resource_node_id = data.get("resource_node_id")
    if resource_node_id is not None:
        resource_node_id = _string(resource_node_id, "landmark.resource_node_id")
    return LandmarkDefinition(
        _string(data.get("id"), "landmark.id"),
        _string(data.get("name"), "landmark.name"),
        _coordinate(data.get("position"), "landmark.position"),
        _string(data.get("type", "generic"), "landmark.type"),
        _string(data.get("visual_type", "generic"), "landmark.visual_type"),
        _bool(data.get("walkable", True), "landmark.walkable"),
        _bool(data.get("interactable", False), "landmark.interactable"),
        tuple(_string(item, "landmark activity") for item in data.get("activities", ())),
        resource_node_id,
        _string(data.get("description", ""), "landmark.description", allow_empty=True),
    )


def _transition(data: Any) -> MapTransition:
    if not isinstance(data, dict):
        raise MapDefinitionError("Transition must be an object.")
    from_tiles = tuple(_coordinate(item, "transition.from_tiles item") for item in data.get("from_tiles", ()))
    if not from_tiles:
        raise MapDefinitionError("transition.from_tiles must not be empty.")
    target_tiles = tuple(_coordinate(item, "transition.target_tiles item") for item in data.get("target_tiles", ()))
    if not target_tiles:
        raise MapDefinitionError("transition.target_tiles must not be empty.")
    direction = data.get("direction")
    if direction is not None:
        direction = _string(direction, "transition.direction")
        if direction not in {"north", "south", "east", "west"}:
            raise MapDefinitionError("transition.direction must be north, south, east, or west.")
    return MapTransition(
        _string(data.get("id"), "transition.id"),
        from_tiles,
        _string(data.get("target_map_id"), "transition.target_map_id"),
        target_tiles,
        direction,
    )


def _bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise MapDefinitionError(f"{field_name} must be a boolean.")
    return value
