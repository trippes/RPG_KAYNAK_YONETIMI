# Content Library JSON Schema v1

**Kind:** `eldoria_content_library`  
**Version:** `schema_version: 1`  \n**Machine-readable schema:** [content-library.v1.schema.json](../../schemas/content-library.v1.schema.json)

The document is UTF-8 JSON with deterministic key ordering and a final newline. Duplicate object keys, NaN/Infinity, unknown fields, unsupported versions, duplicate content/layer/element IDs, invalid palette references and malformed geometry are rejected.

Top-level fields:

- `schema_version`: integer, exactly `1`.
- `kind`: exactly `eldoria_content_library`.
- `library_id`: non-empty stable string.
- `definitions`: array of reusable content definitions.

Each definition contains `content_id`, `name`, `category` (`environmental_object` or `structure`), `visual_document`, `collider` (null or explicit tagged collider), and JSON-compatible `metadata`.

A VisualDocument contains version 1, positive logical dimensions, normalized ground/depth anchors, an RGBA/RGB palette token table, ordered layers and stable drawing elements. Supported element types are polygon, ellipse, circle and polyline. Each element references palette tokens through its fill/stroke style. Generator provenance is optional JSON data.

Collider variants are explicit:
- Circle: `{"type":"circle","center":[x,y],"radius":r}`
- Convex polygon: `{"type":"convex_polygon","vertices":[[x,y],...]}`

Visual geometry never creates or changes collider geometry. A missing collider is valid.

Rotation and scale are not part of v1. Unsupported schema/document versions fail explicitly; automatic migration is not performed.
