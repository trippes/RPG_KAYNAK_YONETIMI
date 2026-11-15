"""World identity, map definitions, registry, and world aggregate."""

from .cell import HexCellData
from .identity import CellAddress, MapId, WorldId
from .map_definition import HexMapDefinition, UnknownCellError
from .map_registry import (
    DuplicateMapError,
    MapAlreadyLoadedError,
    MapNameMismatchError,
    MapNotLoadedError,
    MapRegistration,
    MapRegistry,
    MapRegistryError,
    MapWorldMismatchError,
    UnknownMapError,
)
from .world import HexWorld

__all__ = [
    "CellAddress",
    "DuplicateMapError",
    "HexCellData",
    "HexMapDefinition",
    "HexWorld",
    "MapAlreadyLoadedError",
    "MapId",
    "MapNameMismatchError",
    "MapNotLoadedError",
    "MapRegistration",
    "MapRegistry",
    "MapRegistryError",
    "MapWorldMismatchError",
    "UnknownCellError",
    "UnknownMapError",
    "WorldId",
]
