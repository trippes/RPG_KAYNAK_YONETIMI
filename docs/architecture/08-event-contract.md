# Core 2.0 Event Contract

## Seçilen model

Core 2.0 hierarchical event architecture kullanır:

```text
World/System producer
        ↓
Runtime dispatcher
        ↓
Canonical session EventQueue
        ↓
EventBus subscribers
```

World-local staging queue 1.x compatibility mekanizmasıdır. 2.x canonical
modelde producer olayını session dispatcher'a verir; `Game` üzerinde manuel
`dunya_olaylarini_aktar()` çağrısı yapılmaz.

## Event envelope

```text
Event {
    event_id: EventId
    event_type: EventType
    schema_version: int
    simulation_tick: Tick
    source_id: EntityId | SystemId | None
    target_id: EntityId | None
    world_id: WorldId | None
    payload: TypedPayload
    metadata: Mapping[str, SerializableValue]
}
```

`payload` typed ve versioned olmalıdır. 1.x'teki `dict` payload yalnızca
compatibility formatıdır. `metadata` ordering veya simulation state üretmek
için kullanılamaz.

## Ordering

Event sırası önce `simulation_tick`, sonra dispatcher insertion sequence ile
belirlenir. Wall-clock zamanı ordering'e katılmaz.

## Errors

Handler exception'ları dispatcher tarafından gizlenmez. Runtime policy,
exception'ı failure/diagnostic event'e dönüştürüp simulation'ı durdurma veya
izole etme kararını verir. Bu karar EventBus'ın domain contract'ı değildir.

## Constants

Event isimlerinin tek kaynağı `EventType`/typed event registry olacaktır.
`constants.py` event isimleri için kullanılmayacaktır.

FAZ 3 canonical action event'leri `SimulationEvent` envelope'u kullanır ve
`simulation_tick`, `source_id`, `target_id`, `action_id`, typed payload ve
metadata taşır. Mevcut 1.x `EventBus/EventQueue` bu fazda yeniden yazılmaz.

## Phase 4 canonical transport

`core.simulation.transport.CanonicalEventTransport` canonical queue'dur.
`SimulationEvent` immutable'dır; payload ve metadata derin kopyalanıp mapping
proxy ile dış mutasyona kapatılır. Transport enqueue sırasında eksik kimlik için
deterministic `EventId` ve insertion sequence atar. Aynı EventId ikinci kez
enqueue edilirse açıkça reddedilir.

Ordering yalnızca `(simulation_tick, insertion_sequence)` anahtarına dayanır.
EventId, payload, dictionary veya wall-clock timestamp ordering'e katılmaz.
Bu nedenle aynı tick içindeki olaylar enqueue sırasını, farklı tick'ler ise tick
sırasını korur.

## Legacy sınırı

1.x `Event`, `EventQueue`, `EventBus`, `EventManager` ve
`Game.dunya_olaylarini_aktar()` korunur. `LegacyEventAdapter` bir 1.x Event'i
canonical `SimulationEvent`'e çevirir; legacy EventBus davranışını değiştirmez.
`dunya_olaylarini_aktar()` legacy compatibility API'sidir. Yeni 2.x kodu
`SimulationRuntime.dispatch_world_events()` veya Game üzerindeki canonical
boundary metodunu kullanır.

## Dispatcher ve consumer contract

`CanonicalEventDispatcher` yalnızca `consume(event)` metodunu bilen küçük bir
consumer arayüzü sunar. Registration sırası bir listedir ve aynı event için
consumer'lar registration sırasıyla çağrılır. Event type filtresi opsiyoneldir.

Bir dispatch cycle başında transport'taki event sayısı snapshot alınır. Consumer
sırasında enqueue edilen nested event aynı cycle'a girmez; sonraki
`dispatch_pending()` cycle'ında işlenir. Consumer içinden tekrar dispatch
çağrısı `RuntimeError` ile reddedilir.

Phase 10 final akışı `SimulationEvent → CanonicalEventTransport →
CanonicalEventDispatcher` olarak dondurulmuştur. Legacy EventBus/EventQueue
yalnızca compatibility adapter yüzeyidir.
