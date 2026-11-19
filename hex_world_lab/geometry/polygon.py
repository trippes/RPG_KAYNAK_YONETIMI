"""Regular hexagon vertices and edges in world coordinates."""
import math
from .coordinates import AxialCoord, WorldPoint
from .layout import HexLayout
from .orientation import HexOrientation
from .transforms import axial_to_world

def hex_corners(center: WorldPoint, layout: HexLayout) -> tuple[WorldPoint, ...]:
    """Return six vertices in counter-clockwise order in mathematical space."""
    start = 0.0 if layout.orientation is HexOrientation.FLAT_TOP else 30.0
    return tuple(
        WorldPoint(center.x + layout.radius * math.cos(math.radians(start + 60.0*i)),
                   center.y + layout.radius * math.sin(math.radians(start + 60.0*i)))
        for i in range(6)
    )

def hex_polygon(coord: AxialCoord, layout: HexLayout) -> tuple[WorldPoint, ...]:
    """Return the six world-space vertices for an axial cell."""
    return hex_corners(axial_to_world(coord, layout), layout)

def hex_edges(center: WorldPoint, layout: HexLayout) -> tuple[tuple[WorldPoint, WorldPoint], ...]:
    """Return the six polygon edges in counter-clockwise order."""
    corners = hex_corners(center, layout)
    return tuple((corners[i], corners[(i+1) % 6]) for i in range(6))
