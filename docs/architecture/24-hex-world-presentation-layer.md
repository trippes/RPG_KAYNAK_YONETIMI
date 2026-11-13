# Eldoria — Hex World Presentation Layer

## Purpose

Stage 5 separates the Pygame presentation of the axial hex world from the existing world runtime. It does not replace axial coordinates, map definitions, pathfinding, occupancy, movement rules, or map-transition contracts.

## Presentation components

- `game_ui/world_transform.py`: axial-to-world, world-to-screen, screen-to-world, and screen-to-axial conversions. Camera offset and zoom are presentation state.
- `game_ui/world_rendering/terrain_renderer.py`: deterministic layered terrain cells and viewport visibility checks.
- `game_ui/world_rendering/depth_sorter.py`: stable back-to-front ordering by axial row and column.
- `game_ui/assets/asset_manager.py`: lazy image loading and caching.
- `game_ui/assets/sprite_sheet.py`: sprite-sheet frame extraction.
- `game_ui/assets/animation.py`: time-based frame progression.
- `game_ui/hex_world_view.py`: composition of runtime state and presentation adapters.

## Runtime boundary

The runtime continues to own discrete cell movement and authoritative entity positions. The view interpolates the rendered player marker along a resolved path; it does not introduce continuous world coordinates into domain state. The legacy square map remains a separate view and is not routed through the hex transform or renderer.

## Camera and input

- Mouse wheel adjusts hex-world zoom within a bounded range.
- The camera follows the rendered/interpolated player position at every zoom level.
- Camera follow is time-based and smooth; mouse edge scrolling temporarily enables free-look and leaving the edge resumes player follow.
- The world viewport uses the full game surface and keeps a stable hex scale instead of shrinking the complete map to fit.
- Mouse selection first reverses the screen/camera/zoom transform and then resolves the nearest axial cell.
- Existing hex movement controls and authored map-boundary transitions remain runtime-driven.

## Validation

The stage adds unit coverage for coordinate round trips, camera/zoom transforms, terrain geometry and palette selection, depth ordering, sprite caching, sprite-sheet slicing, animation timing, viewport culling, and visual movement interpolation. The repository release verification workflow runs on Linux and Windows.

## Manual visual checks still required

Automated CI cannot assess artistic quality or actual display behavior. After pulling `demo_eldoria`, launch the game and verify: hex cell selection at default and zoomed views; camera follow while zoomed; wheel zoom bounds; smooth path movement; terrain/river/landmark layering; boundary transitions; and return to the unchanged square map.

## Scope note

This stage establishes a 2D Pygame presentation architecture with layered depth cues and camera transforms. It does not claim full 3D geometry, true height-field terrain, or a complete hand-authored sprite environment. Those are separate art/content production decisions.
