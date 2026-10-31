# Core 2.0 Package Layout

```text
core/
├── foundation/
│   ├── ids.py                 # Identifier, EntityId, WorldId, EventId
│   ├── errors.py
│   ├── result.py
│   ├── math/
│   └── random/
├── domain/
│   ├── entity/
│   ├── world/
│   ├── spatial/
│   │   └── position.py        # immutable Position
│   └── actions/
├── time/
│   ├── tick.py                # immutable simulation Tick
│   ├── game_time.py
│   ├── calendar.py
│   ├── clock.py
│   └── scheduler.py
├── events/
│   ├── event.py
│   ├── event_type.py
│   ├── event_queue.py
│   ├── event_bus.py
│   └── dispatcher.py
├── application/
│   ├── session.py
│   ├── entity_repository.py
│   ├── ownership.py
│   ├── game_state.py
│   ├── world_registry.py
│   ├── entity_registry.py
│   └── commands/
├── simulation/
│   ├── scheduler.py
│   ├── action.py
│   ├── action_processor.py
│   ├── events.py
│   └── runtime.py
└── compatibility/
    └── v1/
```

Gameplay, persistence ve UI bu ağacın dışında kalır:

```text
gameplay/{character,combat,economy,inventory,npc,quests,resources}/
adapters/{save,pygame,cli,logging}/
```

Bu aşamada bu paketler implement edilmeyecektir. Layout, Core 2.0 için hedef
contract'tır; mevcut 1.x modülleri compatibility süreci tamamlanana kadar
yerinde kalır.
