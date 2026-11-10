"""Mutable 1.x Position adapter backed by the canonical immutable value object.

New simulation and actor code should use :mod:`core.domain.spatial` directly.
This adapter preserves the mutable Entity-facing API while keeping its stored
coordinate value canonical.
"""

from core.domain.spatial import Position as CanonicalPosition


class Position:
    """Compatibility adapter for legacy Entity.position callers."""

    def __init__(self, x=0, y=0):
        self._position = CanonicalPosition(x, y)

    @property
    def x(self):
        return self._position.x

    @x.setter
    def x(self, value):
        self._position = CanonicalPosition(value, self._position.y)

    @property
    def y(self):
        return self._position.y

    @y.setter
    def y(self, value):
        self._position = CanonicalPosition(self._position.x, value)

    @staticmethod
    def _validate_coordinate(value, name):
        CanonicalPosition._validate_coordinate(value, name)

    @staticmethod
    def _validate_movement(value, name):
        CanonicalPosition._validate_coordinate(value, name)

    def set_position(self, x, y):
        self._position = CanonicalPosition(x, y)

    def get_position(self):
        return (self.x, self.y)

    def move(self, dx=0, dy=0):
        self._position = self._position.translated(dx, dy)

    def distance_to(self, other):
        if isinstance(other, Position):
            other = other.to_canonical()
        if not isinstance(other, CanonicalPosition):
            raise TypeError("Mesafe hesaplamak için Position nesnesi gereklidir.")
        return self._position.distance_to(other)

    def same_as(self, other):
        if isinstance(other, Position):
            other = other.to_canonical()
        return isinstance(other, CanonicalPosition) and self._position == other

    def copy(self):
        return Position(self.x, self.y)

    def to_dict(self):
        return self._position.to_dict()

    def to_canonical(self):
        """Return the immutable canonical coordinate value."""
        return self._position
