"""Deterministic unit tests for the centralized random API."""
import unittest
from core.random import seed_ayarla, tam_sayi, ondalik_sayi, olasilik_yuzde, sec, agirlikli_sec

class TestRandom(unittest.TestCase):
    def test_seed_reproduces_sequence(self):
        seed_ayarla(12345); first = [tam_sayi(1, 100) for _ in range(5)]
        seed_ayarla(12345); second = [tam_sayi(1, 100) for _ in range(5)]
        self.assertEqual(first, second)
    def test_ranges_and_probability_edges(self):
        seed_ayarla(42)
        self.assertTrue(all(1 <= tam_sayi(1, 20) <= 20 for _ in range(30)))
        self.assertTrue(0.0 <= ondalik_sayi() <= 1.0)
        self.assertTrue(10 <= ondalik_sayi(10, 20) <= 20)
        self.assertFalse(olasilik_yuzde(0)); self.assertTrue(olasilik_yuzde(100))
    def test_selection(self):
        self.assertIn(sec(("a", "b")), ("a", "b"))
        self.assertEqual(agirlikli_sec(["only"], [1]), "only")
        seed_ayarla(42)
        self.assertIn(agirlikli_sec(["a", "b"], [1, 0]), ("a", "b"))
    def test_invalid_inputs(self):
        with self.assertRaises(ValueError): tam_sayi(20, 10)
        with self.assertRaises(TypeError): tam_sayi(True, 10)
        with self.assertRaises(ValueError): olasilik_yuzde(101)
        with self.assertRaises(ValueError): sec([])
        with self.assertRaises(ValueError): agirlikli_sec(["a", "b"], [0, 0])
        with self.assertRaises(ValueError): agirlikli_sec(["a"], [1, 2])

if __name__ == "__main__": unittest.main()
