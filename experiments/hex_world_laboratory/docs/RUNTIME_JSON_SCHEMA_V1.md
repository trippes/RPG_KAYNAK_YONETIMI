# Runtime Snapshot JSON Schema v1

Runtime snapshots store only sparse changes to a single loaded map. The immutable base map remains in its Stage 3.6 map JSON file.

## Top-level document

| Field | Type | Rule |
|---|---|---|
| `schema_version` | integer | Exactly `1`; booleans are not integers here |
| `kind` | string | Exactly `hex_world_runtime_snapshot` |
| `world_id` | string | Non-empty; must match the target map |
| `map_id` | string | Non-empty; must match the target map |
| `base_map_sha256` | string | 64 lowercase hexadecimal characters; must match the canonical Stage 3.6 map serialization |
| `overrides` | array | Zero or more unique cell override objects |

## Override object

Each object requires integer `q` and `r` and at least one of:

- `terrain_id`: non-empty string
- `is_walkable`: boolean
- `has_obstacle`: boolean

Coordinates must exist in the base map and may appear only once. Unknown fields, null values, duplicate coordinates, redundant values equal to the base cell, NaN, Infinity, and duplicate JSON object keys are rejected. Metadata, geometry, cell existence, and game-object data are not part of this format.

An empty `overrides` array is valid and means that restoring the snapshot clears all runtime overrides for that map.

## Fingerprint

`base_map_sha256` is SHA-256 over the UTF-8 bytes of `serialize_map(map_definition)`, including its deterministic indentation and final newline. It detects an incompatible base map; it is not a cryptographic authenticity signature.

## Python API

- `runtime_to_payload(runtime, map_definition)`
- `serialize_runtime(runtime, map_definition)`
- `deserialize_runtime_payload(payload, map_definition)`
- `save_runtime_file(runtime, map_definition, path, mode="create")`
- `load_runtime_file(path, map_definition)`: validates and returns an immutable snapshot without changing runtime state.
- `restore_runtime_file(runtime, map_definition, path)`: validates the complete file before replacing the target map's complete override set.

The default `create` mode never overwrites an existing file. Use `mode="replace"` for an explicit atomic replacement. Save and restore require the map to be registered and loaded. Runtime overrides remain in memory during unload, as defined in Stage 3.5; this persistence layer does not automatically save on unload.
