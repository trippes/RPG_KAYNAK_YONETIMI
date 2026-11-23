"""Distance-driven, world-aware humanoid locomotion and idle animation."""

from __future__ import annotations

import math

from game_ui.world_rendering.humanoid_locomotion_3d import HumanoidFootLockSolver3D


class HumanoidBodyAnimator3D:
    """Produce quantized, cache-friendly rig poses from actual actor movement."""

    DIRECTIONS = (
        "east", "south_east", "south", "south_west",
        "west", "north_west", "north", "north_east",
    )
    STATES = ("idle", "walk", "run")
    WALK_CADENCE_STEPS_PER_MINUTE = 110.0
    RUN_CADENCE_STEPS_PER_MINUTE = 170.0
    WALK_CYCLE_SECONDS = 120.0 / WALK_CADENCE_STEPS_PER_MINUTE
    RUN_CYCLE_SECONDS = 120.0 / RUN_CADENCE_STEPS_PER_MINUTE
    WALK_CYCLE_DISTANCE = 24.0
    RUN_CYCLE_DISTANCE = 34.0
    WALK_STANCE_FRACTION = HumanoidFootLockSolver3D.WALK_STANCE_FRACTION
    RUN_STANCE_FRACTION = HumanoidFootLockSolver3D.RUN_STANCE_FRACTION
    PHASE_STEPS = 16
    IDLE_PHASE_STEPS = 8
    TRANSITION_SECONDS = 0.18
    BLEND_STEPS = 8

    def __init__(self, direction: str = "south", state: str = "idle") -> None:
        self._validate_selection(direction, state)
        self.direction = direction
        self.state = state
        self.phase = 0.0
        self._idle_clock = 0.0
        self._pose: dict[str, tuple[float, float, float]] = {}
        self._translations: dict[str, tuple[float, float, float]] = {}
        self._foot_lock = HumanoidFootLockSolver3D()
        self._blend_pose: dict[str, tuple[float, float, float]] = {}
        self._blend_translations: dict[str, tuple[float, float, float]] = {}
        self._transition_elapsed = self.TRANSITION_SECONDS

    @classmethod
    def _validate_selection(cls, direction: str, state: str) -> None:
        if direction not in cls.DIRECTIONS:
            raise ValueError(f"Unsupported character direction: {direction!r}.")
        if state not in cls.STATES:
            raise ValueError(f"Unsupported character animation state: {state!r}.")

    def select(
        self, *, direction: str | None = None, state: str | None = None
    ) -> None:
        """Change state/facing while preserving accumulated gait phase."""
        next_direction = self.direction if direction is None else direction
        next_state = self.state if state is None else state
        self._validate_selection(next_direction, next_state)
        if next_state != self.state:
            self._blend_pose = dict(self._pose)
            self._blend_translations = dict(self._translations)
            self._transition_elapsed = 0.0
        self.direction = next_direction
        self.state = next_state

    def advance(
        self,
        traveled_distance: float,
        delta_seconds: float = 1.0 / 60.0,
        *,
        world_position: tuple[float, float] | None = None,
        yaw: float = 0.0,
        world_scale: float = 54.0,
    ) -> dict[str, tuple[float, float, float]]:
        """Advance gait from measured displacement and solve stance feet in world space."""
        if (
            isinstance(traveled_distance, bool)
            or not isinstance(traveled_distance, (int, float))
            or not math.isfinite(traveled_distance)
            or traveled_distance < 0
        ):
            raise ValueError("traveled_distance must be a finite non-negative number.")
        if (
            isinstance(delta_seconds, bool)
            or not isinstance(delta_seconds, (int, float))
            or not math.isfinite(delta_seconds)
            or delta_seconds < 0
        ):
            raise ValueError("delta_seconds must be a finite non-negative number.")

        elapsed_seconds = float(delta_seconds)
        transition_delta = min(elapsed_seconds, 0.1)
        if self.state != "idle" and traveled_distance > 0.0 and elapsed_seconds > 1e-6:
            cadence = (
                self.RUN_CADENCE_STEPS_PER_MINUTE
                if self.state == "run"
                else self.WALK_CADENCE_STEPS_PER_MINUTE
            )
            cycle_seconds = 120.0 / cadence
            measured_speed = float(traveled_distance) / elapsed_seconds
            cycle_distance = measured_speed * cycle_seconds
            if cycle_distance > 1e-9:
                self.phase = (
                    self.phase + math.tau * float(traveled_distance) / cycle_distance
                ) % math.tau
        else:
            self._idle_clock += transition_delta

        target_pose = self._build_pose()
        foot_rotations, target_translations = self._foot_lock.update(
            phase=self.phase,
            state=self.state,
            world_position=world_position,
            yaw=float(yaw),
            world_scale=float(world_scale),
            delta_seconds=transition_delta,
        )
        target_pose.update(foot_rotations)

        if self.state == "idle":
            target_translations = {}

        if self._transition_elapsed < self.TRANSITION_SECONDS:
            self._transition_elapsed = min(
                self.TRANSITION_SECONDS,
                self._transition_elapsed + transition_delta,
            )
            raw_weight = self._transition_elapsed / self.TRANSITION_SECONDS
            weight = raw_weight * raw_weight * (3.0 - 2.0 * raw_weight)
            target_pose = self._blend_maps(
                self._blend_pose, target_pose, weight, (0.0, 0.0, 0.0)
            )
            target_translations = self._blend_maps(
                self._blend_translations,
                target_translations,
                weight,
                (0.0, 0.0, 0.0),
            )

        # Quantization keeps the software-rendered sprite cache bounded while
        # preserving much finer motion than the original eight gait samples.
        self._pose = {
            name: tuple(self._quantize(value, 1.0 / 1024.0) for value in rotation)
            for name, rotation in target_pose.items()
        }
        self._translations = {
            name: tuple(self._quantize(value, 1.0 / 1024.0) for value in translation)
            for name, translation in target_translations.items()
        }
        return self.pose

    @staticmethod
    def _quantize(value: float, step: float) -> float:
        return round(value / step) * step

    @staticmethod
    def _blend_maps(first, second, weight, default):
        result = {}
        for name in set(first) | set(second):
            a = first.get(name, default)
            b = second.get(name, default)
            value = tuple(
                a[index] + (b[index] - a[index]) * weight
                for index in range(3)
            )
            if any(abs(component) > 1e-8 for component in value):
                result[name] = value
        return result

    @property
    def pose(self) -> dict[str, tuple[float, float, float]]:
        return dict(self._pose)

    @property
    def translations(self) -> dict[str, tuple[float, float, float]]:
        return dict(self._translations)

    @property
    def foot_lock_diagnostics(self):
        return self._foot_lock.diagnostics

    @property
    def phase_index(self) -> int:
        return min(
            self.PHASE_STEPS - 1,
            int((self.phase % math.tau) * self.PHASE_STEPS / math.tau),
        )

    def _build_pose(self) -> dict[str, tuple[float, float, float]]:
        if self.state == "idle":
            return self._build_idle_pose()
        phase = self.phase
        running = self.state == "run"
        stance_fraction = (
            self.RUN_STANCE_FRACTION if running else self.WALK_STANCE_FRACTION
        )
        knee_amplitude = 0.88 if running else 0.68
        hip_amplitude = 0.48 if running else 0.36
        arm_amplitude = 0.95 if running else 0.82
        torso_twist_amplitude = 0.085 if running else 0.060
        lean = 0.12 if running else 0.025

        def leg_pose(leg_phase):
            leg_phase %= math.tau
            stance_end = math.tau * stance_fraction
            if leg_phase < stance_end:
                progress = leg_phase / stance_end
                hip = hip_amplitude * (1.0 - 2.0 * progress)
                knee = 0.0
                toe = 0.18 * progress
            else:
                progress = (leg_phase - stance_end) / (math.tau - stance_end)
                eased = progress * progress * (3.0 - 2.0 * progress)
                hip = hip_amplitude * (-1.0 + 2.0 * eased)
                knee = -knee_amplitude * math.sin(math.pi * progress)
                toe = -0.10 * math.sin(math.pi * progress)
            return hip, knee, toe

        left_hip, left_knee, left_toe = leg_pose(phase)
        right_hip, right_knee, right_toe = leg_pose(phase + math.pi)
        left_shoulder = -right_hip * arm_amplitude
        right_shoulder = -left_hip * arm_amplitude
        torso_twist = math.sin(phase * 2.0) * torso_twist_amplitude
        pelvis_roll = math.sin(phase * 2.0) * (0.035 if running else 0.025)
        pelvis_bob = max(0.0, math.sin(phase * 2.0)) * (0.025 if running else 0.010)
        left_ankle = -left_hip * 0.20 - left_knee * 0.32
        right_ankle = -right_hip * 0.20 - right_knee * 0.32
        shoulder_tuck = 0.66 if running else 0.56
        return {
            "pelvis": (0.0, 0.0, torso_twist * 0.35 + pelvis_roll),
            "spine_lower": (-lean * 0.30 + pelvis_bob, 0.0, -torso_twist * 0.30),
            "spine_upper": (-lean * 0.70, 0.0, torso_twist),
            "chest": (-lean * 0.30, 0.0, -torso_twist * 0.60),
            "neck": (0.0, 0.0, -torso_twist * 0.18),
            "head": (lean * 0.12, 0.0, -torso_twist * 0.10),
            "clavicle_left": (left_shoulder * 0.16, 0.0, left_shoulder * 0.08),
            "clavicle_right": (right_shoulder * 0.16, 0.0, right_shoulder * 0.08),
            "scapula_left_control": (left_shoulder * 0.10, 0.0, 0.0),
            "scapula_right_control": (right_shoulder * 0.10, 0.0, 0.0),
            "hip_left": (left_hip, 0.0, 0.0),
            "hip_right": (right_hip, 0.0, 0.0),
            "knee_left": (left_knee, 0.0, 0.0),
            "knee_right": (right_knee, 0.0, 0.0),
            "ankle_left": (left_ankle, 0.0, 0.0),
            "ankle_right": (right_ankle, 0.0, 0.0),
            "heel_left": (0.0, 0.0, 0.0),
            "heel_right": (0.0, 0.0, 0.0),
            "foot_ball_left": (left_toe, 0.0, 0.0),
            "foot_ball_right": (right_toe, 0.0, 0.0),
            "toe_left": (-left_toe * 0.25, 0.0, 0.0),
            "toe_right": (-right_toe * 0.25, 0.0, 0.0),
            "shoulder_left": (left_shoulder, -shoulder_tuck, 0.0),
            "shoulder_right": (right_shoulder, shoulder_tuck, 0.0),
            "elbow_left": (0.0, 0.0, -0.24 - max(0.0, left_shoulder) * 0.12),
            "elbow_right": (0.0, 0.0, -0.24 - max(0.0, right_shoulder) * 0.12),
            "wrist_left": (0.025 * math.sin(phase), 0.0, 0.0),
            "wrist_right": (-0.025 * math.sin(phase), 0.0, 0.0),
            "hand_left": (0.015 * math.sin(phase), 0.0, 0.0),
            "hand_right": (-0.015 * math.sin(phase), 0.0, 0.0),
        }

    def _build_idle_pose(self) -> dict[str, tuple[float, float, float]]:
        phase_index = int(
            (self._idle_clock % 3.2) / 3.2 * self.IDLE_PHASE_STEPS
        )
        phase = phase_index * math.tau / self.IDLE_PHASE_STEPS
        breath = math.sin(phase) * 0.025
        sway = math.sin(phase * 0.5 + 0.7) * 0.055
        head_motion = math.sin(phase * 0.5 - 0.4) * 0.035
        return {
            "spine_lower": (0.0, 0.0, -breath * 0.25),
            "spine_upper": (breath * 0.35, 0.0, sway * 0.25),
            "chest": (breath, 0.0, -sway * 0.20),
            "neck": (0.0, 0.0, head_motion * 0.35),
            "head": (head_motion, 0.0, -head_motion),
            "clavicle_left": (breath * 0.18, 0.0, sway * 0.12),
            "clavicle_right": (breath * 0.18, 0.0, -sway * 0.12),
            "scapula_left_control": (breath * 0.12, 0.0, 0.0),
            "scapula_right_control": (breath * 0.12, 0.0, 0.0),
            "shoulder_left": (breath * 0.20, -0.70, sway * 0.20),
            "shoulder_right": (breath * 0.20, 0.70, -sway * 0.20),
            "elbow_left": (0.0, 0.0, -0.20),
            "elbow_right": (0.0, 0.0, -0.20),
            "wrist_left": (0.0, 0.0, 0.012 * math.sin(phase)),
            "wrist_right": (0.0, 0.0, -0.012 * math.sin(phase)),
            "hand_left": (0.0, 0.0, 0.008 * math.sin(phase)),
            "hand_right": (0.0, 0.0, -0.008 * math.sin(phase)),
            "hip_left": (sway, 0.0, 0.0),
            "hip_right": (-sway, 0.0, 0.0),
            "knee_left": (-0.035, 0.0, 0.0),
            "knee_right": (-0.035, 0.0, 0.0),
            "ankle_left": (0.015, 0.0, 0.0),
            "ankle_right": (0.015, 0.0, 0.0),
            "heel_left": (0.0, 0.0, 0.0),
            "heel_right": (0.0, 0.0, 0.0),
            "foot_ball_left": (0.0, 0.0, 0.0),
            "foot_ball_right": (0.0, 0.0, 0.0),
            "toe_left": (0.0, 0.0, 0.0),
            "toe_right": (0.0, 0.0, 0.0),
        }


__all__ = ["HumanoidBodyAnimator3D"]
