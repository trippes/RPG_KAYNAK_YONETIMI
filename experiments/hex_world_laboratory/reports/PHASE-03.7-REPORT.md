# Phase 3.7 — Runtime Persistence Implementation Report

**Status:** Implementation complete; local verification passed.  
**Branch:** `experiment/hex-world-laboratory`  
**Plan:** `reports/PHASE-03.7-TECHNICAL-PLAN.md`

## 1. Objective and scope

Phase 3.7 adds persistence for sparse runtime cell changes while preserving the immutable base-map JSON introduced in Phase 3.6. Runtime snapshots contain only changes to `terrain_id`, `is_walkable`, and `has_obstacle`; they do not duplicate map geometry or base cell data.

The implementation remains isolated to the Hex World Laboratory. It does not add player/entity/NPC/inventory/quest persistence, full save slots, autosave, multi-map transactional manifests, automatic map loading/eviction, offline simulation, movement, rendering, or main-game integration.

## 2. Delivered implementation

- Added runtime snapshot validation, serialization, deserialization, typed errors, and UTF-8 file storage.
- Added deterministic schema v1 payloads containing WorldId, MapId, base-map SHA-256, and sparse coordinate overrides.
- Added immutable decoded snapshots and runtime APIs to export and atomically replace one map's override set.
- Added compatibility validation against the canonical Stage 3.6 map serialization fingerprint.
- Added strict checks for schema version, kind, IDs, hash, duplicate keys/coordinates, unknown fields, invalid values, missing cells, redundant base-equal values, and malformed JSON.
- Added safe `create` behavior that refuses overwrite and explicit `replace` behavior using temporary-file publication and atomic replacement.
- Restore fully parses and validates before replacing the target map's complete override set; a failed restore leaves existing runtime state unchanged.
- Added the Starting Valley runtime sample, schema documentation, integration/unit tests, and a 100/1,000/10,000 override benchmark.
- Extended the dedicated laboratory CI workflow to execute the runtime persistence benchmark.

## 3. Verification

### Local Windows test suite

Executed by the project owner in the laboratory virtual environment:

```text
python -m pytest -q
288 passed in 2.01s
```

The initial run exposed two issues: one test fixture referenced coordinates absent from its map, and one error construction did not pass the required world/map/coordinate context. Both were corrected. The complete suite was then rerun successfully: **288 passed, 0 failed**.

### Runtime persistence benchmark

The owner supplied the following benchmark output from the laboratory environment:

| Overrides | JSON size | Serialize | Deserialize | Save | Load | Peak traced memory |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 7,706 bytes | 5.89 ms | 10.62 ms | 3.27 ms | 9.38 ms | 81.6 KiB |
| 1,000 | 77,007 bytes | 47.99 ms | 62.88 ms | 7.69 ms | 20.04 ms | 810.3 KiB |
| 10,000 | 788,008 bytes | 460.14 ms | 996.30 ms | 63.37 ms | 117.44 ms | 7,333.9 KiB |

These are single-run measurements, not performance guarantees or CI thresholds. The 10,000-override deserialization time is a candidate for later profiling; no speculative optimization was introduced in this phase.

### GitHub Actions

At report preparation time, the GitHub connector returned no workflow run or commit status associated with the latest implementation commit. Therefore, no remote CI success is claimed in this report. The dedicated workflow is configured to run the full laboratory test suite and both persistence benchmarks on pushes to this branch.

## 4. Design guarantees retained

- Base map definitions remain immutable and separate from runtime deltas.
- Runtime overrides remain sparse and scoped by MapId within their owning WorldId.
- Snapshot restore replaces the complete override set for one map rather than merging stale values.
- Save and restore require the target map to be registered and loaded.
- In-memory runtime overrides continue to survive map unload/reload, as specified in Phase 3.5.
- A base-map fingerprint mismatch rejects restoration before runtime mutation.
- The persistence API does not depend on Pygame or rendering.

## 5. Files delivered

Implementation and tests are contained in:

- `src/hex_world_lab/world/runtime.py`
- `src/hex_world_lab/world/persistence/runtime_errors.py`
- `src/hex_world_lab/world/persistence/runtime_validator.py`
- `src/hex_world_lab/world/persistence/runtime_serializer.py`
- `src/hex_world_lab/world/persistence/runtime_deserializer.py`
- `src/hex_world_lab/world/persistence/runtime_file_storage.py`
- `tests/unit/test_world/test_runtime.py`
- `tests/unit/test_persistence/test_runtime_validator.py`
- `tests/unit/test_persistence/test_runtime_serializer.py`
- `tests/unit/test_persistence/test_runtime_file_storage.py`
- `tests/integration/test_runtime_persistence.py`
- `scenarios/runtime/starting_valley.runtime.json`
- `docs/RUNTIME_JSON_SCHEMA_V1.md`
- `scripts/benchmark_runtime_persistence.py`
- `.github/workflows/hex-world-lab-ci.yml`

## 6. Phase boundary and next decision

Phase 3.7 implementation and the owner's local full-suite verification are complete. This report does not itself authorize Phase 4. The overall Phase 3 closure still requires an integrated review of Phases 3.1–3.7, confirmation of any outstanding CI status, and explicit owner acceptance. Phase 4 remains blocked until that process is complete.
