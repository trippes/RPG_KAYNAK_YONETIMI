import unittest
from resources import ResourceDefinition, ResourceUnit


class TestResourceDefinition(unittest.TestCase):
    def test_valid_definition_normalizes_tags(self):
        value = ResourceDefinition("iron_ore", "Demir Cevheri", ResourceUnit.KG, 1, 0.25, "ore", ("metal", "raw"))
        self.assertEqual(value.tags, ("metal", "raw"))

    def test_invalid_identity_and_unit_are_rejected(self):
        with self.assertRaises(ValueError):
            ResourceDefinition("", "Odun", ResourceUnit.ITEM)
        with self.assertRaises(TypeError):
            ResourceDefinition("wood", "Odun", "item")

    def test_negative_and_non_finite_physical_values_are_rejected(self):
        for value in (-1, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ResourceDefinition("wood", "Odun", ResourceUnit.ITEM, weight_kg_per_unit=value)

    def test_duplicate_tags_are_rejected(self):
        with self.assertRaises(ValueError):
            ResourceDefinition("wood", "Odun", ResourceUnit.ITEM, tags=("raw", "raw"))


if __name__ == "__main__":
    unittest.main()
