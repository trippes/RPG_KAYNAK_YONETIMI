"""Canonical restore validation and adapter boundaries.

This module constructs validation plans only. It does not read storage, write
storage, create save slots, or mutate an active runtime.
"""

from dataclasses import dataclass
from typing import Callable, Mapping, Protocol

from core.foundation import EntityId, WorldId
from core.time import Tick
from core.domain import WorldDomainState

from .contracts import (
    PERSISTENCE_SCHEMA_VERSION,
    PersistenceDocument,
    PersistenceSchemaError,
    UnsupportedPersistenceSchemaError,
)
from .state import CanonicalSessionState, EntityRepositoryState, WorldMembershipState


class RestoreValidationError(PersistenceSchemaError):
    """Deterministic collection of canonical restore invariant failures."""

    def __init__(self, errors: tuple[str, ...]):
        self.errors = tuple(sorted(errors))
        super().__init__("; ".join(self.errors))


@dataclass(frozen=True)
class CanonicalRestoreState:
    """Validated, immutable restore input separated from runtime objects."""

    state: CanonicalSessionState
    canonical_worlds: tuple[WorldDomainState, ...]

    @property
    def worlds(self):
        return self.canonical_worlds

    @property
    def entities(self) -> EntityRepositoryState:
        return self.state.entities

    @property
    def memberships(self) -> WorldMembershipState:
        return self.state.memberships

    @property
    def active_world_id(self):
        return self.state.active_world_id

    @property
    def simulation_tick(self) -> Tick:
        return Tick(self.state.simulation_tick)


RestorePlan = CanonicalRestoreState


def validate_canonical_state(state: CanonicalSessionState) -> tuple[str, ...]:
    """Return all deterministic invariant failures without mutating runtime."""
    errors: list[str] = []
    if not isinstance(state, CanonicalSessionState):
        return ("state must be CanonicalSessionState",)

    world_ids = []
    for world in state.worlds:
        if not isinstance(world, Mapping):
            errors.append("missing WorldDomainState field")
            continue
        required = {"world_id", "name", "width", "height"}
        if not required.issubset(world):
            errors.append("missing WorldDomainState field")
            continue
        try:
            canonical_world = WorldDomainState.from_persistence(world)
        except (TypeError, ValueError):
            errors.append("invalid WorldDomainState")
            continue
        world_ids.append(canonical_world.world_id.value)
    entity_ids = [record.entity_id.value for record in state.entities.records]
    membership_pairs = [(record.entity_id.value, record.world_id.value) for record in state.memberships.records]

    if len(world_ids) != len(set(world_ids)):
        errors.append("duplicate WorldId")
    if len(entity_ids) != len(set(entity_ids)):
        errors.append("duplicate EntityId")
    if any(not value.strip() for value in world_ids):
        errors.append("invalid WorldId")
    if any(not value.strip() for value in entity_ids):
        errors.append("invalid EntityId")
    if len(membership_pairs) != len(set(membership_pairs)):
        errors.append("duplicate membership")

    known_worlds = set(world_ids)
    known_entities = set(entity_ids)
    if any(entity_id not in known_entities for entity_id, _ in membership_pairs):
        errors.append("unknown Entity reference")
    if any(world_id not in known_worlds for _, world_id in membership_pairs):
        errors.append("unknown World reference")
    membership_by_entity: dict[str, set[str]] = {}
    for entity_id, world_id in membership_pairs:
        membership_by_entity.setdefault(entity_id, set()).add(world_id)
    if any(len(worlds) > 1 for worlds in membership_by_entity.values()):
        errors.append("multiple World ownership")
    if state.active_world_id is not None and not isinstance(state.active_world_id, WorldId):
        errors.append("invalid active World ID")
    elif state.active_world_id is not None and state.active_world_id.value not in known_worlds:
        errors.append("invalid active World ID")
    if isinstance(state.simulation_tick, bool) or not isinstance(state.simulation_tick, int) or state.simulation_tick < 0:
        errors.append("negative or invalid Tick")

    return tuple(sorted(set(errors)))


class RestoreContract:
    """Validate canonical state and produce a plan without runtime mutation."""

    @staticmethod
    def validate(state: CanonicalSessionState) -> tuple[str, ...]:
        return validate_canonical_state(state)

    @staticmethod
    def prepare(state: CanonicalSessionState) -> CanonicalRestoreState:
        errors = validate_canonical_state(state)
        if errors:
            raise RestoreValidationError(errors)
        canonical_worlds = tuple(
            WorldDomainState.from_persistence(world)
            for world in state.worlds
        )
        return CanonicalRestoreState(state, canonical_worlds)

    @staticmethod
    def from_document(document: PersistenceDocument, state: CanonicalSessionState) -> CanonicalRestoreState:
        if not isinstance(document, PersistenceDocument):
            raise TypeError("document must be PersistenceDocument.")
        PersistenceMigrationBoundary.migrate(document)
        plan = RestoreContract.prepare(state)
        if document.simulation_tick.value != plan.simulation_tick.value:
            raise RestoreValidationError(("document/state Tick mismatch",))
        return plan


class RuntimeActivationBoundary:
    """Technology-neutral activation hook, called only after preparation."""

    @staticmethod
    def activate(plan: CanonicalRestoreState, activator: Callable[[CanonicalRestoreState], object]):
        if not isinstance(plan, CanonicalRestoreState):
            raise TypeError("plan must be CanonicalRestoreState.")
        if not callable(activator):
            raise TypeError("activator must be callable.")
        validated_plan = RestoreContract.prepare(plan.state)
        return activator(validated_plan)


class PersistenceAdapter(Protocol):
    """External representation → canonical state boundary."""

    def decode(self, external_representation: object) -> CanonicalSessionState:
        ...


class PersistenceMigrationBoundary:
    """Version gate; actual v1→v2 transformations are intentionally deferred."""

    current_version = PERSISTENCE_SCHEMA_VERSION

    @classmethod
    def validate_version(cls, stored_version: object) -> None:
        if isinstance(stored_version, bool) or not isinstance(stored_version, int):
            raise PersistenceSchemaError("Persistence schema version must be an integer.")
        if stored_version != cls.current_version:
            raise UnsupportedPersistenceSchemaError(
                f"Persistence schema version {stored_version} requires a migration boundary."
            )

    @classmethod
    def migrate(cls, document: PersistenceDocument) -> PersistenceDocument:
        if not isinstance(document, PersistenceDocument):
            raise TypeError("document must be PersistenceDocument.")
        cls.validate_version(document.schema_version)
        return document
