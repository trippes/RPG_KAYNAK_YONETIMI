import unittest

from core.application import GameSession
from core.entity import Entity, EntityType
from core.foundation import EntityId, WorldId
from core.persistence import (
    CanonicalEntityRecord,
    CanonicalSessionState,
    EntityRepositoryState,
    MembershipRecord,
    RestoreContract,
    RestoreValidationError,
    RuntimeActivationBoundary,
    WorldMembershipState,
)
from core.domain.spatial import Position


def snapshot(session):
    return CanonicalSessionState.from_session(session).to_dict()


def make_valid_plan():
    session = GameSession()
    first = session.worlds.create("First", world_id="world_a")
    second = session.worlds.create("Second", world_id="world_b")
    session.worlds.set_active(second.world_id)
    session.add_entity(Entity(EntityType.NPC, "Guard", entity_id="entity_a"), first.world_id)
    session.add_entity(Entity(EntityType.KARAKTER, "Hero", entity_id="entity_b"), second.world_id)
    session.simulation.advance_to(11)
    return RestoreContract.prepare(CanonicalSessionState.from_session(session))


class TestRestoreActivation(unittest.TestCase):
    def test_empty_session_is_constructible(self):
        session = GameSession()
        self.assertEqual(session.worlds.count(), 0)
        self.assertEqual(session.entities.count(), 0)
        self.assertEqual(session.simulation.current_tick.value, 0)

    def test_runtime_activation_is_deterministic_and_complete(self):
        target = GameSession()
        target.activate_restore(make_valid_plan())

        self.assertEqual([world.world_id for world in target.worlds.get_all()], ["world_a", "world_b"])
        self.assertEqual(target.membership.world_id_for("entity_a"), "world_a")
        self.assertEqual(target.membership.world_id_for("entity_b"), "world_b")
        self.assertEqual(target.worlds.get_active_id(), "world_b")
        self.assertEqual(target.simulation.current_tick.value, 11)

    def test_invalid_restore_leaves_existing_runtime_unchanged(self):
        target = GameSession()
        world = target.worlds.create("Existing", world_id="existing")
        target.worlds.set_active(world.world_id)
        target.add_entity(Entity(EntityType.NPC, "Existing", entity_id="existing_entity"), world.world_id)
        target.simulation.advance_to(100)
        before = snapshot(target)

        invalid = make_valid_plan().state
        invalid = CanonicalSessionState(
            worlds=invalid.worlds,
            entities=invalid.entities,
            memberships=WorldMembershipState((MembershipRecord(EntityId("missing"), WorldId("world_a")),)),
            active_world_id=invalid.active_world_id,
            simulation_tick=invalid.simulation_tick,
        )
        with self.assertRaises(RestoreValidationError):
            target.activate_restore(RestoreContract.prepare(invalid))
        self.assertEqual(snapshot(target), before)

    def test_invalid_activation_entity_state_leaves_existing_runtime_unchanged(self):
        target = GameSession()
        world = target.worlds.create("Existing", world_id="existing")
        target.worlds.set_active(world.world_id)
        target.add_entity(Entity(EntityType.NPC, "Existing", entity_id="existing_entity"), world.world_id)
        before = snapshot(target)

        state = make_valid_plan().state
        records = list(state.entities.records)
        records[0] = CanonicalEntityRecord(
            records[0].entity_id,
            records[0].entity_type,
            {"durum": "invalid", "canli": True},
            records[0].position,
            records[0].name,
        )
        invalid_plan = RestoreContract.prepare(CanonicalSessionState(
            worlds=state.worlds,
            entities=EntityRepositoryState(tuple(records)),
            memberships=state.memberships,
            active_world_id=state.active_world_id,
            simulation_tick=state.simulation_tick,
        ))
        with self.assertRaises(ValueError):
            target.activate_restore(invalid_plan)
        self.assertEqual(snapshot(target), before)

    def test_runtime_activation_boundary_revalidates_plan(self):
        plan = make_valid_plan()
        calls = []
        result = RuntimeActivationBoundary.activate(plan, lambda validated: calls.append(validated) or "activated")
        self.assertEqual(result, "activated")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].simulation_tick.value, 11)


if __name__ == "__main__":
    unittest.main()
