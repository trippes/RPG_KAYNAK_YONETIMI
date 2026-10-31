import unittest

from resources import Quantity, ResourceType, ResourceUnit


class TestResourceType(unittest.TestCase):
    def test_valid_and_unicode_identifiers_are_preserved(self):
        self.assertEqual(ResourceType("wood"), ResourceType("wood"))
        self.assertEqual(ResourceType("demir_çelik").value, "demir_çelik")

    def test_empty_and_whitespace_identifiers_are_rejected(self):
        for value in ("", "   ", "\t\n"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ResourceType(value)

    def test_different_identifiers_are_not_equal(self):
        self.assertNotEqual(ResourceType("wood"), ResourceType("stone"))

    def test_identifier_is_immutable(self):
        resource_type = ResourceType("wood")
        with self.assertRaises((AttributeError, TypeError)):
            resource_type.value = "stone"


class TestResourceUnit(unittest.TestCase):
    def test_supported_units_have_stable_codes(self):
        self.assertEqual(str(ResourceUnit.ITEM), "item")
        self.assertEqual(str(ResourceUnit.KG), "kg")
        self.assertEqual(str(ResourceUnit.LITER), "liter")
        self.assertIs(ResourceUnit.from_code("kg"), ResourceUnit.KG)

    def test_empty_and_unsupported_units_are_rejected(self):
        for code in ("", "   ", "gallon"):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    ResourceUnit.from_code(code)

    def test_non_string_unit_code_is_rejected(self):
        with self.assertRaises(TypeError):
            ResourceUnit.from_code(1)


class TestQuantity(unittest.TestCase):
    def test_zero_and_positive_integer_quantities_are_valid(self):
        self.assertEqual(Quantity(0, ResourceUnit.ITEM).value, 0)
        self.assertEqual(Quantity(12, ResourceUnit.KG), Quantity(12, ResourceUnit.KG))

    def test_negative_and_boolean_quantities_are_rejected(self):
        with self.assertRaises(ValueError):
            Quantity(-1, ResourceUnit.ITEM)
        with self.assertRaises(TypeError):
            Quantity(True, ResourceUnit.ITEM)

    def test_non_integer_quantities_are_rejected(self):
        for value in (1.0, "1", None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    Quantity(value, ResourceUnit.ITEM)

    def test_different_units_are_not_equal_for_same_numeric_value(self):
        self.assertNotEqual(Quantity(1, ResourceUnit.KG), Quantity(1, ResourceUnit.LITER))
        self.assertNotEqual(Quantity(1, ResourceUnit.ITEM), Quantity(1, ResourceUnit.KG))

    def test_unit_is_required_and_value_objects_are_immutable(self):
        with self.assertRaises(TypeError):
            Quantity(1, "kg")

        quantity = Quantity(1, ResourceUnit.ITEM)
        with self.assertRaises((AttributeError, TypeError)):
            quantity.value = 2
        with self.assertRaises((AttributeError, TypeError)):
            quantity.unit = ResourceUnit.KG


if __name__ == "__main__":
    unittest.main()
