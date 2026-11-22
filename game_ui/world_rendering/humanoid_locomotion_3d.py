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
    WALK_PELVIS_DROP = 0.09
    RUN_PELVIS_DROP = 0.08
    UPPER_LEG_LENGTH = 0.22
    LOWER_LEG_LENGTH = 0.228
    CONTACT_FORWARD = 0.02
    TARGET_QUANTIZATION = 1.0 / 64.0
    ANGLE_QUANTIZATION = 1.0 / 32.0
    SIDES = ("left", "right")

    def __init__(self):
        self._anchors = {side: None for side in self.SIDES}
        self._was_stance = {side: False for side in self.SIDES}
        self._last_results = {}

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

    def update(self, *, phase, state, world_position, yaw, world_scale, ground_anchor_z=-0.49):
        """Return stance IK rotations and pelvis translation for one frame."""
        if state not in {"walk", "run"} or world_position is None:
            self.reset()
            return {}, {}
        values = (*world_position, phase, yaw, world_scale, ground_anchor_z)
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
            raise ValueError("Foot-lock inputs must be finite.")
        if world_scale <= 0.0:
            raise ValueError("world_scale must be positive.")

        stance_fraction = self.RUN_STANCE_FRACTION if state == "run" else self.WALK_STANCE_FRACTION
        pelvis_drop = self.RUN_PELVIS_DROP if state == "run" else self.WALK_PELVIS_DROP
        cosine, sine = math.cos(yaw), math.sin(yaw)
        rotations = {}
        self._last_results.clear()

        for side in self.SIDES:
            leg_phase = (phase + (0.0 if side == "left" else math.pi)) % math.tau
            in_stance = leg_phase < math.tau * stance_fraction
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
            anchor = self._anchors[side]
            if not in_stance or anchor is None:
                continue

            world_dx = (anchor[0] - world_position[0]) / world_scale
            world_dy = (anchor[1] - world_position[1]) / world_scale
            local_x = world_dx * cosine + world_dy * sine
            local_y = -world_dx * sine + world_dy * cosine
            target_lateral = local_x - hip_x
            target_forward = round(local_y / self.TARGET_QUANTIZATION) * self.TARGET_QUANTIZATION
            target_lateral = (
                round(target_lateral / self.TARGET_QUANTIZATION)
                * self.TARGET_QUANTIZATION
            )
            target_down = abs(ground_anchor_z + 0.03) - 0.02 - pelvis_drop
            result = solve_two_bone_ik(
                target_forward, target_down,
                self.UPPER_LEG_LENGTH, self.LOWER_LEG_LENGTH
            )
            self._last_results[side] = result
            lateral_angle = -math.atan2(target_lateral, max(1e-6, target_down))
            hip_angle = round(result.hip_angle / self.ANGLE_QUANTIZATION) * self.ANGLE_QUANTIZATION
            knee_angle = round(result.knee_angle / self.ANGLE_QUANTIZATION) * self.ANGLE_QUANTIZATION
            lateral_angle = round(lateral_angle / self.ANGLE_QUANTIZATION) * self.ANGLE_QUANTIZATION
            rotations[f"hip_{side}"] = (hip_angle, lateral_angle, 0.0)
            rotations[f"knee_{side}"] = (knee_angle, 0.0, 0.0)
            rotations[f"ankle_{side}"] = (0.0, 0.0, 0.0)

        translations = {"pelvis": (0.0, 0.0, -pelvis_drop)} if self._last_results else {}
        return rotations, translations


__all__ = ["HumanoidFootLockSolver3D", "TwoBoneIKResult", "solve_two_bone_ik"]
