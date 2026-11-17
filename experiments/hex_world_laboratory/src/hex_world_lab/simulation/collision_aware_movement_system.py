"""60 TPS movement orchestration with continuous static-obstacle collision."""

from collections.abc import Iterable

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement import (
    MovementConfig,
    MovementIntegrator,
    MovementIntent,
    MovementState,
    Vector2,
)
from hex_world_lab.physics import (
    ActorBodyTransform,
    BodyDefinition,
    CircleShape,
    ContinuousCollisionResolution,
    HexMapCollisionGeometry,
    ObstacleDefinition,
    ObstacleCandidateProvider,
    resolve_continuous_motion,
)
from hex_world_lab.world.identity import MapId

from .movement_system import TICK_DELTA_SECONDS


class CollisionAwareMovementSystem:
    """Advance one actor while resolving its circular body against static obstacles.

    Passing a HexMapCollisionGeometry automatically includes blocked perimeter
    edges. Raw obstacle iterables may be bound to a map with map_id.
    """

    __slots__ = (
        "_integrator",
        "_state",
        "_body",
        "_obstacles",
        "_map_id",
        "_next_tick_number",
        "_max_impacts",
        "_last_resolution",
        "_candidate_provider",
    )

    def __init__(
        self,
        initial_state: MovementState,
        config: MovementConfig,
        body: BodyDefinition,
        obstacles: Iterable[ObstacleDefinition] | HexMapCollisionGeometry = (),
        *,
        map_id: MapId | None = None,
        first_tick_number: int = 0,
        max_impacts: int = 6,
        candidate_provider: ObstacleCandidateProvider | None = None,
    ) -> None:
        if not isinstance(initial_state, MovementState):
            raise TypeError("initial_state must be a MovementState")
        if not isinstance(config, MovementConfig):
            raise TypeError("config must be a MovementConfig")
        if not isinstance(body, BodyDefinition):
            raise TypeError("body must be a BodyDefinition")
        if not isinstance(body.collider, CircleShape):
            raise TypeError("continuous movement currently requires a circle body")
        if isinstance(first_tick_number, bool) or not isinstance(first_tick_number, int):
            raise TypeError("first_tick_number must be an integer")
        if first_tick_number < 0:
            raise ValueError("first_tick_number must not be negative")
        if isinstance(max_impacts, bool) or not isinstance(max_impacts, int):
            raise TypeError("max_impacts must be an integer")
        if max_impacts < 1:
            raise ValueError("max_impacts must be at least one")
        if map_id is not None and not isinstance(map_id, MapId):
            raise TypeError("map_id must be a MapId or None")

        if isinstance(obstacles, HexMapCollisionGeometry):
            if map_id is not None and map_id != obstacles.map_id:
                raise ValueError("map_id does not match collision geometry map")
            resolved_map_id = obstacles.map_id
            obstacle_values = obstacles.collision_obstacles
        else:
            obstacle_values = tuple(obstacles)
            resolved_map_id = map_id
        if any(not isinstance(item, ObstacleDefinition) for item in obstacle_values):
            raise TypeError("obstacles must contain ObstacleDefinition values")
        obstacle_ids = tuple(item.obstacle_id for item in obstacle_values)
        if len(obstacle_ids) != len(set(obstacle_ids)):
            raise ValueError("obstacle IDs must be unique")
        obstacle_maps = {item.map_id for item in obstacle_values}
        if len(obstacle_maps) > 1:
            raise ValueError("obstacles from different maps cannot share one movement system")
        if resolved_map_id is not None and any(
            item.map_id != resolved_map_id for item in obstacle_values
        ):
            raise ValueError("all obstacles must belong to the movement system map")
        if resolved_map_id is None and obstacle_maps:
            resolved_map_id = next(iter(obstacle_maps))

        self._integrator = MovementIntegrator(config)
        self._state = initial_state
        self._body = body
        self._obstacles = obstacle_values
        self._map_id = resolved_map_id
        self._next_tick_number = first_tick_number
        self._max_impacts = max_impacts
        if candidate_provider is not None and not callable(getattr(candidate_provider, "query", None)):
            raise TypeError("candidate_provider must provide query(bounds)")
        self._candidate_provider = candidate_provider
        self._last_resolution: ContinuousCollisionResolution | None = None

    @property
    def map_id(self) -> MapId | None:
        """Return the map scope associated with this movement system."""
        return self._map_id

    @property
    def state(self) -> MovementState:
        """Return the current immutable movement state."""
        return self._state

    @property
    def next_tick_number(self) -> int:
        """Return the only tick number currently accepted."""
        return self._next_tick_number

    @property
    def last_resolution(self) -> ContinuousCollisionResolution | None:
        """Return collision diagnostics from the most recently committed tick."""
        return self._last_resolution

    @staticmethod
    def _validate_tick_number(tick_number: int) -> None:
        if isinstance(tick_number, bool) or not isinstance(tick_number, int):
            raise TypeError("tick_number must be an integer")
        if tick_number < 0:
            raise ValueError("tick_number must not be negative")

    def step(self, tick_number: int, intent: MovementIntent) -> MovementState:
        """Compute movement, resolve collision, then atomically commit state/tick."""
        self._validate_tick_number(tick_number)
        if tick_number != self._next_tick_number:
            raise ValueError(
                f"expected tick {self._next_tick_number}, received {tick_number}"
            )
        if not isinstance(intent, MovementIntent):
            raise TypeError("intent must be a MovementIntent")

        proposed = self._integrator.step(
            self._state, intent, TICK_DELTA_SECONDS
        )
        resolution: ContinuousCollisionResolution | None = None

        if self._body.enabled:
            collider = ActorBodyTransform(self._state.position).transform_shape(
                self._body
            )
            displacement = Vector2(
                proposed.position.x - self._state.position.x,
                proposed.position.y - self._state.position.y,
            )
            resolution = resolve_continuous_motion(
                collider,
                displacement,
                self._obstacles,
                max_impacts=self._max_impacts,
                candidate_provider=self._candidate_provider,
            )
            if resolution.unresolved_penetration > 1e-7:
                raise RuntimeError(
                    "collision resolution left unresolved penetration: "
                    f"{resolution.unresolved_penetration}"
                )

            resolved_position = WorldPoint(
                self._state.position.x + resolution.applied_displacement.x,
                self._state.position.y + resolution.applied_displacement.y,
            )
            resolved_velocity = resolution.applied_displacement * (
                1.0 / TICK_DELTA_SECONDS
            )
            proposed = MovementState(
                resolved_position,
                resolved_velocity,
                proposed.mode,
            )

        # Commit only after integration and collision resolution both succeed.
        self._state = proposed
        self._last_resolution = resolution
        self._next_tick_number += 1
        return proposed
