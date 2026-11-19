"""Read-only view of a world's current cell data."""

from hex_world_lab.world.cell import HexCellData
from hex_world_lab.world.identity import CellAddress, WorldId
from hex_world_lab.world.map_definition import UnknownCellError
from hex_world_lab.world.map_registry import MapNotLoadedError, MapRegistry, UnknownMapError
from hex_world_lab.world.runtime import HexWorldRuntime


class HexWorldView:
    """Resolve immutable base cell data plus sparse runtime overrides."""

    __slots__ = ("_world_id", "_map_registry", "_runtime")

    def __init__(
        self,
        world_id: WorldId,
        map_registry: MapRegistry,
        runtime: HexWorldRuntime,
    ) -> None:
        if not isinstance(world_id, WorldId):
            raise TypeError("world_id must be a WorldId")
        if not isinstance(map_registry, MapRegistry):
            raise TypeError("map_registry must be a MapRegistry")
        if not isinstance(runtime, HexWorldRuntime):
            raise TypeError("runtime must be a HexWorldRuntime")
        if map_registry.world_id != world_id or runtime.world_id != world_id:
            raise ValueError("view dependencies must belong to the same world")
        self._world_id = world_id
        self._map_registry = map_registry
        self._runtime = runtime

    @property
    def world_id(self) -> WorldId:
        return self._world_id

    def get_cell(self, address: CellAddress) -> HexCellData | None:
        """Return current cell data, or None only when the cell is absent."""
        self._validate_address(address)
        if self._map_registry.get_registration(address.map_id) is None:
            raise UnknownMapError(f"map '{address.map_id.value}' is not registered")
        definition = self._map_registry.get_map(address.map_id)
        if definition is None:
            raise MapNotLoadedError(f"map '{address.map_id.value}' is not loaded")
        base = definition.get_cell_data(address.coord)
        if base is None:
            return None

        override = self._runtime.get_override(address)
        if override is None:
            return base
        return HexCellData(
            terrain_id=(
                base.terrain_id if override.terrain_id is None else override.terrain_id
            ),
            is_walkable=(
                base.is_walkable
                if override.is_walkable is None
                else override.is_walkable
            ),
            has_obstacle=(
                base.has_obstacle
                if override.has_obstacle is None
                else override.has_obstacle
            ),
            metadata=base.metadata,
        )

    def require_cell(self, address: CellAddress) -> HexCellData:
        """Return current cell data or raise UnknownCellError when absent."""
        cell = self.get_cell(address)
        if cell is None:
            raise UnknownCellError(address.world_id, address.map_id, address.coord)
        return cell

    def _validate_address(self, address: CellAddress) -> None:
        if not isinstance(address, CellAddress):
            raise TypeError("address must be a CellAddress")
        if address.world_id != self._world_id:
            raise ValueError(
                f"address belongs to world '{address.world_id.value}', "
                f"not '{self._world_id.value}'"
            )
