"""Unit tests for ratio and percentage helpers."""
import unittest
from core.math.ratios import yuzde_hesapla, yuzde_artir, yuzde_azalt, katsayi_uygula, bonus_uygula, ceza_uygula, oran_hesapla

class TestRatios(unittest.TestCase):
    def test_percentage_operations(self):
        self.assertEqual(yuzde_hesapla(100, 20), 20)
        self.assertEqual(yuzde_artir(100, 20), 120)
        self.assertEqual(yuzde_azalt(100, 20), 80)
        self.assertEqual(bonus_uygula(100, 20), 120)
        self.assertEqual(ceza_uygula(100, 20), 80)
    def test_multiplier_and_ratio(self):
        self.assertEqual(katsayi_uygula(100, 1.25), 125)
        self.assertEqual(oran_hesapla(25, 100), 0.25)
    def test_invalid_inputs(self):
        with self.assertRaises(TypeError): yuzde_hesapla(100, "20")
        with self.assertRaises(ZeroDivisionError): oran_hesapla(25, 0)

if __name__ == "__main__": unittest.main()
