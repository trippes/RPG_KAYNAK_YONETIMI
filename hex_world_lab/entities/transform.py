"""World-scoped entity locations and continuous transforms."""
from dataclasses import dataclass
import math
from hex_world_lab.geometry import AxialCoord, HexLayout, WorldPoint, axial_to_world, world_to_axial
from hex_world_lab.world.identity import CellAddress, MapId, WorldId
@dataclass(frozen=True, slots=True)
class EntityLocation:
    world_id: WorldId
    map_id: MapId
    position: WorldPoint
    def __post_init__(self) -> None:
        if not isinstance(self.world_id, WorldId): raise TypeError("world_id must be a WorldId")
        if not isinstance(self.map_id, MapId): raise TypeError("map_id must be a MapId")
        if not isinstance(self.position, WorldPoint): raise TypeError("position must be a WorldPoint")
@dataclass(frozen=True, slots=True)
class EntityTransform:
    location: EntityLocation
    rotation_radians: float = 0.0
    def __post_init__(self) -> None:
        if not isinstance(self.location, EntityLocation): raise TypeError("location must be an EntityLocation")
        if isinstance(self.rotation_radians, bool) or not isinstance(self.rotation_radians, (int, float)):
            raise TypeError("rotation_radians must be a real number")
        if not math.isfinite(self.rotation_radians): raise ValueError("rotation_radians must be finite")
@dataclass(frozen=True, slots=True)
class CellPlacement:
    address: CellAddress
    def to_world_point(self, layout: HexLayout) -> WorldPoint:
        if not isinstance(layout, HexLayout): raise TypeError("layout must be a HexLayout")
        return axial_to_world(self.address.coord, layout)
def derive_axial(transform: EntityTransform, layout: HexLayout) -> AxialCoord:
    """Derive a nearest hex cell without changing the authoritative WorldPoint."""
    return world_to_axial(transform.location.position, layout)
