"""Actor-specific movement tuning content validation tests."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from application.content_pack import (
    ContentDefinitionError,
    load_movement_configs,
)

ROOT = Path(__file__).resolve().parents[2]
DEMO_PACKAGE = ROOT / "content" / "demo_eldoria"


class MovementConfigContentTests(unittest.TestCase):
    def _package_with_rules(self, rules):
        temporary = tempfile.TemporaryDirectory()
        package = Path(temporary.name) / "package"
        shutil.copytree(DEMO_PACKAGE, package)
        (package / "gameplay_rules.json").write_text(
            json.dumps(rules),
            encoding="utf-8",
        )
        self.addCleanup(temporary.cleanup)
        return package

    def _rules(self, movement=None):
        rules = {
            "schema_version": 1,
            "player": {"inventory_id": "player", "account_id": "hero"},
            "economy": {"starting_currency": "gold", "starting_balance": 100},
            "consumables": [],
        }
        if movement is not None:
            rules["movement"] = movement
        return rules

    def test_absent_movement_profiles_do_not_invent_speeds(self):
        package = self._package_with_rules(self._rules())
        self.assertEqual(dict(load_movement_configs(package_path=package)), {})

    def test_profiles_are_keyed_by_stable_actor_id(self):
        package = self._package_with_rules(self._rules({
            "actors": {
                "hero": {"max_speed": 83.5},
                "town_guard_01": {
                    "max_speed": 42,
                    "running_speed_multiplier": 1.8,
                    "stealth_speed_multiplier": 0.4,
                },
            },
        }))
        configs = load_movement_configs(package_path=package)
        self.assertEqual(configs["hero"].max_speed, 83.5)
        self.assertEqual(configs["town_guard_01"].max_speed, 42.0)
        self.assertEqual(configs["town_guard_01"].running_speed_multiplier, 1.8)
        self.assertEqual(configs["town_guard_01"].stealth_speed_multiplier, 0.4)
        with self.assertRaises(TypeError):
            configs["new_actor"] = configs["hero"]

    def test_optional_profile_fields_use_movement_config_defaults(self):
        package = self._package_with_rules(self._rules({
            "actors": {"hero": {"max_speed": 83.5}},
        }))
        config = load_movement_configs(package_path=package)["hero"]

        self.assertEqual(config.running_speed_multiplier, 1.5)
        self.assertEqual(config.stealth_speed_multiplier, 0.5)
        self.assertEqual(config.acceleration, 180.0)
        self.assertEqual(config.deceleration, 240.0)
        self.assertEqual(config.braking_deceleration, 360.0)

    def test_invalid_or_missing_speed_is_rejected(self):
        for profile in ({}, {"max_speed": 0}, {"max_speed": -1}, {"max_speed": True}):
            with self.subTest(profile=profile):
                package = self._package_with_rules(self._rules({
                    "actors": {"hero": profile},
                }))
                with self.assertRaises(ContentDefinitionError):
                    load_movement_configs(package_path=package)

    def test_unknown_profile_fields_are_rejected(self):
        package = self._package_with_rules(self._rules({
            "actors": {"hero": {"max_speed": 10, "speed": 20}},
        }))
        with self.assertRaises(ContentDefinitionError):
            load_movement_configs(package_path=package)


if __name__ == "__main__":
    unittest.main()
