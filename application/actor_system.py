"""Application-level world actors and canonical-runtime activities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.simulation.event_types import CanonicalEventType
from core.simulation.events import SimulationEvent
from core.time import Tick

from resources import ProductionJobManager, ProductionJobState, Quantity
from core.domain.spatial import Position

from .production_facility import ProductionFacilityRegistry


class ActorError(ValueError):
    """Invalid actor or actor registry operation."""


class ActivityError(ValueError):
    """Invalid activity lifecycle or target operation."""


class ActivityState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ActorView:
    actor_id: str
    world_id: str
    role: str
    active: bool
    activity_id: str | None
    character_id: str | None = None
    location_id: str | None = None
    position: Position | None = None


@dataclass(frozen=True)
class ActivityView:
    activity_id: str
    actor_id: str
    activity_type: str
    state: str
    start_tick: int
    end_tick: int | None
    target_id: str | None
    inventory_id: str | None
    facility_id: str | None
    job_id: str | None
    reason: str | None


class WorldActor:
    """Mutable actor record kept outside Core canonical state."""

    def __init__(self, actor_id: str, world_id: str, role: str, active: bool = True, character_id: str | None = None, location_id: str | None = None, position: Position | None = None):
        _text(actor_id, "actor_id")
        _text(world_id, "world_id")
        _text(role, "role")
        if not isinstance(active, bool):
            raise TypeError("active must be boolean.")
        if character_id is not None:
            _text(character_id, "character_id")
        self._actor_id = actor_id
        self._world_id = world_id
        self._role = role
        self._active = active
        self._activity_id: str | None = None
        self._character_id = character_id
        self._location_id = location_id
        self._position = position if position is not None else Position()

    @property
    def actor_id(self) -> str:
        return self._actor_id

    @property
    def world_id(self) -> str:
        return self._world_id

    @property
    def role(self) -> str:
        return self._role

    @property
    def active(self) -> bool:
        return self._active

    @property
    def activity_id(self) -> str | None:
        return self._activity_id

    @property
    def character_id(self) -> str | None:
        return self._character_id

    @property
    def location_id(self) -> str | None:
        return self._location_id

    @property
    def position(self) -> Position | None:
        return self._position

    def set_position(self, location_id: str, position: Position | None = None) -> None:
        _text(location_id, "location_id")
        if position is not None and not isinstance(position, Position):
            raise TypeError("position must be Position.")
        self._location_id = location_id
        if position is not None:
            self._position = position

    def bind_character(self, character_id: str) -> None:
        _text(character_id, "character_id")
        if self._character_id is not None and self._character_id != character_id:
            raise ActorError(f"Actor already references character: {self._actor_id}")
        self._character_id = character_id

    def set_active(self, active: bool) -> None:
        if not isinstance(active, bool):
            raise TypeError("active must be boolean.")
        if not active and self._activity_id is not None:
            raise ActorError("An actor with an active activity cannot be deactivated.")
        self._active = active

    def begin_activity(self, activity_id: str) -> None:
        if not self._active:
            raise ActorError(f"Actor is inactive: {self._actor_id}")
        if self._activity_id is not None:
            raise ActorError(f"Actor already has an active activity: {self._actor_id}")
        _text(activity_id, "activity_id")
        self._activity_id = activity_id

    def clear_activity(self, activity_id: str) -> None:
        if self._activity_id == activity_id:
            self._activity_id = None

    def view(self) -> ActorView:
        return ActorView(
            self._actor_id, self._world_id, self._role,
            self._active, self._activity_id,
            self._character_id,
            self._location_id, self._position,
        )


class WorldActorRegistry:
    """Deterministic world-bound actor registry."""

    def __init__(self, world_registry=None) -> None:
        self._actors: dict[str, WorldActor] = {}
        self._world_registry = None
        if world_registry is not None:
            self.bind_world_registry(world_registry)

    @property
    def world_registry(self):
        return self._world_registry

    def bind_world_registry(self, world_registry) -> None:
        if not callable(getattr(world_registry, "exists", None)):
            raise TypeError("world_registry must provide exists(world_id).")
        missing = sorted(
            actor.world_id for actor in self._actors.values()
            if not world_registry.exists(actor.world_id)
        )
        if missing:
            raise ActorError(f"Actors reference unknown worlds: {missing}")
        self._world_registry = world_registry

    def validate(self) -> None:
        if self._world_registry is None:
            return
        missing = sorted(
            actor.world_id for actor in self._actors.values()
            if not self._world_registry.exists(actor.world_id)
        )
        if missing:
            raise ActorError(f"Actors reference unknown worlds: {missing}")

    def add(self, actor: WorldActor) -> None:
        if not isinstance(actor, WorldActor):
            raise TypeError("actor must be WorldActor.")
        if actor.actor_id in self._actors:
            raise ActorError(f"Duplicate actor ID: {actor.actor_id}")
        if self._world_registry is not None and not self._world_registry.exists(actor.world_id):
            raise ActorError(f"Actor references unknown world: {actor.world_id}")
        self._actors[actor.actor_id] = actor

    def get(self, actor_id: str) -> ActorView | None:
        return self._actors.get(actor_id).view() if actor_id in self._actors else None

    def for_world(self, world_id: str) -> tuple[ActorView, ...]:
        _text(world_id, "world_id")
        return tuple(
            self._actors[actor_id].view()
            for actor_id in sorted(self._actors)
            if self._actors[actor_id].world_id == world_id
        )

    def actors(self) -> tuple[ActorView, ...]:
        return tuple(self._actors[actor_id].view() for actor_id in sorted(self._actors))

    def count(self) -> int:
        return len(self._actors)

    def remove(self, actor_id: str) -> ActorView:
        actor = self._actors.pop(actor_id, None)
        if actor is None:
            raise KeyError(f"Actor not found: {actor_id}")
        return actor.view()

    def set_active(self, actor_id: str, active: bool) -> None:
        self._require(actor_id).set_active(active)

    def bind_character(self, actor_id: str, character) -> None:
        """Bind a character aggregate to an existing world actor."""
        if not callable(getattr(character, "bind_actor", None)):
            raise TypeError("character must provide bind_actor(actor_id).")
        actor = self._require(actor_id)
        if actor.character_id is not None and actor.character_id != character.character_id:
            raise ActorError(f"Actor already references character: {actor_id}")
        if getattr(character, "actor_id", None) is not None and character.actor_id != actor_id:
            raise ActorError(f"Character already references another actor: {character.character_id}")
        # Both sides are checked before either side is mutated.
        character.bind_actor(actor_id)
        actor.bind_character(character.character_id)

    def _require(self, actor_id: str) -> WorldActor:
        actor = self._actors.get(actor_id)
        if actor is None:
            raise KeyError(f"Actor not found: {actor_id}")
        return actor


class ActorActivity:
    """One activity lifecycle record."""

    def __init__(
        self,
        activity_id: str,
        actor_id: str,
        activity_type: str,
        start_tick: Tick,
        target_id: str | None = None,
        inventory_id: str | None = None,
        facility_id: str | None = None,
    ) -> None:
        for value, name in ((activity_id, "activity_id"), (actor_id, "actor_id"), (activity_type, "activity_type")):
            _text(value, name)
        if not isinstance(start_tick, Tick):
            raise TypeError("start_tick must be Tick.")
        self.activity_id = activity_id
        self.actor_id = actor_id
        self.activity_type = activity_type
        self.start_tick = start_tick
        self.end_tick: Tick | None = None
        self.target_id = target_id
        self.inventory_id = inventory_id
        self.facility_id = facility_id
        self.job_id: str | None = None
        self.state = ActivityState.PENDING
        self.reason: str | None = None

    def start(self) -> None:
        if self.state != ActivityState.PENDING:
            raise ActivityError("Only a pending activity can start.")
        self.state = ActivityState.RUNNING

    def complete(self, end_tick: Tick, reason: str | None = None) -> None:
        if self.state != ActivityState.RUNNING:
            raise ActivityError("Only a running activity can complete.")
        if end_tick < self.start_tick:
            raise ActivityError("Activity completion cannot precede its start.")
        self.end_tick = end_tick
        self.reason = reason
        self.state = ActivityState.COMPLETED

    def fail(self, reason: str) -> None:
        if self.state not in {ActivityState.PENDING, ActivityState.RUNNING}:
            return
        self.reason = _text(reason, "reason")
        self.state = ActivityState.FAILED

    def cancel(self, reason: str) -> None:
        if self.state not in {ActivityState.PENDING, ActivityState.RUNNING}:
            raise ActivityError("Only pending or running activities can be cancelled.")
        self.reason = _text(reason, "reason")
        self.state = ActivityState.CANCELLED

    def view(self) -> ActivityView:
        return ActivityView(
            self.activity_id, self.actor_id, self.activity_type, self.state.value,
            self.start_tick.value,
            None if self.end_tick is None else self.end_tick.value,
            self.target_id, self.inventory_id, self.facility_id,
            self.job_id, self.reason,
        )


class ActorActivityManager:
    """Coordinate actor activities with existing production action events."""

    def __init__(
        self,
        actors: WorldActorRegistry,
        production_jobs: ProductionJobManager,
        facilities: ProductionFacilityRegistry,
    ) -> None:
        if not isinstance(actors, WorldActorRegistry):
            raise TypeError("actors must be WorldActorRegistry.")
        if not isinstance(production_jobs, ProductionJobManager):
            raise TypeError("production_jobs must be ProductionJobManager.")
        if not isinstance(facilities, ProductionFacilityRegistry):
            raise TypeError("facilities must be ProductionFacilityRegistry.")
        self._actors = actors
        self._jobs = production_jobs
        self._facilities = facilities
        self._activities: dict[str, ActorActivity] = {}
        self._job_to_activity = {}
        self._runtime = None
        self._next_activity_id = 1

    @property
    def actors(self) -> WorldActorRegistry:
        return self._actors

    @property
    def runtime(self):
        return self._jobs.runtime

    @property
    def production_jobs(self) -> ProductionJobManager:
        return self._jobs

    @property
    def facilities(self) -> ProductionFacilityRegistry:
        return self._facilities

    def count(self) -> int:
        return len(self._activities)

    def get(self, activity_id: str) -> ActivityView | None:
        activity = self._activities.get(activity_id)
        return None if activity is None else activity.view()

    def activities(self) -> tuple[ActivityView, ...]:
        return tuple(self._activities[key].view() for key in sorted(self._activities))

    def start_gathering(self, activity_id, actor_id, node_id, inventory_id, quantity, gameplay_service):
        activity = self._create(
            activity_id, actor_id, "gather", node_id, inventory_id=inventory_id,
        )
        actor = self._actors._require(actor_id)
        try:
            actor.begin_activity(activity.activity_id)
            activity.start()
        except Exception:
            self._activities.pop(activity.activity_id, None)
            raise
        try:
            gameplay_service.collect(node_id, inventory_id, quantity)
            activity.complete(self.runtime.current_tick)
        except Exception as error:
            activity.fail(str(error))
            raise
        finally:
            if activity.state in {ActivityState.COMPLETED, ActivityState.FAILED}:
                actor.clear_activity(activity.activity_id)
        return activity.view()

    def start_production(self, activity_id, actor_id, recipe_id, inventory_id, facility_id, gameplay_service):
        activity = self._create(
            activity_id, actor_id, "production", recipe_id,
            inventory_id=inventory_id, facility_id=facility_id,
        )
        actor = self._actors._require(actor_id)
        try:
            actor.begin_activity(activity.activity_id)
            activity.start()
        except Exception:
            self._activities.pop(activity.activity_id, None)
            raise
        try:
            job = gameplay_service.start_production(recipe_id, inventory_id, facility_id)
            activity.job_id = job.job_id
            activity.end_tick = job.end_tick
            self._job_to_activity[job.action_id] = activity.activity_id
            self._bind_runtime()
        except Exception as error:
            activity.fail(str(error))
            actor.clear_activity(activity.activity_id)
            raise
        return activity.view()

    def cancel(self, activity_id: str, reason: str = "cancelled") -> ActivityView:
        activity = self._require_activity(activity_id)
        if activity.state not in {ActivityState.PENDING, ActivityState.RUNNING}:
            raise ActivityError("Only pending or running activities can be cancelled.")
        actor = self._actors._require(activity.actor_id)
        if activity.job_id is not None:
            self._jobs.cancel(activity.job_id, reason)
        activity.cancel(reason)
        actor.clear_activity(activity.activity_id)
        return activity.view()

    def consume(self, event: SimulationEvent) -> None:
        if not isinstance(event, SimulationEvent) or event.action_id is None:
            return
        activity_id = self._job_to_activity.get(event.action_id)
        if activity_id is None:
            return
        activity = self._activities.get(activity_id)
        if activity is None or activity.state in {
            ActivityState.COMPLETED, ActivityState.FAILED, ActivityState.CANCELLED,
        }:
            return
        actor = self._actors._require(activity.actor_id)
        job = self._jobs.get(activity.job_id)
        if event.event_type == CanonicalEventType.ACTION_COMPLETED:
            if job is None or job.state != ProductionJobState.COMPLETED:
                return
            activity.complete(event.simulation_tick)
            actor.clear_activity(activity.activity_id)
        elif event.event_type == CanonicalEventType.ACTION_CANCELLED:
            activity.cancel("production job cancelled")
            actor.clear_activity(activity.activity_id)
        elif event.event_type == CanonicalEventType.ACTION_FAILED:
            activity.fail("production job failed")
            actor.clear_activity(activity.activity_id)

    def dispose(self) -> None:
        if self._runtime is not None:
            self._runtime.dispatcher.unregister(self)
            self._runtime = None

    def restore_activity(self, activity: ActorActivity, job_action_id=None) -> None:
        if activity.activity_id in self._activities:
            raise ActivityError(f"Duplicate activity ID: {activity.activity_id}")
        actor = self._actors._require(activity.actor_id)
        if activity.state in {ActivityState.PENDING, ActivityState.RUNNING}:
            actor.begin_activity(activity.activity_id)
        self._activities[activity.activity_id] = activity
        if activity.job_id is not None and job_action_id is not None:
            self._job_to_activity[job_action_id] = activity.activity_id
            self._bind_runtime()

    def _create(self, activity_id, actor_id, activity_type, target_id, inventory_id=None, facility_id=None):
        if activity_id is None:
            while f"activity_{self._next_activity_id:06d}" in self._activities:
                self._next_activity_id += 1
            activity_id = f"activity_{self._next_activity_id:06d}"
            self._next_activity_id += 1
        if not isinstance(activity_id, str) or not activity_id.strip():
            raise ValueError("activity_id must be a non-empty string.")
        if activity_id in self._activities:
            raise ActivityError(f"Duplicate activity ID: {activity_id}")
        if actor_id not in {actor.actor_id for actor in self._actors.actors()}:
            raise KeyError(f"Actor not found: {actor_id}")
        activity = ActorActivity(
            activity_id, actor_id, activity_type, self.runtime.current_tick,
            target_id, inventory_id, facility_id,
        )
        self._activities[activity_id] = activity
        return activity

    def _require_activity(self, activity_id: str) -> ActorActivity:
        activity = self._activities.get(activity_id)
        if activity is None:
            raise KeyError(f"Activity not found: {activity_id}")
        return activity

    def _bind_runtime(self) -> None:
        runtime = self._jobs.runtime
        if self._runtime is None:
            self._runtime = runtime
            runtime.dispatcher.register(self)
        elif self._runtime is not runtime:
            raise ActivityError("Activity manager cannot span runtimes.")


def _text(value, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{name} must be a non-empty string.")
    return value


__all__ = [
    "ActorError", "ActivityError", "ActivityState", "ActorView", "ActivityView",
    "WorldActor", "WorldActorRegistry", "ActorActivity", "ActorActivityManager",
]
