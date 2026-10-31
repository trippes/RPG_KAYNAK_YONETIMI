import unittest

from core.domain.spatial import Position
from core.domain import WorldDomainState
from core.foundation import EntityId, WorldId
from core.persistence import (
    CanonicalEntityRecord,
    CanonicalRestoreState,
    CanonicalSessionState,
    EntityRepositoryState,
    MembershipRecord,
    PersistenceAdapter,
    PersistenceDocument,
    PersistenceMigrationBoundary,
    RestoreContract,
    RestoreValidationError,
    RuntimeActivationBoundary,
    UnsupportedPersistenceSchemaError,
    WorldMembershipState,
    validate_canonical_state,
)
from core.time import Tick


def make_state(worlds=None, records=None, memberships=None, active="world_1", tick=4):
    return CanonicalSessionState(
        worlds=tuple(worlds or ({"world_id": "world_1", "name": "World", "width": 10, "height": 10},)),
        entities=EntityRepositoryState(tuple(records or (CanonicalEntityRecord(EntityId("entity_1"), "generic", {"durum": "aktif"}, Position(1, 2), "Guard"),))),
        memberships=WorldMembershipState(tuple(memberships or (MembershipRecord(EntityId("entity_1"), WorldId("world_1")),))),
        active_world_id=WorldId(active) if active is not None else None,
        simulation_tick=tick,
    )


class TestRestoreContract(unittest.TestCase):
    def test_prepare_returns_validated_restore_state(self):
        plan = RestoreContract.prepare(make_state())
        self.assertIsInstance(plan, CanonicalRestoreState)
        self.assertEqual(plan.simulation_tick, Tick(4))
        self.assertEqual(plan.worlds, (WorldDomainState(WorldId("world_1"), "World", 10, 10),))

    def test_duplicate_entity_id_is_rejected(self):
        record = CanonicalEntityRecord(EntityId("entity_1"), "generic", {}, Position(0, 0))
        with self.assertRaises(RestoreValidationError):
            RestoreContract.prepare(make_state(records=(record, record)))

    def test_duplicate_world_id_is_rejected(self):
        worlds = (
            {"world_id": "world_1", "name": "A", "width": 1, "height": 1},
            {"world_id": "world_1", "name": "B", "width": 1, "height": 1},
        )
        with self.assertRaises(RestoreValidationError):
            RestoreContract.prepare(make_state(worlds=worlds))

    def test_unknown_entity_and_world_references_are_rejected(self):
        membership = MembershipRecord(EntityId("missing"), WorldId("missing_world"))
        errors = validate_canonical_state(make_state(memberships=(membership,)))
        self.assertIn("unknown Entity reference", errors)
        self.assertIn("unknown World reference", errors)

    def test_multiple_world_ownership_is_rejected(self):
        memberships = (
            MembershipRecord(EntityId("entity_1"), WorldId("world_1")),
            MembershipRecord(EntityId("entity_1"), WorldId("world_2")),
        )
        errors = validate_canonical_state(make_state(
            worlds=(
                {"world_id": "world_1", "name": "A", "width": 1, "height": 1},
                {"world_id": "world_2", "name": "B", "width": 1, "height": 1},
            ),
            memberships=memberships,
        ))
        self.assertIn("multiple World ownership", errors)

    def test_duplicate_membership_and_negative_tick_are_rejected(self):
        duplicate = MembershipRecord(EntityId("entity_1"), WorldId("world_1"))
        errors = validate_canonical_state(make_state(memberships=(duplicate, duplicate)))
        self.assertIn("duplicate membership", errors)
        with self.assertRaises(ValueError):
            make_state(tick=-1)

    def test_invalid_active_world_is_rejected(self):
        with self.assertRaises(RestoreValidationError):
            RestoreContract.prepare(make_state(active="missing"))

    def test_missing_world_field_is_rejected_deterministically(self):
        errors = validate_canonical_state(make_state(worlds=({"name": "missing id"},)))
        self.assertEqual(errors, ("invalid active World ID", "missing WorldDomainState field", "unknown World reference"))

    def test_invalid_world_fields_are_rejected_before_activation(self):
        invalid_worlds = (
            {"world_id": "world_1", "name": "", "width": 10, "height": 10},
            {"world_id": "world_1", "name": "World", "width": True, "height": 10},
            {"world_id": "world_1", "name": "World", "width": 10, "height": "10"},
            {"world_id": "world_1", "name": "World", "width": 0, "height": 10},
        )
        for world in invalid_worlds:
            with self.subTest(world=world):
                errors = validate_canonical_state(make_state(worlds=(world,)))
                self.assertIn("invalid WorldDomainState", errors)
                with self.assertRaises(RestoreValidationError):
                    RestoreContract.prepare(make_state(worlds=(world,)))

    def test_unknown_world_fields_are_tolerated_and_not_carried_to_plan(self):
        world = {
            "world_id": "world_1",
            "name": "World",
            "width": 10,
            "height": 10,
            "future_field": "ignored",
        }
        plan = RestoreContract.prepare(make_state(worlds=(world,)))
        self.assertEqual(plan.worlds[0].to_dict(), {
            "world_id": "world_1",
            "name": "World",
            "width": 10,
            "height": 10,
        })

    def test_validation_precedes_activation_and_prevents_partial_mutation(self):
        calls = []
        invalid = make_state(active="missing")
        with self.assertRaises(RestoreValidationError):
            plan = RestoreContract.prepare(invalid)
            RuntimeActivationBoundary.activate(plan, lambda value: calls.append(value))
        self.assertEqual(calls, [])

    def test_activation_boundary_calls_only_with_valid_plan(self):
        plan = RestoreContract.prepare(make_state())
        activated = RuntimeActivationBoundary.activate(plan, lambda value: {"tick": value.simulation_tick.value})
        self.assertEqual(activated, {"tick": 4})

    def test_document_restore_requires_matching_tick_and_supported_schema(self):
        state = make_state()
        document = PersistenceDocument({}, Tick(4))
        self.assertEqual(RestoreContract.from_document(document, state).simulation_tick, Tick(4))
        with self.assertRaises(RestoreValidationError):
            RestoreContract.from_document(PersistenceDocument({}, Tick(5)), state)
        with self.assertRaises(UnsupportedPersistenceSchemaError):
            PersistenceMigrationBoundary.validate_version(2)

    def test_restore_is_deterministic(self):
        first = RestoreContract.prepare(make_state())
        second = RestoreContract.prepare(make_state())
        self.assertEqual(first.state.to_dict(), second.state.to_dict())

    def test_adapter_and_migration_boundaries_are_storage_agnostic(self):
        self.assertTrue(hasattr(PersistenceAdapter, "decode"))
        self.assertEqual(PersistenceMigrationBoundary.current_version, 1)

    def test_canonical_records_round_trip_without_compatibility_projection(self):
        state = make_state()
        restored = CanonicalSessionState.from_dict(state.to_dict())
        self.assertEqual(restored.to_dict(), state.to_dict())
        self.assertNotIn("world_id", state.entities.to_dict()["records"][0])
        self.assertIn("world_id", state.memberships.to_dict()["records"][0])


if __name__ == "__main__":
    unittest.main()
