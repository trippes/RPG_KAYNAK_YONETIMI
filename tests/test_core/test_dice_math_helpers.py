import unittest
from unittest.mock import patch

from core.dice import (
    zar_at,
    d20,
    d100,
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
    negatif_olmayan_mi,
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
