"""Unit tests for arithmetic helpers."""
import unittest
from core.math.operations import topla, cikar, carp, bol, mod, minimum, maksimum

class TestOperations(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(topla(10, 5), 15); self.assertEqual(cikar(10, 5), 5)
        self.assertEqual(carp(10, 5), 50); self.assertEqual(bol(10, 5), 2)
        self.assertEqual(mod(10, 3), 1)
    def test_minimum_and_maximum(self):
        self.assertEqual(minimum(10, 5), 5); self.assertEqual(maksimum(10, 5), 10)
    def test_invalid_operands_and_zero_divisors(self):
        with self.assertRaises(TypeError): topla(10, "5")
        with self.assertRaises(TypeError): carp(True, 2)
        with self.assertRaises(ZeroDivisionError): bol(10, 0)
        with self.assertRaises(ZeroDivisionError): mod(10, 0)

if __name__ == "__main__": unittest.main()
