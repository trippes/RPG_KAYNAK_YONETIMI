
"""Backward-compatible persistence records for actors and activities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from resources import ProductionJobManager, ProductionJobState, Quantity, ResourceUnit
from core.domain.spatial import Position

from .actor_system import (
    ActivityError,
    ActivityState,
    ActorActivity,
    ActorActivityManager,
    ActorError,
    WorldActor,
    WorldActorRegistry,
)
from .production_facility import ProductionFacilityRegistry


ACTOR_SCHEMA = "rpg-actors"
ACTOR_SCHEMA_VERSION = 1


class ActorPersistenceError(ValueError):
    """Invalid actor/activity snapshot."""


@dataclass(frozen=True)
class ActorRecord:
    actor_id: str
    world_id: str
    role: str
    active: bool
    activity_id: str | None
    character_id: str | None = None
    location_id: str | None = None
    position: Position | None = None


@dataclass(frozen=True)
class ActivityRecord:
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
    quantity: Quantity | None = None


@dataclass(frozen=True)
class ActorSnapshot:
    actors: tuple[ActorRecord, ...]
    activities: tuple[ActivityRecord, ...]

    @classmethod
    def from_runtime(
        cls,
        registry: WorldActorRegistry,
        manager: ActorActivityManager,
        characters=None,
    ) -> "ActorSnapshot":
        if not isinstance(registry, WorldActorRegistry):
            raise TypeError("registry must be WorldActorRegistry.")
        if not isinstance(manager, ActorActivityManager):
            raise TypeError("manager must be ActorActivityManager.")

        registry.validate()

        if characters is not None:
            _validate_character_links(registry.actors(), characters)

        actors = tuple(
            ActorRecord(
                view.actor_id,
                view.world_id,
                view.role,
                view.active,
                view.activity_id,
                view.character_id,
                view.location_id,
                view.position,
            )
            for view in registry.actors()
        )

        activities = tuple(
            ActivityRecord(
                view.activity_id,
                view.actor_id,
                view.activity_type,
                view.state,
                view.start_tick,
                view.end_tick,
                view.target_id,
                view.inventory_id,
                view.facility_id,
                view.job_id,
                view.reason,
                view.quantity,
            )
            for view in manager.activities()
        )

        actor_activity_ids = {
            record.activity_id for record in activities
        }

        for actor in actors:
            if (
                actor.activity_id is not None
                and actor.activity_id not in actor_activity_ids
            ):
                raise ActorPersistenceError(
                    "Actor references an unknown activity."
                )

        for activity in activities:
            if (
                activity.state
                in {
                    ActivityState.PENDING.value,
                    ActivityState.RUNNING.value,
                }
                and activity.activity_type == "production"
                and activity.job_id is None
            ):
                raise ActorPersistenceError("Active production activity must reference a job.")

        return cls(actors, activities)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": ACTOR_SCHEMA,
            "schema_version": ACTOR_SCHEMA_VERSION,
            "actors": [
                {
                    "actor_id": record.actor_id,
                    "world_id": record.world_id,
                    "role": record.role,
                    "active": record.active,
                    "activity_id": record.activity_id,
                    "character_id": record.character_id,
                    "location_id": record.location_id,
                    "position": (
                        record.position.to_dict()
                        if record.position is not None else None
                    ),
                }
                for record in self.actors
            ],
            "activities": [
                {
                    "activity_id": record.activity_id,
                    "actor_id": record.actor_id,
                    "activity_type": record.activity_type,
                    "state": record.state,
                    "start_tick": record.start_tick,
                    "end_tick": record.end_tick,
                    "target_id": record.target_id,
                    "inventory_id": record.inventory_id,
                    "facility_id": record.facility_id,
                    "job_id": record.job_id,
                    "reason": record.reason,
                    "quantity": (
                        {"value": record.quantity.value, "unit": record.quantity.unit.value}
                        if record.quantity is not None else None
                    ),
                }
                for record in self.activities
            ],
        }

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, object],
    ) -> "ActorSnapshot":
        if not isinstance(data, Mapping):
            raise ActorPersistenceError(
                "Actor snapshot must be an object."
            )

        if (
            data.get("schema") != ACTOR_SCHEMA
            or data.get("schema_version") != ACTOR_SCHEMA_VERSION
        ):
            raise ActorPersistenceError(
                "Unsupported actor persistence schema."
            )

        actors = tuple(
            _actor_record(item) for item in _list(data, "actors")
        )
        activities = tuple(
            _activity_record(item) for item in _list(data, "activities")
        )

        _unique((record.actor_id for record in actors), "actor")
        _unique(
            (record.activity_id for record in activities),
            "activity",
        )

        actor_ids = {record.actor_id for record in actors}

        for activity in activities:
            if activity.actor_id not in actor_ids:
                raise ActorPersistenceError(
                    "Activity references unknown actor."
                )

            if (
                activity.state
                in {
                    ActivityState.PENDING.value,
                    ActivityState.RUNNING.value,
                }
                and activity.activity_type == "production"
                and activity.job_id is None
            ):
                raise ActorPersistenceError(
                    "Active activity must reference a production job."
                )

        active_by_actor = {
            record.actor_id: record.activity_id
            for record in activities
            if record.state
            in {
                ActivityState.PENDING.value,
                ActivityState.RUNNING.value,
            }
        }

        for actor in actors:
            if actor.activity_id != active_by_actor.get(actor.actor_id):
                raise ActorPersistenceError(
                    "Actor/activity active-state mismatch."
                )

        return cls(
            tuple(sorted(actors, key=lambda record: record.actor_id)),
            tuple(
                sorted(
                    activities,
                    key=lambda record: record.activity_id,
                )
            ),
        )

    def restore(
        self,
        worlds,
        jobs: ProductionJobManager,
        nodes,
        facilities: ProductionFacilityRegistry,
        inventories: Mapping[str, object],
        recipes: Mapping[str, object],
        characters=None,
    ):
        if not isinstance(jobs, ProductionJobManager):
            raise TypeError("jobs must be ProductionJobManager.")

        if not isinstance(facilities, ProductionFacilityRegistry):
            raise TypeError(
                "facilities must be ProductionFacilityRegistry."
            )

        registry = WorldActorRegistry(worlds)

        try:
            for record in self.actors:
                registry.add(
                    WorldActor(
                        record.actor_id,
                        record.world_id,
                        record.role,
                        record.active,
                        record.character_id,
                        record.location_id,
                        record.position,
                    )
                )

            manager = ActorActivityManager(
                registry,
                jobs,
                facilities,
            )

            for record in self.activities:
                state = ActivityState(record.state)

                if (
                    record.inventory_id is not None
                    and record.inventory_id not in inventories
                ):
                    raise ActorPersistenceError(
                        "Activity references unknown inventory."
                    )

                if record.activity_type == "gather":
                    if (
                        record.target_id is None
                        or nodes.get(record.target_id) is None
                    ):
                        raise ActorPersistenceError(
                            "Gather activity references unknown node."
                        )

                if record.activity_type == "production":
                    if (
                        record.facility_id is None
                        or facilities.get(record.facility_id) is None
                    ):
                        raise ActorPersistenceError(
                            "Production activity references unknown facility."
                        )

                activity = ActorActivity(
                    record.activity_id,
                    record.actor_id,
                    record.activity_type,
                    _tick(record.start_tick),
                    record.target_id,
                    record.inventory_id,
                    record.facility_id,
                )

                activity.state = state
                activity.end_tick = (
                    None
                    if record.end_tick is None
                    else _tick(record.end_tick)
                )
                activity.job_id = record.job_id
                activity.reason = record.reason
                activity.quantity = record.quantity

                job_action_id = None

                if record.job_id is not None:
                    job = jobs.get(record.job_id)

                    if job is None:
                        raise ActorPersistenceError(
                            "Activity references unknown production job."
                        )

                    if (
                        record.activity_type == "production"
                        and job.recipe.recipe_id != record.target_id
                    ):
                        raise ActorPersistenceError(
                            "Activity/job recipe mismatch."
                        )

                    if state in {
                        ActivityState.PENDING,
                        ActivityState.RUNNING,
                    }:
                        if job.state not in {
                            ProductionJobState.PLANNED,
                            ProductionJobState.RUNNING,
                        }:
                            raise ActorPersistenceError(
                                "Active activity references a terminal job."
                            )

                        job_action_id = job.action_id

                manager.restore_activity(activity, job_action_id)

            for actor in self.actors:
                restored = registry.get(actor.actor_id)

                if restored is None:
                    raise ActorPersistenceError(
                        "Actor restore mismatch."
                    )

            if characters is not None:
                _validate_character_links(
                    registry.actors(),
                    characters,
                )

            return registry, manager

        except (
            ActorError,
            ActivityError,
            KeyError,
            ValueError,
            TypeError,
        ) as error:
            raise ActorPersistenceError(
                "Could not restore actors and activities."
            ) from error


def _validate_character_links(actors, characters):
    character_by_id = dict(characters)
    actor_by_id = {actor.actor_id: actor for actor in actors}

    for character in character_by_id.values():
        if character.actor_id is not None and (
            character.actor_id not in actor_by_id
            or actor_by_id[character.actor_id].character_id
            != character.character_id
        ):
            raise ActorPersistenceError(
                "Character references an invalid actor."
            )

    for actor in actors:
        if actor.character_id is not None and (
            actor.character_id not in character_by_id
            or character_by_id[actor.character_id].actor_id
            != actor.actor_id
        ):
            raise ActorPersistenceError(
                "Actor references an invalid character."
            )


def _actor_record(data) -> ActorRecord:
    if not isinstance(data, Mapping):
        raise ActorPersistenceError("Actor record must be an object.")

    return ActorRecord(
        _text(data.get("actor_id"), "actor_id"),
        _text(data.get("world_id"), "world_id"),
        _text(data.get("role"), "role"),
        _bool(data.get("active"), "active"),
        _optional_text(data.get("activity_id"), "activity_id"),
        _optional_text(data.get("character_id"), "character_id"),
        _optional_text(data.get("location_id"), "location_id"),
        _position(data.get("position")),
    )


def _position(data):
    if data is None:
        return None
    try:
        return Position.from_dict(data)
    except (TypeError, ValueError, KeyError) as error:
        raise ActorPersistenceError("Invalid actor position.") from error


def _activity_record(data) -> ActivityRecord:
    if not isinstance(data, Mapping):
        raise ActorPersistenceError(
            "Activity record must be an object."
        )

    state = _text(data.get("state"), "state")

    try:
        ActivityState(state)
    except ValueError as error:
        raise ActorPersistenceError(
            "Unknown activity state."
        ) from error

    start = _non_negative_int(data.get("start_tick"), "start_tick")
    end = data.get("end_tick")

    if end is not None:
        end = _non_negative_int(end, "end_tick")

        if end < start:
            raise ActorPersistenceError(
                "Activity end tick precedes start tick."
            )

    return ActivityRecord(
        _text(data.get("activity_id"), "activity_id"),
        _text(data.get("actor_id"), "actor_id"),
        _text(data.get("activity_type"), "activity_type"),
        state,
        start,
        end,
        _optional_text(data.get("target_id"), "target_id"),
        _optional_text(data.get("inventory_id"), "inventory_id"),
        _optional_text(data.get("facility_id"), "facility_id"),
        _optional_text(data.get("job_id"), "job_id"),
        _optional_text(data.get("reason"), "reason"),
        _quantity(data.get("quantity")),
    )


def _quantity(data) -> Quantity | None:
    if data is None:
        return None
    if not isinstance(data, Mapping):
        raise ActorPersistenceError("Activity quantity must be an object.")
    try:
        return Quantity(
            _non_negative_int(data.get("value"), "quantity.value"),
            ResourceUnit.from_code(data.get("unit")),
        )
    except (TypeError, ValueError) as error:
        raise ActorPersistenceError("Activity quantity is invalid.") from error


def _list(data, key):
    value = data.get(key)

    if not isinstance(value, list):
        raise ActorPersistenceError(f"{key} must be a list.")

    return value


def _unique(values, name):
    values = tuple(values)

    if len(values) != len(set(values)):
        raise ActorPersistenceError(
            f"Duplicate {name} identity."
        )


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ActorPersistenceError(
            f"{name} must be a non-empty string."
        )

    return value


def _optional_text(value, name):
    if value is None:
        return None

    return _text(value, name)


def _bool(value, name):
    if not isinstance(value, bool):
        raise ActorPersistenceError(
            f"{name} must be boolean."
        )

    return value


def _non_negative_int(value, name):
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
    ):
        raise ActorPersistenceError(
            f"{name} must be a non-negative integer."
        )

    return value


def _tick(value):
    from core.time import Tick

    return Tick(value)


__all__ = [
    "ACTOR_SCHEMA",
    "ACTOR_SCHEMA_VERSION",
    "ActorPersistenceError",
    "ActorRecord",
    "ActivityRecord",
    "ActorSnapshot",
]
