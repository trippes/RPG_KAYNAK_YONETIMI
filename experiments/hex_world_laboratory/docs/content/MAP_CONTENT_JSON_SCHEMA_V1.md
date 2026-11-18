# Map Content JSON Schema v1

**Kind:** `eldoria_map_document`  
**Version:** `schema_version: 1`  \n**Machine-readable schema:** [map-content.v1.schema.json](../../schemas/map-content.v1.schema.json)

This wrapper preserves the existing MAP JSON v1 document unchanged inside its `map` field. It adds a `placements` array for reusable content instances.

Each placement contains:
- `instance_id`: unique non-empty ID within this map document.
- `content_id`: stable ID resolved against a ContentLibrary.
- `position`: finite world-space `x` and `y`.

The library reference is validated by `MapContentDocument.validate_references(library)` and before adding a placement through the domain API. Duplicate instance IDs, malformed positions, unknown fields, duplicate JSON keys, non-finite JSON constants and unsupported versions are rejected.

Placements are immutable records. Adding, updating and removing a placement returns a new MapContentDocument; it never mutates the original. A changed content reference must resolve against the supplied library.

No rotation or scale fields exist in v1. The runtime map schema and runtime snapshot schema remain unchanged.
