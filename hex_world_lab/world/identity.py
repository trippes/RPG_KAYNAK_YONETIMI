"""Immutable identifiers and globally scoped hex-cell addresses."""

from dataclasses import dataclass

from hex_world_lab.geometry import AxialCoord


def _validate_identifier(value: object, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty or whitespace-only")


@dataclass(frozen=True, slots=True)
class WorldId:
    """Stable identifier for a world."""

    value: str

    def __post_init__(self) -> None:
        _validate_identifier(self.value, "world id")


@dataclass(frozen=True, slots=True)
class MapId:
    """Identifier for a map within a world."""

    value: str

    def __post_init__(self) -> None:
        _validate_identifier(self.value, "map id")


@dataclass(frozen=True, slots=True)
class CellAddress:
    """Address of one axial cell within a specific world and map."""

    world_id: WorldId
    map_id: MapId
    coord: AxialCoord

    def __post_init__(self) -> None:
        if not isinstance(self.world_id, WorldId):
            raise TypeError("world_id must be a WorldId")
        if not isinstance(self.map_id, MapId):
            raise TypeError("map_id must be a MapId")
        if not isinstance(self.coord, AxialCoord):
            raise TypeError("coord must be an AxialCoord")
