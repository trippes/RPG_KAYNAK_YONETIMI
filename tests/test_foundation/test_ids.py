import unittest

from core.foundation import EntityId, EventId, Identifier, WorldId


class TestIdentifiers(unittest.TestCase):
    def test_identifier_is_immutable_hashable_and_serializable(self):
        identifier = Identifier("value-1")
        self.assertEqual(identifier.value, "value-1")
        self.assertEqual(identifier.to_dict(), {"value": "value-1"})
        self.assertEqual(hash(identifier), hash(Identifier("value-1")))
        with self.assertRaises(AttributeError):
            identifier.value = "other"

    def test_specialized_identifiers(self):
        self.assertEqual(str(EntityId("entity_1")), "entity_1")
        self.assertEqual(str(WorldId("world_1")), "world_1")
        self.assertEqual(str(EventId("event_1")), "event_1")

    def test_identifier_rejects_invalid_values(self):
        for value in (None, 1, "", "   "):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    Identifier(value)
