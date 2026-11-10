"""Unit tests for dice rolling and expression parsing."""
import unittest
from core.dice import (zar_at, zar_havuzu_at, zar_toplami, dusukleri_cikar, yuksekleri_cikar, zar_ifadesi_ayristir, zar_ifadesi_at, dort_d_alti_eksi_en_dusuk, d20, d100)
from core.random import seed_ayarla

class TestDice(unittest.TestCase):
    def setUp(self): seed_ayarla(42)
    def test_single_and_pool_rolls(self):
        self.assertIn(zar_at(20), range(1, 21))
        values = zar_havuzu_at(4, 6)
        self.assertEqual(len(values), 4)
        self.assertTrue(all(1 <= value <= 6 for value in values))
        self.assertTrue(2 <= zar_toplami(2, 6) <= 12)
    def test_drop_lowest_and_highest(self):
        seed_ayarla(7); low = dusukleri_cikar(4, 6, 1)
        self.assertEqual(low["kalanlar"], low["sirali_sonuclar"][1:])
        self.assertEqual(low["toplam"], sum(low["kalanlar"]))
        seed_ayarla(7); high = yuksekleri_cikar(4, 6, 1)
        self.assertEqual(high["kalanlar"], high["sirali_sonuclar"][:-1])
        self.assertEqual(high["toplam"], sum(high["kalanlar"]))
        self.assertEqual(len(dort_d_alti_eksi_en_dusuk()["kalanlar"]), 3)
    def test_expression_parsing_and_rolling(self):
        self.assertEqual(zar_ifadesi_ayristir("2d8+3"), {"adet": 2, "zar": 8, "degistirici": 3})
        self.assertEqual(zar_ifadesi_ayristir("2d8-1")["degistirici"], -1)
        result = zar_ifadesi_at("2d6+3")
        self.assertEqual(result["toplam"], sum(result["sonuclar"]) + 3)
        self.assertIn(d20(), range(1, 21)); self.assertIn(d100(), range(1, 101))
    def test_invalid_rolls_and_expressions(self):
        with self.assertRaises(ValueError): zar_at(7)
        with self.assertRaises(TypeError): zar_at(True)
        with self.assertRaises(ValueError): zar_havuzu_at(0, 6)
        with self.assertRaises(ValueError): dusukleri_cikar(4, 6, 4)
        with self.assertRaises(ValueError): yuksekleri_cikar(4, 6, 4)
        with self.assertRaises(ValueError): zar_ifadesi_ayristir("5d7")
        with self.assertRaises(ValueError): zar_ifadesi_ayristir("abc")

if __name__ == "__main__": unittest.main()
