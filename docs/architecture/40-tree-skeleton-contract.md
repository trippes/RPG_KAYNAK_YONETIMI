# Eldoria — Tree Skeleton Contract

## Purpose
A tree is represented by two independent parts:
- **Skeleton:** stable world geometry used for anchoring, depth ordering, and trunk collision.
- **Artwork:** a replaceable transparent PNG rendered over the skeleton's ground anchor.

Changing the PNG must not require changing movement or collision code.

## Geometry
The initial implementation is in `game_ui/world_rendering/tree_skeleton.py`.

- `ground_anchor`: normalized point that attaches the tree to the world.
- `depth_anchor`: normalized point used to compare the tree with the player's ground-contact depth.
- `trunk_collision`: normalized rectangle around the trunk; it does not include the canopy.
- `canopy_bounds`: normalized foliage region, reserved for editor/debug visualization and future canopy behavior.

All normalized values are relative to the PNG rectangle. Geometry is scaled with the image, while the world anchor remains stable.

## Initial default
The default skeleton uses a bottom-center ground anchor, a depth line slightly above the bottom edge, a narrow trunk collision rectangle, and a larger canopy region. Individual tree definitions can override these values when their silhouette requires it.

## Separation of responsibilities
- PNG: appearance, transparency, silhouette and artistic detail.
- Skeleton: anchor, depth reference, trunk collision and canopy bounds.
- World simulation: movement and collision resolution.
- Renderer: sprite scaling, placement and draw order.

The first commit establishes and tests the reusable geometry model. Wiring the skeleton into the live scene-object rendering/depth pipeline and exposing its guides in a developer view are subsequent integration tasks; this document does not claim those tasks are complete.
