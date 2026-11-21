"""Deterministic, time-based joint poses for the shared character rig."""

from __future__ import annotations

import math


class CharacterRigAnimator:
    """Generate local joint rotations for idle, walk, and run states.

    Each animator owns its phase and pose state. It has no Pygame dependency
    and never changes the immutable skeleton or the character's world position.
    """

    DIRECTIONS = (
        "north", "north_east", "east", "south_east",
        "south", "south_west", "west", "north_west",
    )
    STATES = ("idle", "walk", "run")

    CYCLE_SECONDS = {
        "idle": 3.2,
        "walk": 0.72,
        "run": 0.48,
    }

    def __init__(self, direction: str = "south", state: str = "idle") -> None:
        self._validate_selection(direction, state)
        self.direction = direction
        self.state = state
        self.elapsed = 0.0
        self.phase = 0.0
        self._pose = self._build_pose()

    @classmethod
    def _validate_selection(cls, direction: str, state: str) -> None:
        if direction not in cls.DIRECTIONS:
            raise ValueError(f"Unsupported character direction: {direction!r}.")
        if state not in cls.STATES:
            raise ValueError(f"Unsupported character animation state: {state!r}.")

    def select(self, *, direction: str | None = None, state: str | None = None) -> None:
        """Select facing/state; preserve gait phase when only facing changes."""
        next_direction = self.direction if direction is None else direction
        next_state = self.state if state is None else state
        self._validate_selection(next_direction, next_state)

        if next_state != self.state:
            previous_cycle = self.CYCLE_SECONDS[self.state]
            next_cycle = self.CYCLE_SECONDS[next_state]
            normalized_phase = (self.elapsed % previous_cycle) / previous_cycle
            self.elapsed = normalized_phase * next_cycle
            self.phase = normalized_phase * math.tau
        self.direction = next_direction
        self.state = next_state
        self._pose = self._build_pose()

    def update(self, delta_seconds: float) -> dict[str, float]:
        """Advance by elapsed seconds and return a fresh local-rotation mapping."""
        if (
            isinstance(delta_seconds, bool)
            or not isinstance(delta_seconds, (int, float))
            or not math.isfinite(delta_seconds)
            or delta_seconds < 0
        ):
            raise ValueError("delta_seconds must be a finite non-negative number.")

        self.elapsed += float(delta_seconds)
        cycle = self.CYCLE_SECONDS[self.state]
        self.phase = math.tau * ((self.elapsed % cycle) / cycle)
        self._pose = self._build_pose()
        return dict(self._pose)

    @property
    def pose(self) -> dict[str, float]:
        """Return a copy of the current joint-local rotation mapping."""
        return dict(self._pose)

    def _build_pose(self) -> dict[str, float]:
        if self.state == "idle":
            return self._idle_pose()
        if self.state == "walk":
            return self._gait_pose(amplitude=0.42, knee_bend=0.48, arm_swing=0.30)
        return self._gait_pose(amplitude=0.68, knee_bend=0.78, arm_swing=0.48)

    def _idle_pose(self) -> dict[str, float]:
        breath = math.sin(self.phase)
        sway = math.sin(self.phase * 0.5)
        return {
            "spine": 0.018 * breath,
            "chest": 0.012 * breath,
            "neck": -0.006 * breath,
            "left_shoulder": -0.025 + 0.012 * sway,
            "right_shoulder": 0.025 - 0.012 * sway,
            "left_hip": 0.008 * sway,
            "right_hip": -0.008 * sway,
        }

    def _gait_pose(
        self, *, amplitude: float, knee_bend: float, arm_swing: float
    ) -> dict[str, float]:
        # Opposite legs and arms move together. The cycle is continuous at 2π.
        swing = math.sin(self.phase)
        left_swing = swing * amplitude
        right_swing = -left_swing

        # Knee flexion is strongest while the corresponding leg swings forward.
        left_knee = max(0.0, math.sin(self.phase + math.pi * 0.5)) * knee_bend
        right_knee = max(0.0, math.sin(self.phase - math.pi * 0.5)) * knee_bend

        # The ankle counter-rotates against the accumulated hip/knee rotation,
        # keeping the foot's local orientation close to horizontal.
        left_ankle = -(left_swing + left_knee) * 0.72
        right_ankle = -(right_swing + right_knee) * 0.72

        return {
            "pelvis": 0.012 * math.sin(self.phase * 2.0),
            "spine": 0.035 + 0.018 * math.sin(self.phase * 2.0),
            "chest": -0.025 + 0.012 * math.sin(self.phase * 2.0),
            "left_hip": left_swing,
            "right_hip": right_swing,
            "left_knee": left_knee,
            "right_knee": right_knee,
            "left_ankle": left_ankle,
            "right_ankle": right_ankle,
            "left_shoulder": -left_swing * 0.62 - arm_swing,
            "right_shoulder": -right_swing * 0.62 + arm_swing,
            "left_elbow": 0.10 + max(0.0, -left_swing) * 0.18,
            "right_elbow": -0.10 - max(0.0, -right_swing) * 0.18,
        }
