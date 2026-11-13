# Eldoria — Tree Skeleton Contract

## Purpose
A tree is represented by two independent parts:
- **Skeleton:** stable world geometry and articulation data for anchoring, collision, depth ordering, branches and foliage animation.
- **Artwork:** a replaceable visual skin. PNG dimensions and transparency must not define physical behavior or branch structure.

Changing the PNG must not require changing movement, collision or animation data.

## Skeleton-space geometry
The articulated skeleton uses its own normalized local coordinate space (0–1), independent of the PNG:
- `TreeBranch.start` and `TreeBranch.end`: branch segment endpoints.
- `TreeBranch.parent_index`: optional parent branch, allowing a branch hierarchy.
- `TreeBranch.thickness`: relative branch thickness.
- `TreeBranch.sway_weight` and `phase`: per-branch wind response and phase offset.
- `TreeLeafCluster.anchor`: foliage cluster position.
- `TreeLeafCluster.radius`: relative foliage cluster size.
- `TreeLeafCluster.branch_index`: optional branch attachment.
- `TreeLeafCluster.sway_weight` and `phase`: independent leaf motion response.
- `TreeSkeleton.trunk`: independent trunk segment with a fixed ground root and restrained top sway.
- `TreeSkeleton.wind_response` and `sway_frequency`: global animation controls.
- `animated_trunk_points(time)`, `animated_branch_points(index, time)` and `animated_leaf_anchor(index, time)`: deterministic local-space poses. Child branches inherit parent endpoint motion; foliage follows its attached branch and adds its own sway.

These values describe the tree itself, not pixels in a particular image. The renderer will map the skeleton coordinate space to the selected visual asset.

## World and collision geometry
- `ground_anchor`: point that attaches the tree to the world.
- `depth_anchor`: point used for front/behind ordering.
- `trunk_collision`: legacy normalized rectangle used by the current artwork adapter; the long-term collision authority is the independent world-space collider model.
- `canopy_bounds`: foliage envelope reserved for debug and editor visualization.

The current sprite placement helpers still use normalized artwork anchors as an adapter for the existing PNG renderer. This does not make branch, foliage or future collision geometry dependent on PNG pixels.

## Initial articulated tree
The default skeleton contains a trunk, four branch segments and five leaf clusters. The branch hierarchy is constrained to earlier parent segments, preventing forward references and cycles. The F3 developer overlay now draws the trunk, animated branch poses and independently swaying foliage markers. The current PNG remains a single static image: these pose calculations and guides establish the animation rig, but do not deform or split the artwork itself. Actual visible leaf/branch motion in normal gameplay requires layered or segmented art assets.

## Developer visualization
Press **F3** in the hex-world view to display developer guides: red trunk collision rectangle, blue canopy bounds, yellow depth line, white ground anchor, brown trunk segment, orange branch hierarchy and green foliage-cluster markers. Branch and foliage guides move according to the deterministic wind pose.

## Separation of responsibilities
- Artwork: appearance, transparency, silhouette and artistic detail.
- Skeleton: branch hierarchy, foliage attachment, animation response, anchors and depth metadata.
- World simulation: movement and collision resolution.
- Renderer: mapping skeleton coordinates to visuals, animation and draw order.

The current hex simulation still resolves movement through its existing cell occupancy rules and does not yet perform precise world-space trunk collision.
