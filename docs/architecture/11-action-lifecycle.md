# Core 2.0 Action Lifecycle

## State machine

```text
CREATED → SCHEDULED → STARTED → COMPLETED
      └────────────→ CANCELLED
SCHEDULED ────────→ CANCELLED
STARTED ──────────→ FAILED
STARTED ──────────→ CANCELLED
```

Terminal state'ler `COMPLETED`, `FAILED` ve `CANCELLED`'dır.

## Action contract

```text
Action {
    action_id: ActionId
    action_type: ActionType
    owner_id: EntityId | SystemId
    world_id: WorldId | None
    context: SerializableMapping
    created_tick: Tick
    start_tick: Tick | None
    duration: Tick
    result: SerializableValue | None
    failure: FailureInfo | None
    cancellation: CancellationInfo | None
    state: ActionState
}
```

`Any` canonical API'de kullanılmaz. Owner ve context typed ID/contract ile
ifade edilir.

## Transition events

| Transition | Event |
|---|---|
| create | `ActionCreated` |
| schedule | `ActionScheduled` |
| start | `ActionStarted` |
| complete | `ActionCompleted` |
| fail | `ActionFailed` |
| cancel | `ActionCancelled` |

Her event action ID, world ID, simulation tick ve transition sonucunu taşır.

FAZ 3 implementation karşılığı `core.simulation.Action` ve
`core.simulation.ActionProcessor`'dır. Action state private tutulur; geçişler
yalnızca lifecycle metotları veya processor üzerinden yapılır. Duration kuralı:

```text
completion_tick = started_tick + duration
```

## 1.x note

Mevcut `Action` modeli compatibility döneminde korunur. `action.py` içindeki
geçişleri Core 2.0 canonical lifecycle'ında uygulanmıştır. Canonical scheduler
callback çalıştırmaz; `ActionProcessor` deterministic work üretir ve event
transport'a yayınlar.
