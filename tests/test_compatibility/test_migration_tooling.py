import warnings
import unittest
from pathlib import Path

from core.compatibility import (
    LEGACY_API_MATRIX,
    canonical_for,
    get_all_mappings,
    get_mapping,
    is_legacy,
    reset_runtime_usage,
    runtime_usage_counts,
    scan_static_usage,
    usage_report,
)
from core.event_bus import EventBus
from core.events import EventQueue
from core.game import Game


class TestMigrationTooling(unittest.TestCase):
    def setUp(self):
        reset_runtime_usage()

    def test_metadata_is_complete_and_immutable(self):
        entry = get_mapping("core.event_bus.EventBus")
        self.assertEqual(entry.legacy_name, "core.event_bus.EventBus")
        self.assertEqual(entry.canonical_replacement, "CanonicalEventDispatcher")
        self.assertIsInstance(entry.migration_notes, str)
        with self.assertRaises(TypeError):
            LEGACY_API_MATRIX["new"] = entry
        with self.assertRaises(Exception):
            entry.status = "removed"

    def test_registry_lookup_and_deterministic_order(self):
        mappings = get_all_mappings()
        names = [item.legacy_name for item in mappings]
        self.assertEqual(names, sorted(names))
        self.assertTrue(is_legacy("core.events.EventQueue"))
        self.assertEqual(canonical_for("core.events.EventQueue"), "CanonicalEventTransport")

    def test_deprecation_warning_is_controlled_and_actionable(self):
        game = Game()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            with self.assertRaises(RuntimeError):
                game.dunya_olaylarini_aktar()
        self.assertEqual(len(caught), 1)
        self.assertIn("Game.dunya_olaylarini_canonical_aktar", str(caught[0].message))
        self.assertEqual(runtime_usage_counts()["Game.dunya_olaylarini_aktar"], 1)

    def test_runtime_usage_counter_tracks_legacy_construction(self):
        EventQueue()
        EventBus()
        counts = runtime_usage_counts()
        self.assertEqual(counts["core.events.EventQueue"], 1)
        self.assertEqual(counts["core.event_bus.EventBus"], 1)

    def test_static_scanner_is_ast_based_and_ignores_non_source_areas(self):
        root = Path(__file__).parents[2]
        usages = scan_static_usage(root)
        self.assertTrue(any(item.legacy_name == "core.events.EventQueue" for item in usages))
        self.assertTrue(all(not item.path.startswith("tests") for item in usages))
        self.assertTrue(all(not item.path.startswith("docs") for item in usages))
        self.assertTrue(all("__pycache__" not in item.path for item in usages))

    def test_usage_report_contains_static_and_runtime_columns(self):
        EventQueue()
        report = usage_report(Path(__file__).parents[2])
        row = next(item for item in report if item.legacy_name == "core.events.EventQueue")
        self.assertGreaterEqual(row.static_usage_count, 1)
        self.assertEqual(row.runtime_usage_count, 1)
        self.assertTrue(hasattr(row, "canonical_replacement"))

    def test_migration_matrix_is_complete(self):
        required = {
            "core.event_bus.EventBus", "core.events.EventQueue", "core.event_types.EventType",
            "core.constants event constants", "Game.dunya_olaylarini_aktar", "core.clock.GameClock",
            "time_system.Scheduler", "core.actions.Action", "core.actions.ActionManager",
            "Entity.world_id", "World._entities", "core.entity.position.Position", "time_system.Tick",
        }
        self.assertTrue(required.issubset(LEGACY_API_MATRIX))


if __name__ == "__main__":
    unittest.main()
