# NPC Physics Stage 1 — Four Acceptance Follow-ups

**Branch:** `experiment/map-cleanup`  
**Scope:** Runtime rollback, save restoration, map transfer, and disabled-body semantics  
**Schema compatibility:** `rpg-actors` v1 and `rpg-hex-world` v2 remain unchanged.

## 1. Runtime update atomicity

Movement commits now update the broadphase entry before changing occupancy and authoritative continuous position. If occupancy rejects the move, the previous broadphase entry is restored. The shared commit path is used by cell movement, cross-cell continuous movement, and cross-map transfer. Same-cell continuous movement also updates the index before publishing the new position.

Tests added:
- failed index update leaves continuous position and occupancy unchanged;
- occupancy failure restores the previous broadphase entry;
- old broadphase membership is retained and the new one is absent after failure.

## 2. Collider reconstruction during save restoration

Collider data remains content-owned and is not serialized. `HexWorldSnapshot.restore_into` now requires the restored NPC registry whenever the snapshot contains NPCs. It reconstructs local collider AABBs from each NPC's immutable `PhysicsBodyDefinition`, and restores its `enabled` participation flag. Missing NPC content fails explicitly and the restore rollback clears partial registrations.

The application load path passes `candidate.social.npcs` into restore. This preserves the existing save schema and avoids silently restoring NPCs as point-only spatial entries.

Tests added:
- restored NPC uses the content collider AABB;
- missing NPC content rejects restore without partial state;
- restoring a snapshot with NPCs but without an NPC registry is rejected;
- disabled body participation is retained through restore.

## 3. Cross-map collider lifecycle

All runtime relocation paths share the transactional spatial commit helper. A transfer updates the map-scoped broadphase entry, removes the old map membership, and publishes the new continuous position only after occupancy accepts the transfer.

Test added:
- after transfer, the NPC is absent from the source map query and its collider AABB is queryable only at the destination map and expected bounds.

## 4. Disabled physics body semantics

An NPC with `PhysicsBodyDefinition.enabled == False` remains a registered world actor and occupancy participant, and may still use the movement runtime. It is excluded from physical broadphase candidate results. The flag is carried through the NPC binding and save restoration paths.

Tests added:
- disabled NPC remains spatially registered and movable but is omitted from broadphase queries;
- disabled participation survives save restoration.

## Files changed

- `application/hex_world_runtime.py`
- `application/hex_actor_binding.py`
- `application/npc_hex_binding.py`
- `application/hex_world_persistence.py`
- `application/game_application.py`
- `tests/test_application/test_hex_world_runtime.py`
- `tests/test_application/test_npc_hex_binding.py`
- `tests/test_application/test_hex_world_persistence.py`

## Verification status

The regression tests have been added to the existing test suite. GitHub Actions is configured to run on pushes to `experiment/map-cleanup`. The connected GitHub status endpoint did not return workflow/check-run records for the latest push during this review, so this report does not claim that CI or Ruff passed. The latest workflow result must be checked before marking the four follow-ups fully verified.

No changes were made to `main`.
