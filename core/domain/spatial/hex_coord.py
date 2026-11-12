"""Immutable axial coordinates and topology-only hex operations."""

from __future__ import annotations

from dataclasses import dataclass

from .hex_direction import HexDirection


@dataclass(frozen=True, order=True, slots=True)
class HexCoord:
    """An integer axial coordinate.

    HexCoord represents geometry only. It does not know about map bounds,
    passability, map identity, pixels, or movement costs.
    """

    q: int
    r: int

    def __post_init__(self) -> None:
        self._validate_component(self.q, "q")
        self._validate_component(self.r, "r")

    @staticmethod
    def _validate_component(value: object, name: str) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer.")

    def __add__(self, other: object) -> "HexCoord":
        if not isinstance(other, HexCoord):
            return NotImplemented
        return HexCoord(self.q + other.q, self.r + other.r)

    def __sub__(self, other: object) -> "HexCoord":
        if not isinstance(other, HexCoord):
            return NotImplemented
        return HexCoord(self.q - other.q, self.r - other.r)

    def translated(self, dq: int = 0, dr: int = 0) -> "HexCoord":
        """Return a new coordinate offset by an axial delta."""
        self._validate_component(dq, "dq")
        self._validate_component(dr, "dr")
        return HexCoord(self.q + dq, self.r + dr)

    def neighbor(self, direction: HexDirection) -> "HexCoord":
        """Return the adjacent coordinate in one canonical direction."""
        if not isinstance(direction, HexDirection):
            raise TypeError("direction must be a HexDirection.")
        return self.translated(direction.dq, direction.dr)

    def neighbors(self) -> tuple["HexCoord", ...]:
        """Return all six neighbors in canonical direction order."""
        return tuple(self.neighbor(direction) for direction in HexDirection)

    def distance_to(self, other: "HexCoord") -> int:
        """Return topological hex steps, not physical distance or movement cost."""
        if not isinstance(other, HexCoord):
            raise TypeError("other must be a HexCoord.")
        dq = self.q - other.q
        dr = self.r - other.r
        return max(abs(dq), abs(dr), abs(dq + dr))
