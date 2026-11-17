"""World-space and explicitly topological interaction range helpers."""
import math
from hex_world_lab.geometry import WorldPoint, hex_distance
from hex_world_lab.geometry import AxialCoord

def world_distance(first: WorldPoint, second: WorldPoint) -> float:
    if not isinstance(first, WorldPoint) or not isinstance(second, WorldPoint):
        raise TypeError("world_distance requires WorldPoint values")
    return math.hypot(first.x-second.x, first.y-second.y)

def within_world_range(first: WorldPoint, second: WorldPoint, radius: float) -> bool:
    if isinstance(radius, bool) or not isinstance(radius, (int,float)) or not math.isfinite(radius) or radius < 0:
        raise ValueError("radius must be finite and non-negative")
    return world_distance(first, second) <= radius

def within_hex_range(first: AxialCoord, second: AxialCoord, radius: int) -> bool:
    if isinstance(radius, bool) or not isinstance(radius, int) or radius < 0:
        raise ValueError("hex radius must be a non-negative integer")
    return hex_distance(first, second) <= radius
