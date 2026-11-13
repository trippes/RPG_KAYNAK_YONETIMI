# Eldoria — Pygame Hex Presentation System (Stage 6)

## Scope and boundary

Stage 6 extends the Stage 5 presentation adapters. Axial coordinates, map definitions, movement, collision, pathfinding, occupancy, transitions, and entity positions remain authoritative in the domain/runtime. Presentation metadata and interpolated positions never write back into runtime state. The legacy square-map renderer remains separate.

## Asset metadata

The Pygame-independent JSON catalog in game_ui/assets/asset_definition.py uses schema version 1 and an assets array. Records support asset_id, relative path, width, height, scale, normalized anchor, optional collision box, depth_offset, terrain_types, placement, interaction, spritesheet metadata, and animation metadata. Paths are resolved under the catalog directory and traversal is rejected. The starter package includes an empty presentation_assets.json catalog, so the format is immediately available to content authors. Its optional objects array places reusable asset IDs on a map and axial cell, with pixel offsets, multi-cell footprint, separate collision box, depth offset, layer, and kind (for example prop, flora, resource, or NPC). Missing files are reported by available() without crashing the game.

Example scene placement (the referenced asset must exist in the same catalog):

    {
      "object_id": "oak-west-01",
      "asset_id": "flora.oak",
      "map_id": "hex_forest_demo",
      "q": 2,
      "r": -1,
      "offset_x": 8,
      "offset_y": -4,
      "footprint": [2, 2],
      "collision_box": [28, 74, 32, 40],
      "depth_offset": 0,
      "layer": "ground",
      "kind": "flora"
    }

## Scene objects

SceneObject separates world anchor, visual dimensions, normalized ground anchor, multi-cell footprint, and optional collision box. SceneObjectRenderer draws cached images and culls by complete visual bounds, so tall objects remain visible even when their ground anchor is outside the viewport. Hex-world landmarks resolve an authored visual_type (or landmark.visual_type) asset ID and retain the existing marker fallback when no sprite is available. It does not own collision or placement decisions.

## Character animation

CharacterAnimator selects directional states idle, walk, run, attack, and interact from existing Animation objects. It is presentation-only. The existing procedural HexCharacterRenderer remains the fallback until authored PNG and spritesheet content is supplied.

## Terrain and depth

The terrain renderer accepts multiple ordered texture layers. The view selects base/detail textures by terrain compatibility and transition textures when their terrain_types are present among the cell and its six neighbors. The existing color and deterministic-detail renderer remains the safe fallback when image assets are absent. High-contrast cell outlines are intentionally omitted. Scene-object depth is based on the ground anchor plus a stable offset; authored canopy and underlay parts can be split into separate objects. Sorting and culling must not assume that a sprite fits inside one hex.

## Performance

Image loading remains delegated to the existing lazy AssetManager cache. Metadata is loaded once and does not perform image I/O during each frame. Culling occurs before scaling and blitting. Smooth scaling is skipped when source and target dimensions already match.

## Component inventory and data flow

The pre-existing presentation layer remains the foundation: HexWorldView composes WorldTransform, HexCamera, HexTerrainRenderer, HexCharacterRenderer, DepthSorter, AssetManager, SpriteSheet, and Animation. HexWorldRuntime and HexMapDefinition remain independent of Pygame. ContentPackage continues to own package/map loading; presentation_assets.json is an optional sidecar inside the active package and does not alter the gameplay schema.

At render time, the view transforms valid axial cells to screen centers, resolves compatible terrain textures from the cell plus its six neighbors, and draws terrain before map features. It then gathers landmarks, optional scene-object placements, and the player. Drawables are ordered by layer and screen-space ground depth with a stable axial/object key. Landmark and scene-object sprites are anchored to the ground point and culled by their complete visual bounds. The player sprite animation is selected from visual movement direction/state; if metadata or image decoding fails, the procedural humanoid remains active. Runtime movement and collision continue to be resolved before presentation interpolation.

## Stage 6 coverage

- 6.1: Existing presentation, camera, asset, map, and runtime components inventoried; the presentation/runtime boundary is retained.
- 6.2: Terrain palette fallback and optional PNG texture lookup are supported.
- 6.3: Multiple ordered textures and neighbor-compatible transition layers are supported; coordinate-seeded details remain deterministic.
- 6.4: Asset-backed landmarks and map-authored multi-cell scene objects support ground anchors, visual bounds, collision metadata, layers, and missing-art markers. The same placement schema can label props, flora, resources, and NPC visuals.
- 6.5: Procedural player fallback, PNG/spritesheet frames, eight directional metadata slots, and idle/walk/run/attack/interact animation states are supported. Only idle/walk are selected automatically by the current exploration view.
- 6.6: Stable screen-ground-depth sorting and underlay/ground/canopy/overlay layers are supported.
- 6.7: Existing follow, edge-scroll, zoom, and transform behavior are retained; texture resolution and scaled image surfaces are cached, and large sprites are culled by their full bounds.
- 6.8: Versioned asset and placement metadata is available to future content-authoring tools.
- 6.9: Unit and release verification run through the existing Linux and Windows workflow.

## Content and visual validation boundary

The starter presentation_assets.json intentionally contains empty assets and objects arrays. The repository does not currently provide a complete authored terrain, vegetation, building, resource, or player sprite pack. Consequently, CI verifies rendering contracts and fallbacks, not the artistic quality of a finished environment. A game-window visual pass is still required on the target PC after suitable art is authored. This work does not claim that such a manual visual pass has been performed.

## Verification and limitations

Stage 6 tests cover catalog validation, path traversal rejection, missing assets, multi-cell footprints, independent collision/visual bounds, full-sprite culling, and directional animation selection. Existing terrain, camera, transform, character, and runtime tests remain part of release verification. Automated tests cannot certify art quality or actual display behavior. No authored terrain, tree, building, or character sprite pack is claimed unless files are added to the content package.
