"""Runtime placement of dynamic objects on local world maps."""
from dataclasses import dataclass, replace
from world.local_map import LocalMapDefinition

@dataclass(frozen=True)
class WorldObjectPlacement:
    object_id: str
    world_id: str
    location_id: str
    x: int
    y: int
    width: int = 1
    height: int = 1
    blocks_movement: bool = True
    layer: int = 0
    tags: tuple[str, ...] = ()

    def __post_init__(self):
        for name in ("object_id", "world_id", "location_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        for name in ("x", "y", "width", "height", "layer"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer.")
        if self.x < 0 or self.y < 0 or self.width <= 0 or self.height <= 0:
            raise ValueError("Coordinates must be non-negative and footprint dimensions positive.")
        if self.layer < 0 or not isinstance(self.blocks_movement, bool):
            raise ValueError("Invalid layer or movement-blocking flag.")
        tags = tuple(self.tags)
        if any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            raise ValueError("Placement tags must be non-empty strings.")
        if len(tags) != len(set(tags)):
            raise ValueError("Placement tags must be unique.")
        object.__setattr__(self, "tags", tuple(sorted(tags)))

    @property
    def occupied_tiles(self):
        return tuple((x, y) for y in range(self.y, self.y + self.height)
                     for x in range(self.x, self.x + self.width))

class WorldObjectPlacementError(ValueError):
    """Invalid or conflicting dynamic world-object placement."""

class WorldObjectPlacementRegistry:
    """Single-writer registry enforcing unique placement and tile occupancy."""
    def __init__(self):
        self._maps = {}
        self._placements = {}

    def register_local_map(self, definition):
        if not isinstance(definition, LocalMapDefinition):
            raise TypeError("definition must be LocalMapDefinition.")
        key = (definition.world_id, definition.location_id)
        if key in self._maps:
            raise WorldObjectPlacementError(f"Local map already registered: {key}")
        self._maps[key] = definition

    def has_local_map(self, world_id, location_id):
        return (world_id, location_id) in self._maps

    def place(self, placement):
        if not isinstance(placement, WorldObjectPlacement):
            raise TypeError("placement must be WorldObjectPlacement.")
        if placement.object_id in self._placements:
            raise WorldObjectPlacementError(f"Object already placed: {placement.object_id}")
        self._validate_candidate(placement)
        self._placements[placement.object_id] = placement
        return placement

    def move(self, object_id, x, y):
        current = self._require(object_id)
        candidate = replace(current, x=x, y=y)
        self._validate_candidate(candidate, replacing=object_id)
        self._placements[object_id] = candidate
        return candidate

    def transfer(self, object_id, location_id, x, y):
        current = self._require(object_id)
        candidate = replace(current, location_id=location_id, x=x, y=y)
        self._validate_candidate(candidate, replacing=object_id)
        self._placements[object_id] = candidate
        return candidate

    def remove(self, object_id):
        placement = self._placements.pop(object_id, None)
        if placement is None:
            raise KeyError(f"World object placement not found: {object_id}")
        return placement

    def get(self, object_id):
        return self._placements.get(object_id)

    def for_location(self, world_id, location_id):
        return tuple(self._placements[key] for key in sorted(self._placements)
                     if self._placements[key].world_id == world_id
                     and self._placements[key].location_id == location_id)

    def at(self, world_id, location_id, x, y):
        return tuple(item for item in self.for_location(world_id, location_id)
                     if (x, y) in item.occupied_tiles)

    def blocked_tiles(self, world_id, location_id):
        return frozenset(tile for item in self.for_location(world_id, location_id)
                         if item.blocks_movement for tile in item.occupied_tiles)

    def placements(self):
        return tuple(self._placements[key] for key in sorted(self._placements))

    def validate(self):
        for item in self.placements():
            self._validate_candidate(item, replacing=item.object_id)

    def _validate_candidate(self, candidate, replacing=None):
        local_map = self._maps.get((candidate.world_id, candidate.location_id))
        if local_map is None:
            raise WorldObjectPlacementError(
                f"Local map not registered: {candidate.world_id}/{candidate.location_id}"
            )
        if candidate.x + candidate.width > local_map.width or candidate.y + candidate.height > local_map.height:
            raise WorldObjectPlacementError(f"Object footprint outside local map: {candidate.object_id}")
        if not candidate.blocks_movement:
            return
        tiles = set(candidate.occupied_tiles)
        for other in self._placements.values():
            if other.object_id == replacing or not other.blocks_movement:
                continue
            if (other.world_id, other.location_id) != (candidate.world_id, candidate.location_id):
                continue
            if tiles.intersection(other.occupied_tiles):
                raise WorldObjectPlacementError(f"Blocking placement overlaps: {other.object_id}")

    def _require(self, object_id):
        placement = self._placements.get(object_id)
        if placement is None:
            raise KeyError(f"World object placement not found: {object_id}")
        return placement
