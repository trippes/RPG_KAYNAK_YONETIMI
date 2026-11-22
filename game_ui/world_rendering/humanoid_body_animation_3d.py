"""Distance-driven gait poses for the parametric 3D humanoid body.

The animator consumes presentation-space travel distance only. It never owns
world position, movement authority, collision, or physics state. Gait poses are
quantized into reusable samples so the raster sprite cache can serve repeated
poses across actors instead of rebuilding a unique mesh every frame.
"""

from __future__ import annotations

import math


class HumanoidBodyAnimator3D:
    """Produce cached-sample XYZ joint rotations from actual travel distance."""

    DIRECTIONS = (
        "east", "south_east", "south", "south_west",
        "west", "north_west", "north", "north_east",
    )
    STATES = ("idle", "walk", "run")

    # WorldTransform uses world-pixel coordinates. These are full gait-cycle
    # travel distances, not frame durations; animation therefore stops with
    # movement and is independent of frame-rate fluctuations.
    WALK_CYCLE_DISTANCE = 56.0
    RUN_CYCLE_DISTANCE = 84.0
    PHASE_STEPS = 8

    def __init__(self, direction: str = "south", state: str = "idle") -> None:
        self._validate_selection(direction, state)
        self.direction = direction
        self.state = state
        self.phase = 0.0
        self._pose = self._build_pose()

    @classmethod
    def _validate_selection(cls, direction: str, state: str) -> None:
        if direction not in cls.DIRECTIONS:
            raise ValueError(f"Unsupported character direction: {direction!r}.")
        if state not in cls.STATES:
            raise ValueError(f"Unsupported character animation state: {state!r}.")

    def select(
        self, *, direction: str | None = None, state: str | None = None
    ) -> None:
        """Change facing/state without resetting the accumulated gait phase."""
        next_direction = self.direction if direction is None else direction
        next_state = self.state if state is None else state
        self._validate_selection(next_direction, next_state)
        self.direction = next_direction
        self.state = next_state
        self._pose = self._build_pose()

    def advance(self, traveled_distance: float) -> dict[str, tuple[float, float, float]]:
        """Advance gait by measured world travel and return local XYZ rotations."""
        if (
            isinstance(traveled_distance, bool)
            or not isinstance(traveled_distance, (int, float))
            or not math.isfinite(traveled_distance)
            or traveled_distance < 0
        ):
            raise ValueError("traveled_distance must be a finite non-negative number.")

        if self.state != "idle" and traveled_distance > 0.0:
            cycle_distance = (
                self.RUN_CYCLE_DISTANCE
                if self.state == "run"
                else self.WALK_CYCLE_DISTANCE
            )
            self.phase = (
                self.phase + math.tau * float(traveled_distance) / cycle_distance
            ) % math.tau
        self._pose = self._build_pose()
        return self.pose

    @property
    def pose(self) -> dict[str, tuple[float, float, float]]:
        """Return a copy of the current sparse local-rotation mapping."""
        return dict(self._pose)

    @property
    def phase_index(self) -> int:
        """Return the deterministic raster-cache sample for the current phase."""
        return min(
            self.PHASE_STEPS - 1,
            int((self.phase % math.tau) * self.PHASE_STEPS / math.tau),
        )

    def _build_pose(self) -> dict[str, tuple[float, float, float]]:
        if self.state == "idle":
            return {}

        phase = self.phase_index * math.tau / self.PHASE_STEPS
        amplitude = 0.42 if self.state == "walk" else 0.66
        knee_amplitude = 0.62 if self.state == "walk" else 0.88

        left_hip = math.sin(phase) * amplitude
        right_hip = -left_hip
        left_knee = -max(0.0, math.sin(phase + math.pi * 0.5)) * knee_amplitude
        right_knee = -max(0.0, math.sin(phase - math.pi * 0.5)) * knee_amplitude

        # Counter-swing the arms and ankles against the legs. Axes follow the
        # rig contract: +Y forward, +Z up, and X as the sagittal swing axis.
        left_shoulder = -right_hip * 0.48
        right_shoulder = -left_hip * 0.48
        left_ankle = -(left_hip + left_knee) * 0.22
        right_ankle = -(right_hip + right_knee) * 0.22
        torso_twist = math.sin(phase * 2.0) * 0.018

        return {
            "pelvis": (0.0, 0.0, torso_twist * 0.45),
            "spine_upper": (0.0, 0.0, torso_twist),
            "chest": (0.0, 0.0, -torso_twist * 0.65),
            "hip_left": (left_hip, 0.0, 0.0),
            "hip_right": (right_hip, 0.0, 0.0),
            "knee_left": (left_knee, 0.0, 0.0),
            "knee_right": (right_knee, 0.0, 0.0),
            "ankle_left": (left_ankle, 0.0, 0.0),
            "ankle_right": (right_ankle, 0.0, 0.0),
            "shoulder_left": (left_shoulder, 0.0, 0.0),
            "shoulder_right": (right_shoulder, 0.0, 0.0),
        }


__all__ = ["HumanoidBodyAnimator3D"]
