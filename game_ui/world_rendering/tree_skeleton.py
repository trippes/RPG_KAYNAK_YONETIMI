"""PNG-independent tree geometry and animation skeleton definitions.

The skeleton is authored in its own normalized local coordinate space.
Artwork is only a visual skin mapped onto this geometry by the renderer.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


def _point(value, name):
    if len(value) != 2:
        raise ValueError(f"{name} must contain two normalized coordinates.")
    if any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(item)
        or not 0.0 <= item <= 1.0
        for item in value
    ):
        raise ValueError(f"{name} coordinates must be finite values from 0 to 1.")
    return tuple(float(item) for item in value)


def _rect(value, name):
    if len(value) != 4:
        raise ValueError(f"{name} must contain normalized x, y, width and height.")
    if any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(item)
        for item in value
    ):
        raise ValueError(f"{name} values must be finite numbers.")
    x, y, width, height = (float(item) for item in value)
    if x < 0 or y < 0 or width < 0 or height < 0 or x + width > 1 or y + height > 1:
        raise ValueError(f"{name} must fit inside the normalized rectangle.")
    return x, y, width, height


def _unit_interval(value, name):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not 0.0 <= value <= 1.0
    ):
        raise ValueError(f"{name} must be a finite value from 0 to 1.")
    return float(value)


@dataclass(frozen=True, slots=True)
class TreeBranch:
    """One articulated branch in tree-local space, independent of any PNG."""

    start: tuple[float, float]
    end: tuple[float, float]
    thickness: float = 0.08
    sway_weight: float = 0.45
    phase: float = 0.0
    parent_index: int | None = None

    def __post_init__(self):
        object.__setattr__(self, "start", _point(self.start, "branch.start"))
        object.__setattr__(self, "end", _point(self.end, "branch.end"))
        object.__setattr__(self, "thickness", _unit_interval(self.thickness, "branch.thickness"))
        object.__setattr__(self, "sway_weight", _unit_interval(self.sway_weight, "branch.sway_weight"))
        if isinstance(self.phase, bool) or not isinstance(self.phase, (int, float)) or not math.isfinite(self.phase):
            raise ValueError("branch.phase must be a finite number.")
        if self.parent_index is not None and (
            isinstance(self.parent_index, bool)
            or not isinstance(self.parent_index, int)
            or self.parent_index < 0
        ):
            raise ValueError("branch.parent_index must be a non-negative index or None.")


@dataclass(frozen=True, slots=True)
class TreeLeafCluster:
    """A foliage cluster attached to a branch endpoint or tree-local point."""

    anchor: tuple[float, float]
    radius: float = 0.12
    sway_weight: float = 1.0
    phase: float = 0.0
    branch_index: int | None = None

    def __post_init__(self):
        object.__setattr__(self, "anchor", _point(self.anchor, "leaf_cluster.anchor"))
        object.__setattr__(self, "radius", _unit_interval(self.radius, "leaf_cluster.radius"))
        object.__setattr__(self, "sway_weight", _unit_interval(self.sway_weight, "leaf_cluster.sway_weight"))
        if isinstance(self.phase, bool) or not isinstance(self.phase, (int, float)) or not math.isfinite(self.phase):
            raise ValueError("leaf_cluster.phase must be a finite number.")
        if self.branch_index is not None and (
            isinstance(self.branch_index, bool)
            or not isinstance(self.branch_index, int)
            or self.branch_index < 0
        ):
            raise ValueError("leaf_cluster.branch_index must be a non-negative index or None.")


_DEFAULT_TRUNK = TreeBranch(
    (0.50, 0.985), (0.50, 0.68),
    thickness=0.18, sway_weight=0.08, phase=0.4,
)
_DEFAULT_BRANCHES = (
    TreeBranch((0.50, 0.78), (0.22, 0.48), thickness=0.12, sway_weight=0.30, phase=0.2),
    TreeBranch((0.50, 0.76), (0.78, 0.42), thickness=0.11, sway_weight=0.32, phase=1.1),
    TreeBranch((0.22, 0.48), (0.34, 0.25), thickness=0.075, sway_weight=0.62, phase=2.0, parent_index=0),
    TreeBranch((0.78, 0.42), (0.88, 0.22), thickness=0.07, sway_weight=0.66, phase=3.0, parent_index=1),
)
_DEFAULT_LEAF_CLUSTERS = (
    TreeLeafCluster((0.22, 0.48), radius=0.18, phase=0.0, branch_index=0),
    TreeLeafCluster((0.78, 0.42), radius=0.19, phase=1.2, branch_index=1),
    TreeLeafCluster((0.34, 0.25), radius=0.17, phase=2.4, branch_index=2),
    TreeLeafCluster((0.88, 0.22), radius=0.16, phase=3.6, branch_index=3),
    TreeLeafCluster((0.52, 0.20), radius=0.22, phase=4.8),
)


@dataclass(frozen=True, slots=True)
class TreeSkeleton:
    """Tree-local geometry plus legacy artwork attachment metadata.

    Branches, foliage clusters and animation weights are defined in a
    normalized skeleton space, not measured from the PNG. The legacy sprite
    anchors remain an adapter for the current artwork renderer.
    """

    ground_anchor: tuple[float, float] = (0.5, 0.985)
    depth_anchor: tuple[float, float] = (0.5, 0.955)
    trunk_collision: tuple[float, float, float, float] = (0.39, 0.82, 0.22, 0.16)
    canopy_bounds: tuple[float, float, float, float] = (0.03, 0.02, 0.94, 0.76)
    trunk: TreeBranch = _DEFAULT_TRUNK
    branches: tuple[TreeBranch, ...] = _DEFAULT_BRANCHES
    leaf_clusters: tuple[TreeLeafCluster, ...] = _DEFAULT_LEAF_CLUSTERS
    wind_response: float = 0.7
    sway_frequency: float = 1.0

    def __post_init__(self):
        object.__setattr__(self, "ground_anchor", _point(self.ground_anchor, "ground_anchor"))
        object.__setattr__(self, "depth_anchor", _point(self.depth_anchor, "depth_anchor"))
        object.__setattr__(self, "trunk_collision", _rect(self.trunk_collision, "trunk_collision"))
        object.__setattr__(self, "canopy_bounds", _rect(self.canopy_bounds, "canopy_bounds"))
        if not isinstance(self.trunk, TreeBranch):
            raise ValueError("trunk must be a TreeBranch.")
        branches = tuple(self.branches)
        leaves = tuple(self.leaf_clusters)
        if any(not isinstance(branch, TreeBranch) for branch in branches):
            raise ValueError("branches must contain TreeBranch values.")
        if any(not isinstance(cluster, TreeLeafCluster) for cluster in leaves):
            raise ValueError("leaf_clusters must contain TreeLeafCluster values.")
        for index, branch in enumerate(branches):
            if branch.parent_index is not None and branch.parent_index >= index:
                raise ValueError("branch.parent_index must refer to an earlier branch.")
        for cluster in leaves:
            if cluster.branch_index is not None and cluster.branch_index >= len(branches):
                raise ValueError("leaf_cluster.branch_index refers to a missing branch.")
        object.__setattr__(self, "branches", branches)
        object.__setattr__(self, "leaf_clusters", leaves)
        object.__setattr__(self, "wind_response", _unit_interval(self.wind_response, "wind_response"))
        if (
            isinstance(self.sway_frequency, bool)
            or not isinstance(self.sway_frequency, (int, float))
            or not math.isfinite(self.sway_frequency)
            or self.sway_frequency < 0
        ):
            raise ValueError("sway_frequency must be a finite non-negative number.")
        object.__setattr__(self, "sway_frequency", float(self.sway_frequency))

    def _sway_offset(self, weight, phase, time_seconds):
        """Small local-space wind displacement; roots remain anchored."""
        angle = time_seconds * self.sway_frequency + phase
        amplitude = self.wind_response * weight
        return (
            math.sin(angle) * amplitude * 0.014,
            math.cos(angle * 0.83) * amplitude * 0.004,
        )

    def animated_trunk_points(self, time_seconds):
        """Return trunk endpoints with a restrained top sway and fixed ground root."""
        offset = self._sway_offset(
            self.trunk.sway_weight, self.trunk.phase, time_seconds
        )
        return self.trunk.start, (
            self.trunk.end[0] + offset[0],
            self.trunk.end[1] + offset[1],
        )

    def animated_branch_points(self, index, time_seconds):
        """Return a branch pose, inheriting its parent's endpoint movement."""
        if not 0 <= index < len(self.branches):
            raise IndexError("branch index is outside this skeleton.")
        branch = self.branches[index]
        inherited = (0.0, 0.0)
        if branch.parent_index is not None:
            _, parent_end = self.animated_branch_points(
                branch.parent_index, time_seconds
            )
            parent = self.branches[branch.parent_index]
            inherited = (
                parent_end[0] - parent.end[0],
                parent_end[1] - parent.end[1],
            )
        sway = self._sway_offset(branch.sway_weight, branch.phase, time_seconds)
        return (
            (branch.start[0] + inherited[0], branch.start[1] + inherited[1]),
            (
                branch.end[0] + inherited[0] + sway[0],
                branch.end[1] + inherited[1] + sway[1],
            ),
        )

    def animated_leaf_anchor(self, index, time_seconds):
        """Return foliage position following its parent branch plus its own wind."""
        if not 0 <= index < len(self.leaf_clusters):
            raise IndexError("leaf cluster index is outside this skeleton.")
        cluster = self.leaf_clusters[index]
        inherited = (0.0, 0.0)
        if cluster.branch_index is not None:
            _, endpoint = self.animated_branch_points(
                cluster.branch_index, time_seconds
            )
            branch = self.branches[cluster.branch_index]
            inherited = (
                endpoint[0] - branch.end[0],
                endpoint[1] - branch.end[1],
            )
        sway = self._sway_offset(
            cluster.sway_weight, cluster.phase, time_seconds
        )
        return (
            cluster.anchor[0] + inherited[0] + sway[0],
            cluster.anchor[1] + inherited[1] + sway[1],
        )

    def sprite_top_left(self, world_anchor, sprite_size, scale=1.0):
        """Return the artwork's top-left world point for its ground anchor."""
        width, height = self._scaled_size(sprite_size, scale)
        return (
            float(world_anchor[0]) - width * self.ground_anchor[0],
            float(world_anchor[1]) - height * self.ground_anchor[1],
        )

    def depth_y(self, world_anchor, sprite_size, scale=1.0):
        """Return the world-space depth line, independent of canopy height."""
        _, height = self._scaled_size(sprite_size, scale)
        return float(world_anchor[1]) + height * (
            self.depth_anchor[1] - self.ground_anchor[1]
        )

    def trunk_collision_bounds(self, world_anchor, sprite_size, scale=1.0):
        """Return the legacy artwork-adapter trunk rectangle in world coordinates."""
        width, height = self._scaled_size(sprite_size, scale)
        left, top = self.sprite_top_left(world_anchor, sprite_size, scale)
        x, y, collision_width, collision_height = self.trunk_collision
        return (
            left + x * width,
            top + y * height,
            collision_width * width,
            collision_height * height,
        )

    @staticmethod
    def _scaled_size(sprite_size, scale):
        if len(sprite_size) != 2:
            raise ValueError("sprite_size must contain width and height.")
        width, height = sprite_size
        if (
            isinstance(width, bool) or isinstance(height, bool)
            or not isinstance(width, (int, float))
            or not isinstance(height, (int, float))
            or width <= 0 or height <= 0
            or not math.isfinite(width) or not math.isfinite(height)
        ):
            raise ValueError("sprite dimensions must be finite positive numbers.")
        if (
            isinstance(scale, bool) or not isinstance(scale, (int, float))
            or not math.isfinite(scale) or scale <= 0
        ):
            raise ValueError("scale must be a finite positive number.")
        return float(width) * float(scale), float(height) * float(scale)


DEFAULT_TREE_SKELETON = TreeSkeleton()
