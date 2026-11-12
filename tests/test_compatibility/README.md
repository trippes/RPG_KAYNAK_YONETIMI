# Compatibility contract tests

This package intentionally holds tests for the public 1.x compatibility surface and its adapters. These tests are not candidates for deletion merely because newer canonical implementations exist.

| Test module | Compatibility contract retained | Canonical implementation / migration boundary |
|---|---|---|
| `test_legacy_event_bus.py` | EventBus subscription, dispatch ordering, re-entrancy and exception behavior | Canonical event dispatcher / transport |
| `test_legacy_event_manager.py` | EventManager creation, FIFO queue and dispatch facade | `CanonicalEventManagerAdapter` |
| `test_event_manager_adapter.py` | Legacy queue projection backed by canonical transport | `CanonicalEventTransport` |
| `test_legacy_time_system.py` | `time_system` imports, GameTime, Calendar, Tick alias and clock-facing behavior | `core.time.Tick`, `core.clock.GameClock` |
| `test_legacy_scheduler.py` | Callback-based `time_system.Scheduler` contract | `LegacyCallbackSchedulerAdapter` over `CanonicalScheduler` |
| `test_legacy_scheduler_adapter.py` | Adapter FIFO, cancellation, reset and exception semantics | `CanonicalScheduler` |
| `test_legacy_world_clock.py` | `World` clock and time-advance compatibility projection | Canonical session/world runtime boundary |
| `test_legacy_world_scheduler.py` | `World` callback scheduling and event projection | Typed canonical scheduler and event transport |

Retirement rule: keep these tests until the corresponding `core.compatibility.LEGACY_API_MATRIX` entry is explicitly retired, runtime/static usage reports are clean for the supported consumers, and a separate migration decision approves removal. Canonical-only tests remain in their domain packages (for example, `tests/test_time/test_canonical_tick.py`).
