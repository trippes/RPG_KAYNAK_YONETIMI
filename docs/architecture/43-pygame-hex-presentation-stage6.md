# Eldoria — Pygame Hex Presentation System (Stage 6)

## Scope and boundary

Stage 6 extends the Stage 5 presentation adapters. Axial coordinates, map definitions, movement, collision, pathfinding, occupancy, transitions, and entity positions remain authoritative in the domain/runtime. Presentation metadata and interpolated positions never write back into runtime state. The legacy square-map renderer remains separate.

## Asset metadata

The Pygame-independent JSON catalog in game_ui/assets/asset_definition.py uses schema version 1 and an assets array. Records support asset_id, relative path, width, height, scale, normalized anchor, optional collision box, depth_offset, terrain_types, placement, interaction, spritesheet metadata, and animation metadata. Paths are resolved under the catalog directory and traversal is rejected. Missing files are reported by available() without crashing the game.

## Scene objects

SceneObject separates world anchor, visual dimensions, normalized ground anchor, multi-cell footprint, and optional collision box. SceneObjectRenderer draws cached images and culls by complete visual bounds, so tall objects remain visible even when their ground anchor is outside the viewport. It does not own collision or placement decisions.

## Character animation

CharacterAnimator selects directional states idle, walk, run, attack, and interact from existing Animation objects. It is presentation-only. The existing procedural HexCharacterRenderer remains the fallback until authored PNG and spritesheet content is supplied.

## Terrain and depth

The existing terrain renderer remains the safe fallback when image assets are absent. Scene-object depth is based on the ground anchor plus a stable offset; authored canopy and underlay parts can be split into separate objects. Sorting and culling must not assume that a sprite fits inside one hex.

## Performance

Image loading remains delegated to the existing lazy AssetManager cache. Metadata is loaded once and does not perform image I/O during each frame. Culling occurs before scaling and blitting. Smooth scaling is skipped when source and target dimensions already match.

## Verification and limitations

Stage 6 tests cover catalog validation, path traversal rejection, missing assets, multi-cell footprints, independent collision/visual bounds, full-sprite culling, and directional animation selection. Existing terrain, camera, transform, character, and runtime tests remain part of release verification. Automated tests cannot certify art quality or actual display behavior. No authored terrain, tree, building, or character sprite pack is claimed unless files are added to the content package.
