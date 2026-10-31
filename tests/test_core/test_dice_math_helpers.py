import unittest
from unittest.mock import patch

from core.dice import (
    zar_at,
    zar_havuzu_at,
    zar_toplami,
    dusukleri_cikar,
    yuksekleri_cikar,
    zar_ifadesi_ayristir,
    zar_ifadesi_at,
    dort_d_alti_eksi_en_dusuk,
)
from core.random import (
    seed_ayarla,
    tam_sayi,
    ondalik_sayi,
    olasilik_yuzde,
    sec,
    agirlikli_sec,
)
from core.math.numbers import (
    sayi_mi,
    tam_sayi_mi,
    pozitif_mi,
    negatif_mi,
    sifir_mi,
    mutlak_deger,
)
from core.math.operations import topla, cikar, carp, bol, mod, minimum, maksimum
from core.math.ratios import (
    yuzde_hesapla,
    yuzde_artir,
    yuzde_azalt,
    katsayi_uygula,
    bonus_uygula,
    ceza_uygula,
    oran_hesapla,
)
from core.math.rounding import asagi_yuvarla, yukari_yuvarla, en_yakina_yuvarla, oyun_yuvarla


class TestDiceHelpers(unittest.TestCase):
    def test_supported_dice(self):
        for sides in (4, 6, 8, 10, 12, 20, 100):
            with self.subTest(sides=sides):
                result = zar_at(sides)
                self.assertGreaterEqual(result, 1)
                self.assertLessEqual(result, sides)

    def test_unsupported_die_rejected(self):
        with self.assertRaises((ValueError, TypeError)):
            zar_at(7)

    def test_zero_dice_rejected(self):
        with self.assertRaises((ValueError, TypeError)):
            zar_havuzu_at(0, 6)

    def test_dice_pool_size_and_range(self):
        results = zar_havuzu_at(20, 6)
        self.assertEqual(len(results), 20)
        self.assertTrue(all(1 <= result <= 6 for result in results))

    def test_dice_total_matches_pool(self):
        seed_ayarla(12345)
        pool = zar_havuzu_at(5, 6)
        seed_ayarla(12345)
        self.assertEqual(zar_toplami(5, 6), sum(pool))

    def test_drop_lowest(self):
        with patch("core.dice.zar_havuzu_at", return_value=[6, 2, 5, 3]):
            result = dusukleri_cikar(4, 6, 1)
        self.assertEqual(result["kalanlar"], [3, 5, 6])
        self.assertEqual(result["cikarilanlar"], [2])
        self.assertEqual(result["toplam"], 14)

    def test_drop_highest(self):
        with patch("core.dice.zar_havuzu_at", return_value=[6, 2, 5, 3]):
            result = yuksekleri_cikar(4, 6, 1)
        self.assertEqual(result["kalanlar"], [2, 3, 5])
        self.assertEqual(result["cikarilanlar"], [6])
        self.assertEqual(result["toplam"], 10)

    def test_parse_valid_dice_expressions(self):
        for expression in ("1d20", "2d6", "4d6", "2d8+3", "2d8-1", "1d100"):
            with self.subTest(expression=expression):
                self.assertIsNotNone(zar_ifadesi_ayristir(expression))

    def test_invalid_expression_rejected(self):
        for expression in ("abc", "5d7"):
            with self.subTest(expression=expression):
                with self.assertRaises((ValueError, TypeError)):
                    zar_ifadesi_at(expression)

    def test_seed_repeats_expression_result(self):
        seed_ayarla(9876)
        first = zar_ifadesi_at("4d6")
        seed_ayarla(9876)
        second = zar_ifadesi_at("4d6")
        self.assertEqual(first, second)

    def test_four_d6_drop_lowest(self):
        result = dort_d_alti_eksi_en_dusuk()["toplam"]
        self.assertGreaterEqual(result, 3)
        self.assertLessEqual(result, 18)


class TestRandomHelpers(unittest.TestCase):
    def test_integer_random_range(self):
        for _ in range(50):
            result = tam_sayi(3, 9)
            self.assertGreaterEqual(result, 3)
            self.assertLessEqual(result, 9)

    def test_integer_random_rejects_boolean(self):
        with self.assertRaises((ValueError, TypeError)):
            tam_sayi(True, 10)

    def test_seed_reproducibility(self):
        seed_ayarla(42)
        first = [tam_sayi(1, 100) for _ in range(5)]
        seed_ayarla(42)
        second = [tam_sayi(1, 100) for _ in range(5)]
        self.assertEqual(first, second)

    def test_decimal_random_range(self):
        result = ondalik_sayi(10.0, 20.0)
        self.assertGreaterEqual(result, 10.0)
        self.assertLessEqual(result, 20.0)

    def test_probability_endpoints(self):
        self.assertIs(olasilik_yuzde(0), False)
        self.assertIs(olasilik_yuzde(100), True)

    def test_choice_rejects_empty_sequence(self):
        with self.assertRaises((ValueError, TypeError)):
            sec([])

    def test_weighted_choice_rejects_zero_weights(self):
        with self.assertRaises((ValueError, TypeError)):
            agirlikli_sec(["a", "b"], [0, 0])


class TestNumberHelpers(unittest.TestCase):
    def test_number_predicates(self):
        self.assertTrue(sayi_mi(3.5))
        self.assertTrue(tam_sayi_mi(3))
        self.assertFalse(tam_sayi_mi(3.5))

    def test_boolean_is_not_number(self):
        self.assertFalse(sayi_mi(True))
        self.assertFalse(tam_sayi_mi(False))

    def test_sign_predicates(self):
        self.assertTrue(pozitif_mi(1))
        self.assertTrue(negatif_mi(-1))
        self.assertTrue(sifir_mi(0))

    def test_absolute_value(self):
        self.assertEqual(mutlak_deger(-7), 7)
        self.assertEqual(mutlak_deger(7), 7)


class TestMathOperations(unittest.TestCase):
    def test_basic_operations(self):
        self.assertEqual(topla(2, 3), 5)
        self.assertEqual(cikar(7, 4), 3)
        self.assertEqual(carp(3, 4), 12)
        self.assertEqual(bol(8, 2), 4)
        self.assertEqual(mod(8, 3), 2)

    def test_minimum_and_maximum(self):
        self.assertEqual(minimum(2, 8), 2)
        self.assertEqual(maksimum(2, 8), 8)

    def test_division_by_zero_rejected(self):
        with self.assertRaises((ValueError, ZeroDivisionError)):
            bol(10, 0)


class TestRatioHelpers(unittest.TestCase):
    def test_percentage(self):
        self.assertAlmostEqual(yuzde_hesapla(200, 10), 20)

    def test_increase_and_decrease(self):
        self.assertAlmostEqual(yuzde_artir(100, 10), 110)
        self.assertAlmostEqual(yuzde_azalt(100, 10), 90)

    def test_multiplier_bonus_penalty(self):
        self.assertAlmostEqual(katsayi_uygula(100, 1.5), 150)
        self.assertAlmostEqual(bonus_uygula(100, 10), 110)
        self.assertAlmostEqual(ceza_uygula(100, 10), 90)

    def test_ratio(self):
        self.assertAlmostEqual(oran_hesapla(25, 100), 0.25)

    def test_zero_total_ratio_rejected(self):
        with self.assertRaises((ValueError, ZeroDivisionError)):
            oran_hesapla(10, 0)


class TestRoundingHelpers(unittest.TestCase):
    def test_floor_and_ceiling(self):
        self.assertEqual(asagi_yuvarla(3.8), 3)
        self.assertEqual(yukari_yuvarla(3.2), 4)

    def test_negative_floor_and_ceiling(self):
        self.assertEqual(asagi_yuvarla(-3.2), -4)
        self.assertEqual(yukari_yuvarla(-3.2), -3)

    def test_nearest_rounding(self):
        self.assertEqual(en_yakina_yuvarla(3.5), 4)
        self.assertEqual(en_yakina_yuvarla(-3.5), -4)

    def test_game_rounding(self):
        self.assertEqual(oyun_yuvarla(2.5), 3)


if __name__ == "__main__":
    unittest.main()


