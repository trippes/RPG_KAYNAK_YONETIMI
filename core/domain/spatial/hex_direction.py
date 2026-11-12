"""Canonical directions for pointy-top axial hex geometry."""

from enum import Enum


class HexDirection(Enum):
    """Six axial directions in the canonical clockwise order."""

    EAST = (1, 0, "WEST")
    NORTH_EAST = (1, -1, "SOUTH_WEST")
    NORTH_WEST = (0, -1, "SOUTH_EAST")
    WEST = (-1, 0, "EAST")
    SOUTH_WEST = (-1, 1, "NORTH_EAST")
    SOUTH_EAST = (0, 1, "NORTH_WEST")

    @property
    def dq(self) -> int:
        return self.value[0]

    @property
    def dr(self) -> int:
        return self.value[1]

    @property
    def offset(self) -> tuple[int, int]:
        return self.dq, self.dr

    @property
    def opposite(self) -> "HexDirection":
        return HexDirection[self.value[2]]
