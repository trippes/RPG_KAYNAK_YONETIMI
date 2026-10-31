import unittest

from core.application import GameSession
from core.domain import WorldDomainState
from core.domain.spatial import Position
from core.entity import Entity, EntityType
from core.foundation import EntityId, WorldId
from core.persistence import (
    CanonicalEntityRecord,
    CanonicalSessionState,
    EntityRepositoryState,
    MembershipRecord,
    WorldMembershipState,
)


class TestSessionStateRecords(unittest.TestCase):
    def test_world_records_are_canonicalized_from_raw_mapping(self):
        source = {
            "worlds": [{
                "world_id": "world_b",
                "name": "B",
                "width": 20,
                "height": 20,
                "future_field": "ignored",
            }, {
                "world_id": "world_a",
                "name": "A",
                "width": 10,
                "height": 10,
                "future_field": "ignored",
            }],
            "entities": {"records": []},
            "memberships": {"records": []},
            "active_world_id": "world_b",
            "simulation_tick": 3,
        }
        state = CanonicalSessionState.from_dict(source)

        self.assertEqual(state.worlds[0]["world_id"], "world_a")
        self.assertNotIn("future_field", state.worlds[0])
        self.assertEqual(
            CanonicalSessionState.from_dict(state.to_dict()).to_dict(),
            state.to_dict(),
        )

    def test_direct_valid_world_records_are_identity_sorted(self):
        state = CanonicalSessionState(
            worlds=(
                {"world_id": "world_b", "name": "B", "width": 2, "height": 2},
                {"world_id": "world_a", "name": "A", "width": 1, "height": 1},
            ),
            entities=EntityRepositoryState(()),
            memberships=WorldMembershipState(()),
            active_world_id=None,
            simulation_tick=0,
        )
        self.assertEqual([world["world_id"] for world in state.worlds], ["world_a", "world_b"])

    def test_entity_record_round_trip_excludes_membership(self):
        record = CanonicalEntityRecord(
            EntityId("entity_a"),
            EntityType.NPC,
            {"durum": "aktif", "canli": True},
            Position(2, 4),
            "Guard",
        )
        restored = CanonicalEntityRecord.from_dict({
            **record.to_dict(),
            "world_id": "legacy_world",
            "future_field": "ignored",
        })

        self.assertEqual(restored, record)
        self.assertNotIn("world_id", restored.to_dict())

    def test_membership_record_round_trip_is_typed_and_deterministic(self):
        record = MembershipRecord(EntityId("entity_a"), WorldId("world_a"))
        restored = MembershipRecord.from_dict({
            **record.to_dict(),
            "future_field": "ignored",
        })

        self.assertEqual(restored, record)
        self.assertEqual(restored.to_dict(), {
            "entity_id": "entity_a",
            "world_id": "world_a",
        })

    def test_entity_and_membership_records_are_identity_sorted(self):
        entities = EntityRepositoryState((
            CanonicalEntityRecord(EntityId("entity_b"), "npc", {}, Position(0, 0)),
            CanonicalEntityRecord(EntityId("entity_a"), "npc", {}, Position(0, 0)),
        ))
        memberships = WorldMembershipState((
            MembershipRecord(EntityId("entity_b"), WorldId("world_b")),
            MembershipRecord(EntityId("entity_a"), WorldId("world_z")),
            MembershipRecord(EntityId("entity_a"), WorldId("world_a")),
        ))

        self.assertEqual([item.entity_id.value for item in entities.records], ["entity_a", "entity_b"])
        self.assertEqual(
            [(item.entity_id.value, item.world_id.value) for item in memberships.records],
            [("entity_a", "world_a"), ("entity_a", "world_z"), ("entity_b", "world_b")],
        )

    def test_session_records_do_not_depend_on_legacy_projections(self):
        session = GameSession()
        world = session.worlds.create("World", world_id="world_a")
        entity = Entity(EntityType.NPC, "Guard", entity_id="entity_a")
        session.add_entity(entity, world.world_id)
        before = CanonicalSessionState.from_session(session).to_dict()

        world._entities.clear()
        entity.remove_from_world()

        after = CanonicalSessionState.from_session(session).to_dict()
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
