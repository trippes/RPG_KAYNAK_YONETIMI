import unittest

from core.application import GameSession
from core.domain.spatial import Position
from core.domain import WorldDomainState
from core.entity import Entity, EntityType
from core.foundation import ActionId, EntityId, EventId, WorldId
from core.persistence import (
    CANONICAL_PERSISTENCE_SCHEMA,
    PERSISTENCE_EXCLUSIONS,
    PERSISTENCE_SCHEMA_VERSION,
    CanonicalEntityRecord,
    CanonicalSessionState,
    EntityRepositoryState,
    PersistenceDocument,
    PersistenceSchemaError,
    WorldMembershipState,
    deserialize_identifier,
    deserialize_position,
    deserialize_tick,
    serialize_identifier,
    serialize_position,
    serialize_tick,
)
from core.simulation import SimulationEvent
from core.time import Tick
from core.world import World


class TestPersistenceContracts(unittest.TestCase):
    def setUp(self):
        Entity._id_generator.reset()
        World._id_generator.reset()

    def test_identifier_round_trips_are_type_safe(self):
        for identifier_type in (EntityId, WorldId, ActionId, EventId):
            original = identifier_type("stable_001")
            self.assertEqual(deserialize_identifier(serialize_identifier(original), identifier_type), original)
            self.assertEqual(original.to_persistence(), "stable_001")

    def test_position_and_tick_round_trip(self):
        position = Position(1.5, -2)
        self.assertEqual(deserialize_position(serialize_position(position)), position)
        tick = Tick(42)
        self.assertEqual(deserialize_tick(serialize_tick(tick)), tick)
        self.assertEqual(hash(position), hash(Position(1.5, -2)))

    def test_persistence_document_version_is_not_event_version(self):
        document = PersistenceDocument({"x": 1}, Tick(3))
        event = SimulationEvent("example", Tick(3), None, None, None, {}, {})
        self.assertEqual(document.schema_version, PERSISTENCE_SCHEMA_VERSION)
        self.assertEqual(event.schema_version, 1)
        self.assertNotEqual(document.__class__.__name__, event.__class__.__name__)
        self.assertEqual(PersistenceDocument.from_dict(document.to_dict()).to_dict(), document.to_dict())

    def test_document_tolerates_future_fields_but_rejects_missing_fields(self):
        data = {
            "schema": CANONICAL_PERSISTENCE_SCHEMA,
            "schema_version": 1,
            "core_version": "2.0",
            "simulation_tick": 0,
            "state": {},
            "future_field": {"ignored": True},
        }
        self.assertEqual(PersistenceDocument.from_dict(data).simulation_tick, Tick(0))
        with self.assertRaises(PersistenceSchemaError):
            PersistenceDocument.from_dict({"schema": CANONICAL_PERSISTENCE_SCHEMA})

    def test_world_domain_state_round_trip_excludes_runtime(self):
        original = WorldDomainState(WorldId("world_1"), "World", 10, 20)
        restored = WorldDomainState.from_persistence(original.to_persistence())
        self.assertEqual(restored, original)
        self.assertFalse(hasattr(restored, "scheduler"))
        self.assertFalse(hasattr(restored, "event_transport"))

    def test_entity_repository_state_is_record_based_and_deterministic(self):
        session = GameSession()
        first = Entity(EntityType.KARAKTER, "first", entity_id="entity_b")
        second = Entity(EntityType.NPC, "second", entity_id="entity_a")
        session.entities.add(first)
        session.entities.add(second)
        state = EntityRepositoryState.from_repository(session.entities)
        self.assertEqual([record.entity_id.value for record in state.records], ["entity_a", "entity_b"])
        self.assertNotIn("world_id", state.to_dict()["records"][0])
        self.assertNotIn("_entities", state.to_dict())

    def test_membership_state_is_canonical_mapping(self):
        session = GameSession()
        world = session.worlds.create("world", world_id="world_2")
        entity = Entity(EntityType.KARAKTER, "guard")
        session.add_entity(entity, world.world_id)
        state = WorldMembershipState.from_service(session.membership)
        self.assertEqual(state.records[0].entity_id.value, entity.entity_id)
        self.assertEqual(state.records[0].world_id.value, "world_2")
        self.assertIn("world_id", state.to_dict()["records"][0])
        self.assertNotIn("Entity.world_id", state.to_dict())

    def test_canonical_session_state_excludes_runtime_objects(self):
        session = GameSession()
        session.worlds.create("world", world_id="world_1")
        state = CanonicalSessionState.from_session(session)
        data = state.to_dict()
        self.assertIn("worlds", data)
        self.assertIn("entities", data)
        self.assertIn("memberships", data)
        self.assertNotIn("dispatcher", data)
        self.assertNotIn("event_transport", data)
        self.assertNotIn("scheduler", data)

    def test_session_world_records_are_immutable(self):
        session = GameSession()
        session.worlds.create("world", world_id="world_1")
        state = CanonicalSessionState.from_session(session)
        with self.assertRaises(TypeError):
            state.worlds[0]["name"] = "changed"

    def test_exclusion_contract_is_explicit(self):
        self.assertIn("Entity.world_id", PERSISTENCE_EXCLUSIONS)
        self.assertIn("World._entities", PERSISTENCE_EXCLUSIONS)
        self.assertIn("GameClock", PERSISTENCE_EXCLUSIONS)
        self.assertIn("ActionManager", PERSISTENCE_EXCLUSIONS)

    def test_entity_record_defensively_copies_state(self):
        source = {"status": "active"}
        record = CanonicalEntityRecord(EntityId("e"), "generic", source, Position(0, 0))
        source["status"] = "changed"
        self.assertEqual(record.state["status"], "active")
        with self.assertRaises(TypeError):
            record.state["new"] = "value"


if __name__ == "__main__":
    unittest.main()
