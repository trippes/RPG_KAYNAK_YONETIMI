import json
import shutil
import tempfile
import unittest
from pathlib import Path
from application.content_pack import ContentDefinitionError, load_production_definitions, load_structure_part_catalog

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "content" / "demo_eldoria"

class TestCraftingContent(unittest.TestCase):
    def test_demo_package_registers_intermediates_and_part_outputs(self):
        _facilities, recipes = load_production_definitions(package_path=PACKAGE)
        by_id = {recipe.recipe_id: recipe for recipe in recipes}
        self.assertEqual(by_id["wooden_plank"].item_outputs, (("wooden_plank", 1),))
        self.assertEqual(by_id["wooden_floor_panel"].structure_part_bindings, (("wooden_floor_panel", "wooden_floor_panel"),))
        catalog = load_structure_part_catalog(package_path=PACKAGE)
        self.assertIsNotNone(catalog.part("wooden_floor_panel"))
        self.assertIsNotNone(catalog.part("wooden_door"))

    def test_package_rejects_unknown_crafted_item(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "package"
            shutil.copytree(PACKAGE, target)
            path = target / "starter_content.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["production"]["recipes"][0]["item_outputs"][0]["item_id"] = "missing_item"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ContentDefinitionError, "unknown item"):
                load_production_definitions(package_path=target)

    def test_package_rejects_unknown_structure_part_binding(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "package"
            shutil.copytree(PACKAGE, target)
            path = target / "starter_content.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["production"]["recipes"][3]["structure_part_bindings"][0]["part_definition_id"] = "missing_part"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ContentDefinitionError, "unknown structure part"):
                load_production_definitions(package_path=target)

if __name__ == "__main__":
    unittest.main()
