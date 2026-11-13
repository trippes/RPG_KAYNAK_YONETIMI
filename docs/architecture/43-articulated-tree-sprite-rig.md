# Eldoria — Articulated Tree Sprite Rig

## Scope

This increment connects the extracted transparent tree-atlas components to the existing PNG-independent `TreeSkeleton`. It is limited to the presentation layer on `demo_eldoria`; hex movement, occupancy, pathfinding, map transitions, save data, square maps, and UI windows remain unchanged.

## Runtime flow

1. `TreePartsAtlas` loads the atlas and validates each component rectangle.
2. The atlas manifest provides ordered `rig_layers`. Each layer names a component, normalized tree-space anchor, normalized sprite pivot, normalized rendered size, and optional motion binding.
3. `TreeRigRenderer` scales and caches component surfaces, places each pivot at its authored anchor, and applies the current skeleton pose.
4. Trunk and branch layers rotate around their attachment pivots using the animated skeleton segment angle. Foliage layers follow their bound leaf-cluster anchor and receive a small independent sway.
5. If the atlas or rig metadata is missing, the existing single-sprite scene-object renderer remains the fallback.

## Coordinate contract

- `anchor` is normalized against the tree's rendered bounds.
- `pivot` is normalized against the extracted component surface.
- `size` is normalized against the tree's rendered width and height.
- Motion bindings are `none`, `trunk`, `branch`, or `leaf`; branch/leaf bindings use the skeleton's stable indices.
- Layer `order` controls back-to-front composition.
- The whole tree continues to use the same ground anchor and depth reference as the previous scene-object renderer.

The atlas rig coordinates are initial composition values. They are data-driven so they can be tuned without changing renderer code. Final visual alignment and branch-to-pixel calibration still require an in-game screenshot at the target zoom levels.

## Validation

Automated tests cover atlas rig metadata validation, layer composition, fixed-root behavior, time-dependent foliage movement, and legacy fallback when rig metadata is absent.

Manual acceptance remains required for:
- correct branch/root/canopy alignment against the supplied atlas,
- no visible gaps between trunk and branch pivots,
- foliage overlap and front/back layering,
- subtle wind motion at normal and zoomed camera scales,
- depth sorting against the player and other environmental objects.

## Deliberate non-goals

This increment does not add sub-cell tree collision, cutout deformation of the original single PNG, leaf particle simulation, or the Content Editor. Those systems remain separate.
