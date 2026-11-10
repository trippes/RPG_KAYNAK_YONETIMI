import unittest

from core.compatibility.action_adapter import CanonicalActionAdapter
from core.foundation import ActionId, Identifier
from core.simulation import ActionProcessor, ActionState
from core.actions import ActionDurumu
from core.time import Tick


class TestCanonicalActionAdapter(unittest.TestCase):
    def setUp(self):
        self.processor = ActionProcessor()
        self.adapter = CanonicalActionAdapter(self.processor)

    def test_legacy_id_and_creation_map_to_canonical_action(self):
        legacy = self.adapter.aksiyon_olustur(
            tur="dinlenme",
            sahip="hero",
            sure=3,
            veri={"source": "test"},
        )

        canonical = self.processor.get(ActionId("legacy_action_000001"))

        self.assertEqual(legacy.id, 1)
        self.assertIsNotNone(canonical)
        self.assertEqual(canonical.owner_id, Identifier("hero"))
        self.assertEqual(canonical.duration, Tick(3))
        self.assertEqual(canonical.context["tur"], "dinlenme")
        self.assertEqual(canonical.context["veri"], {"source": "test"})

    def test_start_and_completion_are_reflected_in_legacy_action(self):
        legacy = self.adapter.aksiyon_olustur("work", "hero", 3)

        self.adapter.aksiyon_baslat(legacy.id, 2)
        self.assertEqual(legacy.durum, ActionDurumu.AKTIF)
        self.assertEqual(legacy.baslangic_zamani, 2)

        self.assertEqual(self.adapter.guncelle(4), [])
        self.assertEqual(legacy.durum, ActionDurumu.AKTIF)

        completed = self.adapter.guncelle(5)

        self.assertEqual(completed, [legacy])
        self.assertEqual(legacy.durum, ActionDurumu.TAMAMLANDI)
        self.assertEqual(legacy.bitis_zamani, 5)
        self.assertEqual(self.processor.get(ActionId("legacy_action_000001")).state, ActionState.COMPLETED)

    def test_canonical_failure_is_mapped_to_legacy_failure(self):
        legacy = self.adapter.aksiyon_olustur("work", "hero", 3)
        self.adapter.aksiyon_baslat(legacy.id, 0)
        self.adapter.guncelle(0)

        self.processor.fail(ActionId("legacy_action_000001"), "resource unavailable")
        self.adapter.guncelle(0)

        self.assertEqual(legacy.durum, ActionDurumu.BASARISIZ)
        self.assertEqual(legacy.sonuc, "resource unavailable")

    def test_missing_legacy_action_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.adapter.aksiyon_baslat(999, 0)


if __name__ == "__main__":
    unittest.main()
