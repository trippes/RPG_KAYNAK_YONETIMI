"""Validated bridge from continuous world positions to one loaded hex map."""

from hex_world_lab.geometry import AxialCoord, WorldPoint, world_to_axial
from hex_world_lab.world.identity import CellAddress, MapId, WorldId
from hex_world_lab.world.map_registry import MapNotLoadedError, UnknownMapError
from hex_world_lab.world.movement_resolution import MovementCellResolution
from hex_world_lab.world.world import HexWorld


class MovementWorldContext:
    """Resolve actor positions against one registered and loaded map.

    The context never loads maps and never changes actor positions. The map
    definition is the sole source of the hex layout used for conversion.
    """

    __slots__ = ("_world", "_map_id")

    def __init__(self, world: HexWorld, map_id: MapId) -> None:
        if not isinstance(world, HexWorld):
            raise TypeError("world must be a HexWorld")
        if not isinstance(map_id, MapId):
            raise TypeError("map_id must be a MapId")
        self._world = world
        self._map_id = map_id
        self._require_loaded_map()

    @property
    def world_id(self) -> WorldId:
        """World identity for this context."""
        return self._world.world_id

    @property
    def map_id(self) -> MapId:
        """The single map addressed by this context."""
        return self._map_id

    def resolve_position(
        self,
        position: WorldPoint,
        previous_cell: AxialCoord | None = None,
    ) -> MovementCellResolution:
        """Resolve a continuous point and read its current cell data.

        The previous cell is used only by the canonical geometry transform's
        exact-boundary tie-break rule. Missing map cells yield None cell data.
        """
        if not isinstance(position, WorldPoint):
            raise TypeError("position must be a WorldPoint")
        if previous_cell is not None and not isinstance(previous_cell, AxialCoord):
            raise TypeError("previous_cell must be an AxialCoord or None")

        definition = self._require_loaded_map()
        coord = world_to_axial(position, definition.layout, previous_cell)
        address = CellAddress(self._world.world_id, self._map_id, coord)
        cell_data = self._world.view.get_cell(address)
        return MovementCellResolution(
            world_id=self._world.world_id,
            map_id=self._map_id,
            coord=coord,
            address=address,
            cell_data=cell_data,
        )

    def _require_loaded_map(self):
        registry = self._world.map_registry
        if registry.get_registration(self._map_id) is None:
            raise UnknownMapError(f"map '{self._map_id.value}' is not registered")
        definition = registry.get_map(self._map_id)
        if definition is None:
            raise MapNotLoadedError(f"map '{self._map_id.value}' is not loaded")
        return definition
