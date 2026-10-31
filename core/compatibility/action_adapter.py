"""Compatibility facade backed by the canonical ActionProcessor."""

from core.actions.action import Action as LegacyAction, ActionDurumu
from core.foundation import ActionId, Identifier
from core.simulation import ActionProcessor, ActionState
from core.time import Tick


class CanonicalActionAdapter:
    """Keep the 1.x action shape while delegating lifecycle to Core 2.x."""

    def __init__(self, processor: ActionProcessor) -> None:
        if not isinstance(processor, ActionProcessor):
            raise TypeError("processor must be ActionProcessor.")
        self._processor = processor
        self._legacy: dict[int, LegacyAction] = {}
        self._canonical_by_legacy: dict[int, ActionId] = {}
        self._next_id = 1

    @property
    def processor(self) -> ActionProcessor:
        return self._processor

    def aksiyon_olustur(self, tur, sahip, sure, veri=None):
        legacy_id = self._next_id
        action_id = ActionId(f"legacy_action_{legacy_id:06d}")
        canonical = self._processor.create(
            owner_id=Identifier(str(sahip)),
            duration=Tick(sure),
            context={"tur": tur, "veri": dict(veri or {})},
            action_id=action_id,
        )
        legacy = LegacyAction(tur=tur, sahip=sahip, sure=sure, veri=dict(veri or {}), id=legacy_id)
        self._legacy[legacy_id] = legacy
        self._canonical_by_legacy[legacy_id] = canonical.action_id
        self._next_id += 1
        return legacy

    def aksiyon_baslat(self, aksiyon_id, zaman):
        legacy = self._get(aksiyon_id)
        self._processor.schedule(self._canonical_by_legacy[aksiyon_id], Tick(zaman))
        legacy.baslat(zaman)
        return legacy

    def guncelle(self, zaman):
        self._processor.advance_to(Tick(zaman))
        completed = []
        for legacy_id, legacy in self._legacy.items():
            canonical = self._processor.get(self._canonical_by_legacy[legacy_id])
            if canonical is None:
                continue
            if canonical.state == ActionState.COMPLETED and legacy.durum == ActionDurumu.AKTIF:
                legacy.tamamla(canonical.completed_tick.value, canonical.result)
                completed.append(legacy)
            elif canonical.state == ActionState.FAILED and legacy.durum == ActionDurumu.AKTIF:
                legacy.basarisiz(canonical.failure)
            elif canonical.state == ActionState.CANCELLED and legacy.durum in (ActionDurumu.BEKLIYOR, ActionDurumu.AKTIF):
                legacy.iptal_et()
        return completed

    def aksiyon_getir(self, aksiyon_id):
        return self._legacy.get(aksiyon_id)

    def aksiyon_sayisi(self):
        return len(self._legacy)

    def aktif_aksiyonlar(self):
        return [action for action in self._legacy.values() if action.durum == ActionDurumu.AKTIF]

    def bekleyen_aksiyonlar(self):
        return [action for action in self._legacy.values() if action.durum == ActionDurumu.BEKLIYOR]

    def tamamlanan_aksiyonlar(self):
        return [action for action in self._legacy.values() if action.durum == ActionDurumu.TAMAMLANDI]

    def _get(self, action_id):
        action = self._legacy.get(action_id)
        if action is None:
            raise KeyError(f"Aksiyon bulunamadi: {action_id}")
        return action
