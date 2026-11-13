import unittest
from pathlib import Path
from application.content_loader import load_content_package

ROOT=Path(__file__).resolve().parents[2]

class TestMixedMapPackage(unittest.TestCase):
 def test_existing_nine_square_maps_and_new_hex_map_coexist(self):
  p=load_content_package(ROOT/"content"/"demo_eldoria")
  expected={"village","forest","north_mine","east_forest","east_mine","south_forest","south_mine","west_forest","west_mine"}
  self.assertEqual(set(p.map_definitions),expected)
  self.assertEqual(set(p.hex_map_definitions), {
        "hex_forest_demo", "hex_clearing_demo", "hex_northeast_demo",
        "hex_northwest_demo", "hex_west_demo", "hex_southwest_demo",
        "hex_southeast_demo",
    })
  self.assertEqual(p.schema_version,1)
 def test_hex_fixture_does_not_become_starting_map(self):
  p=load_content_package(ROOT/"content"/"demo_eldoria")
  self.assertNotIn("hex_forest_demo",p.map_definitions)
  self.assertNotIn("hex_clearing_demo",p.map_definitions)
  self.assertEqual(sum(m.starting_position is not None for m in p.map_definitions.values()),1)

if __name__=="__main__": unittest.main()
