"""Drive continuous movement from externally supplied canonical ticks."""

from hex_world_lab.movement import (
    MovementConfig,
    MovementIntegrator,
    MovementIntent,
    MovementState,
)

TICK_RATE = 60
TICK_DELTA_SECONDS = 1.0 / TICK_RATE


class MovementSystem:
    """Advance one actor exactly once for each accepted consecutive tick."""

    __slots__ = ("_integrator", "_state", "_next_tick_number")

    def __init__(
        self,
        initial_state: MovementState,
        config: MovementConfig,
        *,
        first_tick_number: int = 0,
    ) -> None:
        if not isinstance(initial_state, MovementState):
            raise TypeError("initial_state must be a MovementState")
        if not isinstance(config, MovementConfig):
            raise TypeError("config must be a MovementConfig")
        self._validate_tick_number(first_tick_number)
        self._integrator = MovementIntegrator(config)
        self._state = initial_state
        self._next_tick_number = first_tick_number

    @staticmethod
    def _validate_tick_number(tick_number: int) -> None:
        if isinstance(tick_number, bool) or not isinstance(tick_number, int):
            raise TypeError("tick_number must be an integer")
        if tick_number < 0:
            raise ValueError("tick_number must not be negative")

    @property
    def state(self) -> MovementState:
        """Return the current immutable movement state."""
        return self._state

    @property
    def next_tick_number(self) -> int:
        """Return the only tick number currently accepted."""
        return self._next_tick_number

    def step(self, tick_number: int, intent: MovementIntent) -> MovementState:
        """Apply one fixed-duration movement step for the expected tick."""
        self._validate_tick_number(tick_number)
        if tick_number != self._next_tick_number:
            raise ValueError(
                f"expected tick {self._next_tick_number}, received {tick_number}"
            )
        if not isinstance(intent, MovementIntent):
            raise TypeError("intent must be a MovementIntent")

        # Compute first; commit state and tick sequence only after success.
        next_state = self._integrator.step(
            self._state, intent, TICK_DELTA_SECONDS
        )
        self._state = next_state
        self._next_tick_number += 1
        return next_state
