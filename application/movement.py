"""Deterministic actor movement driven by the canonical simulation scheduler."""

from __future__ import annotations

from dataclasses import dataclass

from core.foundation import ActionId, Identifier
from core.simulation.event_types import CanonicalEventType
from core.simulation.events import SimulationEvent
from core.time import Tick
from core.domain.spatial import Position
from world import WorldMap
from world.movement import MovementActionView, MovementState


@dataclass
class _Movement:
    action_id: str
    actor_id: str
    world_id: str
    path: tuple[str, ...]
    start_tick: Tick
    end_tick: Tick
    state: MovementState = MovementState.SCHEDULED

    def view(self):
        return MovementActionView(
            self.action_id, self.actor_id, self.world_id, self.path[0],
            self.path[-1], self.path, self.start_tick.value, self.end_tick.value,
            self.state.value,
        )


class MovementManager:
    """Plans movement immediately and applies it on action completion."""

    def __init__(self, actors, runtime):
        self._actors = actors
        self._runtime = runtime
        self._maps: dict[str, WorldMap] = {}
        self._movements: dict[str, _Movement] = {}
        self._bound = False

    def register_map(self, world_map: WorldMap) -> None:
        if not isinstance(world_map, WorldMap):
            raise TypeError("world_map must be WorldMap.")
        if world_map.world_id in self._maps:
            raise ValueError(f"Map already registered: {world_map.world_id}")
        self._maps[world_map.world_id] = world_map

    def map_for(self, world_id: str) -> WorldMap | None:
        return self._maps.get(world_id)

    def set_position(self, actor_id: str, location_id: str) -> None:
        actor = self._actors._require(actor_id)
        world_map = self._require_map(actor.world_id)
        if world_map.get(location_id) is None:
            raise KeyError(f"Location not found: {location_id}")
        actor.set_position(location_id)

    def set_tile_position(self, actor_id: str, x: int, y: int, size: int = 32) -> None:
        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError("Tile coordinates must be integers.")
        if not 0 <= x < size or not 0 <= y < size:
            raise ValueError(f"Tile coordinates must be within 0..{size - 1}.")
        actor = self._actors._require(actor_id)
        if actor.location_id is None:
            raise ValueError("Actor has no current location.")
        actor.set_position(actor.location_id, Position(x, y))

    def move(self, actor_id: str, destination_id: str, action_id: str | None = None) -> MovementActionView:
        if not self._bound:
            self._runtime.dispatcher.register(self)
            self._bound = True
        actor = self._actors._require(actor_id)
        if not actor.active:
            raise ValueError(f"Actor is inactive: {actor_id}")
        if actor.activity_id is not None:
            raise ValueError(f"Actor is busy: {actor_id}")
        if actor.location_id is None:
            raise ValueError("Actor has no starting location.")
        world_map = self._require_map(actor.world_id)
        path = world_map.find_path(actor.location_id, destination_id)
        if action_id is None:
            action_id = f"move_{len(self._movements) + 1:06d}"
        if action_id in self._movements:
            raise ValueError(f"Duplicate movement action: {action_id}")
        duration = Tick(len(path) - 1)
        action = self._runtime.actions.create(
            Identifier(actor_id), duration,
            {"movement_action_id": action_id, "destination_id": destination_id},
            ActionId(f"movement_{action_id}"),
        )
        self._runtime.actions.schedule(action.action_id, self._runtime.current_tick)
        movement = _Movement(action_id, actor_id, actor.world_id, path,
                             self._runtime.current_tick,
                             self._runtime.current_tick + duration)
        self._movements[str(action.action_id)] = movement
        return movement.view()

    def get(self, action_id: str) -> MovementActionView | None:
        return next((movement.view() for movement in self._movements.values() if movement.action_id == action_id), None)

    def movements(self) -> tuple[MovementActionView, ...]:
        return tuple(movement.view() for movement in sorted(self._movements.values(), key=lambda item: item.action_id))

    def consume(self, event: SimulationEvent) -> None:
        if event.event_type != CanonicalEventType.ACTION_COMPLETED or event.action_id is None:
            return
        movement = self._movements.get(str(event.action_id))
        if movement is None or movement.state != MovementState.SCHEDULED:
            return
        actor = self._actors._require(movement.actor_id)
        destination = self._maps[movement.world_id].get(movement.path[-1])
        position = destination.position if destination is not None else None
        actor.set_position(
            movement.path[-1],
            position if isinstance(position, Position) else None,
        )
        movement.state = MovementState.COMPLETED

    def _require_map(self, world_id: str) -> WorldMap:
        world_map = self._maps.get(world_id)
        if world_map is None:
            raise KeyError(f"No movement map registered for world: {world_id}")
        return world_map
