import unittest
from pathlib import Path

from application.content_loader import load_content_package

ROOT = Path(__file__).resolve().parents[2]


class TestLegacySquareMapPackage(unittest.TestCase):
    def test_demo_package_contains_only_the_nine_legacy_square_maps(self):
        package = load_content_package(ROOT / "content" / "demo_eldoria")
        expected = {
            "village", "forest", "north_mine", "east_forest", "east_mine",
            "south_forest", "south_mine", "west_forest", "west_mine",
        }
        self.assertEqual(set(package.map_definitions), expected)
        self.assertEqual(package.hex_map_definitions, {})
        self.assertIsNone(package.world_map_definition)
        self.assertEqual(package.schema_version, 1)

    def test_legacy_square_package_has_one_starting_map(self):
        package = load_content_package(ROOT / "content" / "demo_eldoria")
        self.assertEqual(
            sum(item.starting_position is not None for item in package.map_definitions.values()),
            1,
        )


if __name__ == "__main__":
    unittest.main()
