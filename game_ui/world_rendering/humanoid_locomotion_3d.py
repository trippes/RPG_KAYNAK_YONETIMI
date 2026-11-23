"""World-space foot contacts and analytic two-bone leg IK for humanoid locomotion."""
from __future__ import annotations
from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class TwoBoneIKResult:
    hip_angle: float
    knee_angle: float
    reachable: bool
    target_distance: float
    solved_distance: float
    end_forward: float
    end_down: float


def solve_two_bone_ik(target_forward, target_down, upper_length, lower_length):
    """Solve a planar leg in local forward/down coordinates."""
    values = (target_forward, target_down, upper_length, lower_length)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise ValueError("IK inputs must be finite numbers.")
    if upper_length <= 0.0 or lower_length <= 0.0:
        raise ValueError("Bone lengths must be positive.")
    distance = math.hypot(target_forward, target_down)
    maximum = upper_length + lower_length
    minimum = abs(upper_length - lower_length)
    epsilon = 1e-7
    solved = max(minimum + epsilon, min(maximum - epsilon, distance))
    reachable = abs(solved - distance) <= 1e-7
    target_angle = math.atan2(target_forward, target_down)
    cosine_knee = (solved * solved - upper_length**2 - lower_length**2) / (2.0 * upper_length * lower_length)
    knee = -math.acos(max(-1.0, min(1.0, cosine_knee)))
    hip_offset = math.atan2(
        lower_length * math.sin(knee),
        upper_length + lower_length * math.cos(knee),
    )
    hip = target_angle - hip_offset
    end_forward = upper_length * math.sin(hip) + lower_length * math.sin(hip + knee)
    end_down = upper_length * math.cos(hip) + lower_length * math.cos(hip + knee)
    return TwoBoneIKResult(hip, knee, reachable, distance, solved, end_forward, end_down)


class HumanoidFootLockSolver3D:
    """Keep stance-foot anchors fixed in world space and solve both leg chains."""
    WALK_STANCE_FRACTION = 0.42
    RUN_STANCE_FRACTION = 0.30
    WALK_PELVIS_DROP = 0.07
    RUN_PELVIS_DROP = 0.06
    RUN_FLIGHT_RISE = 0.025
    UPPER_LEG_LENGTH = 0.22
    LOWER_LEG_LENGTH = 0.228
    CONTACT_FORWARD = 0.02
    TARGET_QUANTIZATION = 1.0 / 1024.0
    ANGLE_QUANTIZATION = 1.0 / 1024.0
    WALK_SWING_LIFT = 0.075
    RUN_SWING_LIFT = 0.125
    SIDES = ("left", "right")

    def __init__(self):
        self._anchors = {side: None for side in self.SIDES}
        self._was_stance = {side: False for side in self.SIDES}
        self._last_results = {}
        self._smoothed_rotations = {}
        self._smoothed_translations = {}

    @property
    def anchors(self):
        return dict(self._anchors)

    @property
    def diagnostics(self):
        return {
            side: {
                "reachable": result.reachable,
                "target_distance": result.target_distance,
                "solved_distance": result.solved_distance,
                "error": abs(result.target_distance - result.solved_distance),
            }
            for side, result in self._last_results.items()
        }

    def reset(self):
        for side in self.SIDES:
            self._anchors[side] = None
            self._was_stance[side] = False
        self._last_results.clear()
        self._smoothed_rotations.clear()
        self._smoothed_translations.clear()

    def update(
        self, *, phase, state, world_position, yaw, world_scale,
        ground_anchor_z=-0.49, delta_seconds=1.0 / 60.0,
    ):
        """Solve stance contacts and a lifted swing arc in the same gait phase."""
        if state not in {"walk", "run"} or world_position is None:
            self.reset()
            return {}, {}
        values = (*world_position, phase, yaw, world_scale, ground_anchor_z, delta_seconds)
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in values
        ):
            raise ValueError("Foot-lock inputs must be finite.")
        if world_scale <= 0.0 or delta_seconds < 0.0:
            raise ValueError("world_scale must be positive and delta_seconds non-negative.")

        stance_fraction = (
            self.RUN_STANCE_FRACTION if state == "run" else self.WALK_STANCE_FRACTION
        )
        pelvis_drop = self.RUN_PELVIS_DROP if state == "run" else self.WALK_PELVIS_DROP
        swing_lift = self.RUN_SWING_LIFT if state == "run" else self.WALK_SWING_LIFT
        cosine, sine = math.cos(yaw), math.sin(yaw)
        rotations = {}
        self._last_results.clear()
        base_down = abs(ground_anchor_z + 0.03) - 0.02 - pelvis_drop
        stance_load = 0.0

        for side in self.SIDES:
            leg_phase = (phase + (0.0 if side == "left" else math.pi)) % math.tau
            stance_end = math.tau * stance_fraction
            in_stance = leg_phase < stance_end
            hip_x = -0.075 if side == "left" else 0.075
            if in_stance and not self._was_stance[side]:
                local_y = self.CONTACT_FORWARD
                self._anchors[side] = (
                    world_position[0] + (hip_x * cosine - local_y * sine) * world_scale,
                    world_position[1] + (hip_x * sine + local_y * cosine) * world_scale,
                )
            elif not in_stance:
                self._anchors[side] = None
            self._was_stance[side] = in_stance

            if in_stance and self._anchors[side] is not None:
                anchor = self._anchors[side]
                world_dx = (anchor[0] - world_position[0]) / world_scale
                world_dy = (anchor[1] - world_position[1]) / world_scale
                local_x = world_dx * cosine + world_dy * sine
                local_y = -world_dx * sine + world_dy * cosine
                target_lateral = local_x - hip_x
                target_forward = local_y
                stance_progress = leg_phase / stance_end
                stance_load += math.sin(math.pi * stance_progress) ** 2
                target_down = base_down
                ankle_angle = 0.10 * stance_progress
            else:
                swing_progress = (leg_phase - stance_end) / (math.tau - stance_end)
                eased = swing_progress * swing_progress * (3.0 - 2.0 * swing_progress)
                target_forward = -0.16 + 0.32 * eased
                target_lateral = 0.0
                target_down = base_down - swing_lift * math.sin(math.pi * swing_progress)
                ankle_angle = (
                    -0.18 * math.sin(math.pi * swing_progress)
                    + 0.08 * (1.0 - swing_progress)
                )

            result = solve_two_bone_ik(
                target_forward, target_down,
                self.UPPER_LEG_LENGTH, self.LOWER_LEG_LENGTH,
            )
            self._last_results[side] = result
            lateral_angle = -math.atan2(target_lateral, max(1e-6, target_down))
            rotations[f"hip_{side}"] = (result.hip_angle, lateral_angle, 0.0)
            rotations[f"knee_{side}"] = (result.knee_angle, 0.0, 0.0)
            rotations[f"ankle_{side}"] = (ankle_angle, 0.0, 0.0)

        contact_weight = min(1.0, stance_load)
        pelvis_height = -pelvis_drop * contact_weight
        if state == "run":
            phase_position = phase % math.tau
            swing_phase = (phase_position - math.tau * stance_fraction) % math.pi
            pelvis_height += self.RUN_FLIGHT_RISE * max(0.0, math.sin(swing_phase))
        translations = {"pelvis": (0.0, 0.0, pelvis_height)}

        smoothing_time = 0.055
        weight = 1.0 - math.exp(-max(0.0, delta_seconds) / smoothing_time)
        if not self._smoothed_rotations:
            self._smoothed_rotations = dict(rotations)
            self._smoothed_translations = dict(translations)
        else:
            self._smoothed_rotations = self._blend(
                self._smoothed_rotations, rotations, weight
            )
            self._smoothed_translations = self._blend(
                self._smoothed_translations, translations, weight
            )
        return dict(self._smoothed_rotations), dict(self._smoothed_translations)

    @staticmethod
    def _blend(previous, target, weight):
        blended = {}
        for name in set(previous) | set(target):
            first = previous.get(name, target.get(name, (0.0, 0.0, 0.0)))
            second = target.get(name, first)
            blended[name] = tuple(
                first[index] + (second[index] - first[index]) * weight
                for index in range(3)
            )
        return blended



__all__ = ["HumanoidFootLockSolver3D", "TwoBoneIKResult", "solve_two_bone_ik"]
