import unittest
from pathlib import Path

from application.content_loader import load_content_package

ROOT = Path(__file__).resolve().parents[2]


class TestLegacyMapRemoval(unittest.TestCase):
    def test_demo_package_has_no_legacy_square_or_hex_demo_maps(self):
        package = load_content_package(ROOT / "content" / "demo_eldoria")
        self.assertEqual(tuple(package.hex_map_definitions), ("starting_valley",))
        self.assertIsNone(package.world_map_definition)


if __name__ == "__main__":
    unittest.main()
