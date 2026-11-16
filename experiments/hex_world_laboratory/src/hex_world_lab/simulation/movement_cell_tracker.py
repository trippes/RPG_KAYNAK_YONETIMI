"""Track the selected hex cell for one continuously moving actor."""

from hex_world_lab.geometry import AxialCoord, WorldPoint
from hex_world_lab.world.movement_context import MovementWorldContext
from hex_world_lab.world.movement_resolution import MovementCellResolution


class MovementCellTracker:
    """Keep one actor's last successful axial-cell resolution.

    The tracker does not own movement, time, or tick counters. Call update
    after the actor's MovementSystem has completed its movement step.
    """

    __slots__ = ("_context", "_previous_cell", "_current_resolution")

    def __init__(self, context: MovementWorldContext) -> None:
        if not isinstance(context, MovementWorldContext):
            raise TypeError("context must be a MovementWorldContext")
        self._context = context
        self._previous_cell: AxialCoord | None = None
        self._current_resolution: MovementCellResolution | None = None

    @property
    def previous_cell(self) -> AxialCoord | None:
        """Last successfully selected geometric cell."""
        return self._previous_cell

    @property
    def current_resolution(self) -> MovementCellResolution | None:
        """Last successful full resolution, or None before the first update."""
        return self._current_resolution

    def update(self, position: WorldPoint) -> MovementCellResolution:
        """Resolve a new position and commit tracker state only on success."""
        if not isinstance(position, WorldPoint):
            raise TypeError("position must be a WorldPoint")

        resolution = self._context.resolve_position(
            position,
            previous_cell=self._previous_cell,
        )
        # Commit only after all validation and world-view reads succeeded.
        self._previous_cell = resolution.coord
        self._current_resolution = resolution
        return resolution
