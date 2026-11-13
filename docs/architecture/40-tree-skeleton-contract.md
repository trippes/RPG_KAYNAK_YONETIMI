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
The current oak PNG uses a ground anchor at `(0.50, 0.985)`, a depth reference at `(0.50, 0.955)`, a trunk collision rectangle `(0.39, 0.82, 0.22, 0.16)`, and canopy bounds `(0.03, 0.02, 0.94, 0.76)`. These are normalized to the 949×936 artwork and are initial calibration values, not universal values for every tree silhouette. Individual tree definitions can override them when their silhouette requires it.

## Separation of responsibilities
- PNG: appearance, transparency, silhouette and artistic detail.
- Skeleton: anchor, depth reference, trunk collision and canopy bounds.
- World simulation: movement and collision resolution.
- Renderer: sprite scaling, placement and draw order.

The skeleton is now used by the live tree sprite renderer for ground anchoring and depth sorting. Press **F3** in the hex-world view to display developer guides: red trunk collision rectangle, blue canopy bounds, yellow depth line, and white ground anchor. The collision rectangle is currently presentation/debug metadata; the hex simulation still resolves movement through its existing cell occupancy rules and does not yet perform pixel-level trunk collision.
