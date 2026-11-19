"""Validation and construction of NPC physics content records."""

import json
import tempfile
import unittest
from pathlib import Path

from application.content_pack import ContentDefinitionError, _build_npc_physics_body, load_npc_definitions
from core.domain.physics import CircleShape, PhysicsBodyDefinition


class TestNPCPhysicsContent(unittest.TestCase):
    def _load(self, physics):
        payload = {"schema_version": 1, "npcs": [{
            "id": "content_guard", "name": "Content Guard", "role": "guard",
            "load_phase": "opening", "physics": physics,
        }]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "npcs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return load_npc_definitions(path)

    def test_content_physics_builds_npc_owned_circle_body(self):
        record = self._load({"shape": "circle", "radius": 4.0})[0]
        body = _build_npc_physics_body(record)
        self.assertIsInstance(body, PhysicsBodyDefinition)
        self.assertIsInstance(body.collider, CircleShape)
        self.assertEqual(body.body_id, "content_guard")
        self.assertEqual(body.collider.radius, 4.0)

    def test_content_can_define_an_individual_radius(self):
        record = self._load({"shape": "circle", "radius": 6.25})[0]
        self.assertEqual(_build_npc_physics_body(record).collider.radius, 6.25)

    def test_content_rejects_unsupported_shape(self):
        with self.assertRaisesRegex(ContentDefinitionError, "shape must be 'circle'"):
            self._load({"shape": "polygon", "radius": 4.0})

    def test_content_rejects_invalid_radius(self):
        for radius in (0, -1, float("inf"), float("nan"), True):
            with self.subTest(radius=radius):
                with self.assertRaisesRegex(ContentDefinitionError, "radius must be finite and positive"):
                    self._load({"shape": "circle", "radius": radius})

    def test_legacy_record_without_physics_uses_domain_default(self):
        payload = {"schema_version": 1, "npcs": [{
            "id": "legacy_guard", "name": "Legacy Guard", "role": "guard",
            "load_phase": "opening",
        }]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "npcs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            record = load_npc_definitions(path)[0]
        self.assertIsNone(_build_npc_physics_body(record))


if __name__ == "__main__":
    unittest.main()
