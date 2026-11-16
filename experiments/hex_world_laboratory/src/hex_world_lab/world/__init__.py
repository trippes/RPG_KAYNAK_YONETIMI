"""World identity, map definitions, runtime, view, and world aggregate."""

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
from .movement_context import MovementWorldContext
from .movement_resolution import MovementCellResolution
from .runtime import HexWorldRuntime, RuntimeCellOverride
from .world_view import HexWorldView
from .world import HexWorld

__all__ = [
    "CellAddress",
    "DuplicateMapError",
    "HexCellData",
    "HexMapDefinition",
    "HexWorld",
    "HexWorldRuntime",
    "HexWorldView",
    "MapAlreadyLoadedError",
    "MapId",
    "MapNameMismatchError",
    "MapNotLoadedError",
    "MapRegistration",
    "MapRegistry",
    "MapRegistryError",
    "MapWorldMismatchError",
    "MovementCellResolution",
    "MovementWorldContext",
    "RuntimeCellOverride",
    "UnknownCellError",
    "UnknownMapError",
    "WorldId",
]
