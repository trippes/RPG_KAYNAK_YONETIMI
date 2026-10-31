import json
import unittest

from core.application import GameSession
from core.entity import Entity, EntityType
from core.persistence import (
    CanonicalSessionState,
    PersistenceDocument,
    PersistenceSchemaError,
)


class TestPersistenceDocumentBridge(unittest.TestCase):
    def setUp(self):
        Entity._id_generator.reset()

    def _make_state(self):
        session = GameSession()
        first_world = session.worlds.create("A World", width=20, height=30, world_id="world_a")
        second_world = session.worlds.create("B World", width=40, height=50, world_id="world_b")
        first = Entity(EntityType.KARAKTER, "Arin", entity_id="entity_a")
        second = Entity(EntityType.NPC, "Guard", entity_id="entity_b")
        session.add_entity(first, first_world.world_id)
        session.add_entity(second, second_world.world_id)
        session.worlds.set_active(second_world.world_id)
        session.simulation.advance_to(7)
        return CanonicalSessionState.from_session(session)

    def test_state_document_dict_document_state_round_trip_preserves_fields(self):
        original = self._make_state()

        document = PersistenceDocument.from_state(original)
        document_dict = document.to_dict()
        restored_document = PersistenceDocument.from_dict(document_dict)
        restored = restored_document.to_state()

        self.assertEqual(restored.to_dict(), original.to_dict())
        self.assertEqual([world["world_id"] for world in restored.worlds], ["world_a", "world_b"])
        self.assertEqual(
            [record.entity_id.value for record in restored.entities.records],
            ["entity_a", "entity_b"],
        )
        self.assertEqual(
            [(record.entity_id.value, record.world_id.value) for record in restored.memberships.records],
            [("entity_a", "world_a"), ("entity_b", "world_b")],
        )
        self.assertEqual(restored.active_world_id.value, "world_b")
        self.assertEqual(restored.simulation_tick, 7)

    def test_document_dictionary_is_json_compatible(self):
        document = PersistenceDocument.from_state(self._make_state())

        encoded = json.dumps(document.to_dict(), sort_keys=True)

        self.assertIsInstance(encoded, str)

    def test_envelope_and_state_ticks_must_match(self):
        document_data = PersistenceDocument.from_state(self._make_state()).to_dict()
        document_data["simulation_tick"] = 8
        document = PersistenceDocument.from_dict(document_data)

        with self.assertRaisesRegex(PersistenceSchemaError, "document/state Tick mismatch"):
            document.to_state()

    def test_from_state_requires_canonical_session_state(self):
        with self.assertRaises(TypeError):
            PersistenceDocument.from_state({})

    def test_core_version_default_remains_unchanged(self):
        document = PersistenceDocument.from_state(self._make_state())

        self.assertEqual(document.core_version, "2.0")


if __name__ == "__main__":
    unittest.main()
