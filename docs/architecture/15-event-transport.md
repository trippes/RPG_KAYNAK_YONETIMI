# Phase 4 — Canonical Event Transport

## Akış

```text
SimulationRuntime / ActionProcessor
World-local EventQueue
          ↓
Runtime dispatcher / LegacyEventAdapter
          ↓
CanonicalEventTransport
          ↓
Runtime/Application consumers
```

Transport bir subscriber bus değildir; yalnızca immutable `SimulationEvent`
envelope'larını taşır. `enqueue`, `dequeue`, `peek`, `empty`, `count`, `drain`
ve `clear` kontrollü API'leridir.

## Sıralama ve identity

Her enqueue işlemi deterministic bir insertion sequence alır. İşleme sırası
`simulation_tick`, sonra insertion sequence'tir. EventId yalnızca canonical
identity'dir; sıralama anahtarı değildir. Aynı EventId tekrar enqueue edilirse
duplicate policy olarak `ValueError` verilir.

`SimulationEvent.event_id` ve `insertion_sequence` transport tarafından atanır.
Payload/metadata derin kopyalanır ve mapping proxy ile immutable hale getirilir.
Bu tasarım ileride serialize edilebilir value-object sınırını korur, fakat bu
fazda persistence/serialization implementasyonu yapmaz.

## Runtime ve action lifecycle

ActionProcessor `ActionCreated`, `ActionScheduled`, `ActionStarted`,
`ActionCompleted`, `ActionFailed` ve `ActionCancelled` eventlerini doğrudan
runtime'ın canonical transport'una yayınlar. `advance_to()` eski Phase 3 tuple
çıktısını korur.

## World routing ve migration

World kendi local EventQueue'sunu korur. Runtime dispatcher bir legacy Event'i
World tick'i ile canonical envelope'a dönüştürür. World global Game queue'suna
bağlanmaz. `Game.dunya_olaylarini_aktar()` 1.x compatibility için korunur;
canonical kullanım `dunya_olaylarini_canonical_aktar()` veya doğrudan runtime
dispatcher'dır. `EventType` ve `constants.py` tekrarları bu fazda kaldırılmaz;
canonical action type kaynağı `CanonicalEventType`'tır.

Transport üzerine `CanonicalEventDispatcher` bulunur. Dispatcher consumer'ları
registration order ile çağırır; filtre verilirse yalnızca seçilen event type'ları
iletir. Cycle snapshot nedeniyle consumer tarafından üretilen event sonraki
cycle'a kalır. Re-entrant dispatch reddedilir.

Freeze contract: ordering `(simulation_tick, insertion_sequence)` ile belirlenir;
`EventId`, schema version ve immutable payload/metadata canonical envelope'in
parçasıdır.
