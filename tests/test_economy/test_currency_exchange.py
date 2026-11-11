import unittest

from economy import (
    BRONZE_CURRENCY, GOLD_CURRENCY, SILVER_CURRENCY,
    Currency, CurrencyExchange, Ledger, Money,
)


class TestCurrencyExchange(unittest.TestCase):
    def setUp(self):
        self.exchange = CurrencyExchange()
        self.ledger = Ledger()

    def test_fixed_exchange_rates(self):
        self.assertEqual(self.exchange.convert(Money(60, BRONZE_CURRENCY), SILVER_CURRENCY), Money(1, SILVER_CURRENCY))
        self.assertEqual(self.exchange.convert(Money(60, SILVER_CURRENCY), GOLD_CURRENCY), Money(1, GOLD_CURRENCY))
        self.assertEqual(self.exchange.convert(Money(3600, BRONZE_CURRENCY), GOLD_CURRENCY), Money(1, GOLD_CURRENCY))

    def test_conversion_to_smaller_denominations(self):
        self.assertEqual(self.exchange.convert(Money(1, GOLD_CURRENCY), SILVER_CURRENCY), Money(60, SILVER_CURRENCY))
        self.assertEqual(self.exchange.convert(Money(1, SILVER_CURRENCY), BRONZE_CURRENCY), Money(60, BRONZE_CURRENCY))
        self.assertEqual(self.exchange.convert(Money(1, GOLD_CURRENCY), BRONZE_CURRENCY), Money(3600, BRONZE_CURRENCY))

    def test_non_exact_conversion_is_rejected(self):
        for source, target in (
            (Money(59, BRONZE_CURRENCY), SILVER_CURRENCY),
            (Money(3599, BRONZE_CURRENCY), GOLD_CURRENCY),
            (Money(61, SILVER_CURRENCY), GOLD_CURRENCY),
        ):
            with self.subTest(source=source, target=target), self.assertRaises(ValueError):
                self.exchange.convert(source, target)

    def test_unknown_currency_is_rejected(self):
        with self.assertRaises(ValueError):
            self.exchange.convert(Money(60, Currency("copper")), SILVER_CURRENCY)
        with self.assertRaises(ValueError):
            self.exchange.convert(Money(60, BRONZE_CURRENCY), Currency("copper"))

    def test_exchange_updates_balances_and_audit_entries(self):
        self.ledger.credit("hero", Money(120, BRONZE_CURRENCY))
        received = self.exchange.exchange(
            self.ledger, "hero", Money(60, BRONZE_CURRENCY), SILVER_CURRENCY,
        )
        self.assertEqual(received, Money(1, SILVER_CURRENCY))
        self.assertEqual(self.ledger.balance("hero", BRONZE_CURRENCY).amount, 60)
        self.assertEqual(self.ledger.balance("hero", SILVER_CURRENCY).amount, 1)
        self.assertEqual(len(self.ledger.entries()), 3)
        self.assertEqual(self.ledger.entries()[-2].direction, "debit")
        self.assertEqual(self.ledger.entries()[-1].direction, "credit")

    def test_insufficient_balance_does_not_mutate_ledger(self):
        self.ledger.credit("hero", Money(59, BRONZE_CURRENCY))
        before, entry_count = self.ledger.accounts(), len(self.ledger.entries())
        with self.assertRaises(ValueError):
            self.exchange.exchange(
                self.ledger, "hero", Money(60, BRONZE_CURRENCY), SILVER_CURRENCY,
            )
        self.assertEqual(self.ledger.accounts(), before)
        self.assertEqual(len(self.ledger.entries()), entry_count)

    def test_same_currency_and_zero_amount_are_rejected(self):
        with self.assertRaises(ValueError):
            self.exchange.convert(Money(1, GOLD_CURRENCY), GOLD_CURRENCY)
        with self.assertRaises(ValueError):
            self.exchange.convert(Money(0, BRONZE_CURRENCY), SILVER_CURRENCY)


if __name__ == "__main__":
    unittest.main()
