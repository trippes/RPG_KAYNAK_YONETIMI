import unittest

from core.time import Tick


class TestCanonicalTick(unittest.TestCase):
    def test_creation_comparison_and_hashing(self):
        self.assertLess(Tick(1), Tick(2))
        self.assertEqual(Tick(5), Tick(5))
        self.assertEqual(hash(Tick(5)), hash(Tick(5)))

    def test_arithmetic(self):
        self.assertEqual(Tick(5) + Tick(2), Tick(7))
        self.assertEqual(Tick(5) + 2, Tick(7))
        self.assertEqual(2 + Tick(5), Tick(7))
        self.assertEqual(Tick(5) - 2, Tick(3))
        self.assertEqual(Tick(2) * 3, Tick(6))
        self.assertEqual(3 * Tick(2), Tick(6))

    def test_negative_result_is_rejected(self):
        with self.assertRaises(ValueError):
            Tick(1) - 2
        with self.assertRaises(ValueError):
            Tick(1) * -1

    def test_invalid_values_and_immutability(self):
        for value in (True, 1.5, -1):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    Tick(value)
        tick = Tick(1)
        with self.assertRaises(AttributeError):
            tick.value = 2

    def test_serialization(self):
        self.assertEqual(Tick(42).to_dict(), {"value": 42})
