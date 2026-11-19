# Phase 16 — Player Physics and Movement Integration

Date: 2026-11-19

## Scope

Implemented on `experiment/map-cleanup` only. The approved player collider is a circle with radius **8 world units**. The axial map layout remains pointy-top with a 32-world-unit hex radius. No NPC body dimensions or static-object collider dimensions were inferred or introduced.

## Implementation

- `GameplayService.hex_actor_binding` now supplies a physics snapshot for the player's active local map and an explicit `BodyDefinition` for the player.
- Physics snapshots are cached by world ID, map ID, and the identity of the immutable map definition. A different map definition cannot accidentally reuse stale collision geometry.
- `ActorHexBindingService` supports an optional physics snapshot/body pair. Existing callers that have not spatially registered the player retain the previous no-physics binding behavior.
- Player keyboard movement and direct cell movement perform static-physics preflight before committing the existing authoritative hex occupancy.
- A* pathfinding accepts an edge validator. Player click-to-move now rejects candidate path edges that the player's collider cannot traverse; NPC and non-player pathfinding behavior remains unchanged.
- Physical collision rejection leaves the player's canonical position and occupancy unchanged.

## Tests and CI

Added tests for:
- configured player keyboard movement rejecting a physically blocked edge;
- configured player A* movement refusing a corridor with no physically valid route;
- requiring physics snapshot and player body configuration as a pair.

GitHub Actions run: [44540228897](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44540228897)

Both Linux and Windows jobs completed successfully:
- 2,273 tests passed on each platform;
- 235 subtests passed on each platform;
- Ruff checks passed;
- legacy map cleanup boundary passed;
- release-candidate verification passed.

## Explicitly deferred

- NPC collider metadata and NPC physical movement remain deferred; no NPC body size was approved.
- Static scenery/prop collider shapes and transforms remain deferred until explicit content metadata is authored. The snapshot currently includes collision geometry derived from the canonical map's blocked cells, non-walkable landmarks, and blocked map boundary.
- Resource-node interaction distance and gathering behavior are unchanged.
- Manual interactive Pygame acceptance on a graphical desktop has not yet been performed. CI is headless and does not replace that check.

## Branch safety

No merge was performed. `demo_eldoria`, `main`, and `experiment/hex-world-laboratory` were not targeted by these commits.
