"""Unit tests for the legacy numeric helper API."""
import unittest
from core.math.numbers import sayi_mi, tam_sayi_mi, pozitif_mi, negatif_mi, sifir_mi, negatif_olmayan_mi, mutlak_deger

class TestNumbers(unittest.TestCase):
    def test_numeric_types_exclude_booleans(self):
        self.assertTrue(sayi_mi(10)); self.assertTrue(sayi_mi(10.5))
        self.assertFalse(sayi_mi("10")); self.assertFalse(sayi_mi(True))
        self.assertTrue(tam_sayi_mi(10)); self.assertFalse(tam_sayi_mi(10.0))
        self.assertFalse(tam_sayi_mi(False))
    def test_sign_predicates(self):
        self.assertTrue(pozitif_mi(1)); self.assertTrue(negatif_mi(-1))
        self.assertTrue(sifir_mi(0)); self.assertTrue(negatif_olmayan_mi(0))
        self.assertFalse(pozitif_mi("1")); self.assertFalse(negatif_mi(True))
        self.assertFalse(sifir_mi(None))
    def test_absolute_value(self):
        self.assertEqual(mutlak_deger(-25), 25)
        self.assertEqual(mutlak_deger(-2.5), 2.5)
        with self.assertRaises(TypeError): mutlak_deger(True)

if __name__ == "__main__": unittest.main()
