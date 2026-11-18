# Eldoria Content Data API — Phase 14

This API is the shared data foundation for the future **ELDORIA CONTENT EDITOR** desktop application and the game runtime. It is not an editor UI.

## Core documents

- `VisualDocument`: Pygame-independent vector artwork, palette tokens, stable element/layer IDs, anchors and optional generator provenance.
- `ContentDefinition`: reusable visual asset, category, metadata and optional explicit collider.
- `ContentLibrary`: immutable collection of definitions indexed by stable `content_id`.
- `ContentPlacement`: one map-local instance with a stable `instance_id`, content reference and world position.
- `MapContentDocument`: existing `HexMapDefinition` plus immutable placements.

The five established procedural profiles are available as editable vector sources:

```python
from hex_world_lab.rendering.procedural import build_builtin_content_library

library = build_builtin_content_library(seed=17)
tree = library.resolve("environment.tree")
```

The library factory is a rendering-side adapter. The content domain itself imports neither Pygame nor rendering modules.

## Editing content data without a GUI

```python
from hex_world_lab.content import ContentPlacement, MapContentDocument

document = MapContentDocument(map_definition)
document = document.add_placement(
    ContentPlacement("oak-instance-01", "environment.tree", 120.0, 84.0),
    library,
)
document = document.update_placement("oak-instance-01", x=140.0)
document = document.remove_placement("oak-instance-01")
```

Every operation returns a new immutable document. A changed content reference must resolve against the supplied library. No mouse input, map painting or desktop window is required.

## Persistence

```python
from hex_world_lab.content.persistence import (
    load_library_file, save_library_file,
    load_map_content_file, save_map_content_file,
)

save_library_file(library, "content-library.json", mode="create")
loaded_library = load_library_file("content-library.json")
save_map_content_file(document, "valley-content.json", mode="create")
loaded_document = load_map_content_file("valley-content.json")
loaded_document.validate_references(loaded_library)
```

Default save mode is `create`; replacing an existing file requires explicit `mode="replace"`. JSON is deterministic and strict: duplicate keys, NaN/Infinity, unknown fields and unsupported versions are rejected.

## Runtime adapters

- `render_visual_document` / `render_content_definition` convert vector documents to alpha Pygame Surfaces.
- `register_content_library_assets` registers the resulting surfaces under stable content IDs.
- `to_environment_scene` adapts map placements to the existing environmental object scene.
- `environment_sprite_visuals` and `environment_obstacles` remain the existing render/physics presentation APIs.

Collider data is independent of artwork. No collider is inferred from polygon bounds, alpha pixels or visible shapes. The five built-in profiles intentionally have no default collider in this data factory; collision must be authored explicitly.

## Version 1 limitations

- No placement rotation or scale.
- No raster editor, bezier editor, animation timeline or 3D model format.
- No desktop GUI or map-editing UI.
- No automatic migration from unknown schema versions.
- No main-game integration in Phase 14.
