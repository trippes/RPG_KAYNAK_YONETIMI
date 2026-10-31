# Phase 5 — Event Schema Versioning

Canonical `SimulationEvent.schema_version` pozitif immutable integer'dır ve
default değeri `1`'dir. Event identity (`event_id`) ve ordering alanlarından
bağımsızdır; schema version değiştirmek event sırasını değiştirmez.

Canonical envelope şu alanları taşır:

`event_type`, `schema_version`, `event_id`, `simulation_tick`, `source_id`,
`target_id`, `action_id`, `payload`, `metadata`.

Payload ve metadata defensive deep-copy ile alınır ve mapping proxy olarak
sunulur. Bu faz serialization veya migration transform implementasyonu içermez;
yalnızca ileride v1 → v2 dönüşümleri için açık contract oluşturur.

Event schema version ile persistence schema version ayrıdır; event replay veya
event sourcing Core 2.0 persistence davranışı değildir.
