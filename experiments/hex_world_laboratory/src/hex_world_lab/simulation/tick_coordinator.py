"""Deterministic orchestration of one authoritative simulation tick."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement import MovementIntent, MovementState
from hex_world_lab.simulation.collision_aware_movement_system import (
    CollisionAwareMovementSystem,
)
from hex_world_lab.simulation.movement_cell_tracker import MovementCellTracker


@dataclass(slots=True)
class _PendingTick:
    """Checkpoint for safely resuming a tick after a downstream failure."""

    tick_number: int
    intent: MovementIntent | None = None
    movement_state: MovementState | None = None
    movement_complete: bool = False
    cell_complete: bool = False
    entity_sync_complete: bool = False


class SimulationTickCoordinator:
    """Run input, movement/collision, cell tracking, and entity sync in order.

    This class deliberately owns neither wall-clock time nor presentation.
    DemoTickPump remains responsible for scheduling fixed-duration ticks.
    """

    __slots__ = (
        "_movement_system",
        "_input_source",
        "_cell_tracker",
        "_entity_sync_callback",
        "_next_tick_number",
        "_pending",
        "_last_completed_tick_number",
    )

    def __init__(
        self,
        movement_system: CollisionAwareMovementSystem,
        input_source: Callable[[], MovementIntent],
        cell_tracker: MovementCellTracker,
        entity_sync_callback: Callable[[WorldPoint], None] | None = None,
    ) -> None:
        if not callable(getattr(movement_system, "step", None)):
            raise TypeError("movement_system must provide step(tick_number, intent)")
        first_tick_number = getattr(movement_system, "next_tick_number", None)
        if (
            isinstance(first_tick_number, bool)
            or not isinstance(first_tick_number, int)
            or first_tick_number < 0
        ):
            raise TypeError("movement_system must expose a non-negative integer next_tick_number")
        if not callable(input_source):
            raise TypeError("input_source must be callable")
        if not callable(getattr(cell_tracker, "update", None)):
            raise TypeError("cell_tracker must provide update(position)")
        if entity_sync_callback is not None and not callable(entity_sync_callback):
            raise TypeError("entity_sync_callback must be callable or None")

        self._movement_system = movement_system
        self._input_source = input_source
        self._cell_tracker = cell_tracker
        self._entity_sync_callback = entity_sync_callback
        self._next_tick_number = first_tick_number
        self._pending: _PendingTick | None = None
        self._last_completed_tick_number: int | None = None

    @property
    def next_tick_number(self) -> int:
        """Return the next tick accepted by this coordinator."""
        return self._next_tick_number

    @property
    def last_completed_tick_number(self) -> int | None:
        """Return the most recently completed tick, if any."""
        return self._last_completed_tick_number

    @property
    def has_pending_tick(self) -> bool:
        """Whether a failed tick is waiting to resume."""
        return self._pending is not None

    def bind_entity_sync_callback(
        self, callback: Callable[[WorldPoint], None]
    ) -> None:
        """Bind entity synchronization once, before the first tick begins."""
        if not callable(callback):
            raise TypeError("callback must be callable")
        if self._pending is not None or self._last_completed_tick_number is not None:
            raise RuntimeError("entity sync callback must be bound before the first tick")
        if self._entity_sync_callback is not None:
            raise RuntimeError("entity sync callback has already been bound")
        self._entity_sync_callback = callback

    def advance_tick(self, tick_number: int) -> MovementState:
        """Advance or resume exactly one tick, committing only when all stages pass."""
        if isinstance(tick_number, bool) or not isinstance(tick_number, int):
            raise TypeError("tick_number must be an integer")
        if tick_number < 0:
            raise ValueError("tick_number must not be negative")

        if self._pending is None:
            if tick_number != self._next_tick_number:
                raise ValueError(
                    f"expected tick {self._next_tick_number}, received {tick_number}"
                )
            self._pending = _PendingTick(tick_number)
        elif tick_number != self._pending.tick_number:
            raise ValueError(
                f"tick {self._pending.tick_number} is pending; received {tick_number}"
            )

        pending = self._pending
        assert pending is not None

        if pending.intent is None:
            intent = self._input_source()
            if not isinstance(intent, MovementIntent):
                raise TypeError("input_source must return a MovementIntent")
            pending.intent = intent

        if not pending.movement_complete:
            state = self._movement_system.step(tick_number, pending.intent)
            if not isinstance(state, MovementState):
                raise TypeError("movement_system.step must return a MovementState")
            pending.movement_state = state
            pending.movement_complete = True

        state = pending.movement_state
        assert state is not None

        if not pending.cell_complete:
            self._cell_tracker.update(state.position)
            pending.cell_complete = True

        if not pending.entity_sync_complete:
            if self._entity_sync_callback is not None:
                self._entity_sync_callback(state.position)
            pending.entity_sync_complete = True

        self._last_completed_tick_number = tick_number
        self._next_tick_number = tick_number + 1
        self._pending = None
        return state
