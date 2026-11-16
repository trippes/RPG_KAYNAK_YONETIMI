"""Pygame-independent camera controller, zoom, follow, and bounds policy."""

from __future__ import annotations

from enum import Enum
import math

from hex_world_lab.geometry import WorldPoint

from .bounds import WorldBounds, clamp_camera_center
from .coordinates import Viewport
from .follow import CameraFollowController
from .state import CameraState
from .transform import WorldScreenTransform


class CameraBoundsPolicy(Enum):
    """Presentation-only camera boundary behavior."""

    UNBOUNDED = "unbounded"
    CLAMP_TO_MAP = "clamp_to_map"


class CameraController:
    """Own camera state while exposing immutable snapshots to consumers."""

    __slots__ = (
        "_center",
        "_viewport",
        "_zoom",
        "_min_zoom",
        "_max_zoom",
        "_zoom_factor",
        "_follow",
        "_target",
        "_bounds",
        "_bounds_policy",
    )

    def __init__(
        self,
        viewport: Viewport,
        center: WorldPoint = WorldPoint(0.0, 0.0),
        *,
        zoom: float = 1.0,
        min_zoom: float = 0.5,
        max_zoom: float = 3.0,
        zoom_factor: float = 1.1,
        follow_smoothing: float = 8.0,
        bounds: WorldBounds | None = None,
        bounds_policy: CameraBoundsPolicy = CameraBoundsPolicy.UNBOUNDED,
    ) -> None:
        if not isinstance(viewport, Viewport):
            raise TypeError("viewport must be a Viewport")
        if not isinstance(center, WorldPoint):
            raise TypeError("center must be a WorldPoint")
        for name, value in (
            ("min_zoom", min_zoom),
            ("max_zoom", max_zoom),
            ("zoom_factor", zoom_factor),
            ("zoom", zoom),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be a real number")
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if min_zoom <= 0.0:
            raise ValueError("min_zoom must be greater than zero")
        if max_zoom < min_zoom:
            raise ValueError("max_zoom must be greater than or equal to min_zoom")
        if zoom_factor <= 1.0:
            raise ValueError("zoom_factor must be greater than one")
        if bounds is not None and not isinstance(bounds, WorldBounds):
            raise TypeError("bounds must be a WorldBounds or None")
        if not isinstance(bounds_policy, CameraBoundsPolicy):
            raise TypeError("bounds_policy must be a CameraBoundsPolicy")
        if bounds_policy is CameraBoundsPolicy.CLAMP_TO_MAP and bounds is None:
            raise ValueError("CLAMP_TO_MAP requires world bounds")

        self._viewport = viewport
        self._center = center
        self._min_zoom = float(min_zoom)
        self._max_zoom = float(max_zoom)
        self._zoom_factor = float(zoom_factor)
        self._zoom = self._clamp_zoom(float(zoom))
        self._follow = CameraFollowController(smoothing=follow_smoothing)
        self._target: WorldPoint | None = None
        self._bounds = bounds
        self._bounds_policy = bounds_policy
        self._apply_bounds()

    @property
    def state(self) -> CameraState:
        """Return an immutable snapshot of the current camera."""
        return CameraState(self._center, self._viewport, self._zoom)

    @property
    def transform(self) -> WorldScreenTransform:
        """Return the world/screen transform for the current snapshot."""
        state = self.state
        return WorldScreenTransform(state.viewport, state.center, state.zoom)

    @property
    def min_zoom(self) -> float:
        return self._min_zoom

    @property
    def max_zoom(self) -> float:
        return self._max_zoom

    @property
    def target(self) -> WorldPoint | None:
        return self._target

    @property
    def bounds(self) -> WorldBounds | None:
        return self._bounds

    @property
    def bounds_policy(self) -> CameraBoundsPolicy:
        return self._bounds_policy

    def set_zoom(self, zoom: float) -> float:
        """Set zoom, clamping it to the configured inclusive limits."""
        if isinstance(zoom, bool) or not isinstance(zoom, (int, float)):
            raise TypeError("zoom must be a real number")
        if not math.isfinite(zoom):
            raise ValueError("zoom must be finite")
        self._zoom = self._clamp_zoom(float(zoom))
        self._apply_bounds()
        return self._zoom

    def zoom_by_steps(self, steps: int) -> float:
        """Apply discrete wheel steps; positive values zoom in."""
        if isinstance(steps, bool) or not isinstance(steps, int):
            raise TypeError("steps must be an integer")
        target_log = math.log(self._zoom) + steps * math.log(self._zoom_factor)
        if target_log >= math.log(self._max_zoom):
            return self.set_zoom(self._max_zoom)
        if target_log <= math.log(self._min_zoom):
            return self.set_zoom(self._min_zoom)
        return self.set_zoom(math.exp(target_log))

    def set_viewport(self, viewport: Viewport) -> None:
        """Update drawable dimensions without changing world center or zoom."""
        if not isinstance(viewport, Viewport):
            raise TypeError("viewport must be a Viewport")
        self._viewport = viewport
        self._apply_bounds()

    def set_center(self, center: WorldPoint) -> None:
        """Set the camera center in authoritative world coordinates."""
        if not isinstance(center, WorldPoint):
            raise TypeError("center must be a WorldPoint")
        self._center = center
        self._apply_bounds()

    def set_target(self, target: WorldPoint | None) -> None:
        """Set or clear the world-space point followed by the camera."""
        if target is not None and not isinstance(target, WorldPoint):
            raise TypeError("target must be a WorldPoint or None")
        self._target = target

    def set_bounds(
        self,
        bounds: WorldBounds | None,
        policy: CameraBoundsPolicy = CameraBoundsPolicy.UNBOUNDED,
    ) -> None:
        """Set presentation bounds independently of physical world boundaries."""
        if bounds is not None and not isinstance(bounds, WorldBounds):
            raise TypeError("bounds must be a WorldBounds or None")
        if not isinstance(policy, CameraBoundsPolicy):
            raise TypeError("policy must be a CameraBoundsPolicy")
        if policy is CameraBoundsPolicy.CLAMP_TO_MAP and bounds is None:
            raise ValueError("CLAMP_TO_MAP requires world bounds")
        self._bounds = bounds
        self._bounds_policy = policy
        self._apply_bounds()

    def update(self, delta_seconds: float) -> CameraState:
        """Advance camera follow by render time and return a state snapshot."""
        self._center = self._follow.update(
            self._center, self._target, delta_seconds
        )
        self._apply_bounds()
        return self.state

    def _apply_bounds(self) -> None:
        if (
            self._bounds_policy is CameraBoundsPolicy.CLAMP_TO_MAP
            and self._bounds is not None
        ):
            self._center = clamp_camera_center(
                self._center, self._bounds, self._viewport, self._zoom
            )

    def _clamp_zoom(self, zoom: float) -> float:
        return min(self._max_zoom, max(self._min_zoom, zoom))
