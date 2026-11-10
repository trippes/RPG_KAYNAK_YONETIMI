"""Unit tests for the game's rounding policy."""
import unittest
from core.math.rounding import asagi_yuvarla, yukari_yuvarla, en_yakina_yuvarla, oyun_yuvarla

class TestRounding(unittest.TestCase):
    def test_floor_and_ceiling(self):
        self.assertEqual(asagi_yuvarla(3.9), 3); self.assertEqual(asagi_yuvarla(-3.1), -4)
        self.assertEqual(yukari_yuvarla(3.1), 4); self.assertEqual(yukari_yuvarla(-3.1), -3)
    def test_half_away_from_zero(self):
        self.assertEqual(en_yakina_yuvarla(3.5), 4); self.assertEqual(en_yakina_yuvarla(-3.5), -4)
        self.assertEqual(oyun_yuvarla(2.5), 3); self.assertEqual(oyun_yuvarla(-2.5), -3)
    def test_invalid_inputs(self):
        with self.assertRaises(TypeError): asagi_yuvarla("5.5")
        with self.assertRaises(TypeError): oyun_yuvarla(True)

if __name__ == "__main__": unittest.main()
