# Lock & Key Domain

## Status

Stage 6 architecture contract. This document defines the domain boundary and invariants before runtime implementation. All work is confined to `ui/location-based-dynamic-markets`; `main` remains independent and untouched.

## Goals

Provide one reusable, data-driven lock system for any lockable world entity: containers, doors, gates, chests, vaults, and future interactable objects. A lock is an independent capability attached to an entity; it is not a subclass of Container and does not own container durability or contents.

The domain must be deterministic, serializable, testable without Pygame, and independent of UI presentation.

## Domain model

### LockDefinition

Immutable content data describing one lock kind:

- `definition_id`: stable unique identifier.
- `name`: display name.
- `required_key_id`: one exact key definition identifier, or `None` for locks without a matching-key route.
- `lockpick_difficulty`: non-negative skill threshold / difficulty input.
- `lockpick_profile_id`: optional profile describing tool requirements and pick constraints.
- `force_profile_id`: optional profile describing whether and how this lock can be forced.
- Optional tags for content filtering and future editor validation.

A lock definition is not runtime state. Definitions are immutable and shared by instances.

### LockInstance

Runtime state for one uniquely identified lock attached to one existing Core Entity:

- `lock_id`: unique runtime identity.
- `entity_id`: the Core entity carrying the lock capability.
- `definition_id`: registered LockDefinition.
- `locked`: current lock state.
- `jammed` / `broken`: explicit terminal or obstructed states only where supported by the selected profile.

One Core Entity may have at most one LockInstance in this stage. The lock system must not change the entity's Core EntityType. Lock capability attachment is separate from Container capability attachment, so an entity may have both.

### KeyDefinition

Immutable content data:

- `key_id`: stable unique key identity.
- `name`: display name.
- `lock_definition_id`: exactly one lock definition this key can operate.
- Optional owner-binding policy metadata.

**Single-key matching rule:** a key definition matches exactly one lock definition. A lock definition names at most one required key. No wildcard, key-ring, master-key, or multi-lock matching behavior is introduced in this stage.

A key is not consumed merely by unlocking; ordinary key use is reusable. Consumption can only be added later as an explicit content rule, never inferred from the word “single”.

## Key ownership

Both ownership modes are supported:

1. Ordinary key: the key item is present in the acting character/NPC inventory.
2. Owner-bound key: the key is associated with a specific actor/character owner and is usable only by that owner. It may still be represented as an inventory item when the content setup requires physical possession.

The application boundary is responsible for resolving the actor, inventory, and owner identity. The lock domain must not reach into character or inventory repositories directly.

## Unlock methods

### Matching key

Unlock succeeds only when:
- the lock exists and is currently locked;
- the key exists and its `lock_definition_id` exactly matches the lock's definition;
- the key is available to the actor through ordinary inventory ownership or valid owner binding.

Wrong keys must not mutate state.

### Lockpicking

Both routes are supported:
- skill-based attempt using the actor's lockpicking skill value;
- tool-based attempt requiring an eligible lockpick tool/item.

A lockpick profile defines which tools qualify and any profile-specific constraints. If a profile requires both skill and a tool, both checks must pass. If it permits either route, either valid route may be used. The profile must state this explicitly; the manager must not silently guess.

Difficulty and any random/roll resolution are supplied to the domain as explicit inputs or by an injected deterministic resolver. The domain must not import UI, Pygame, global random state, or character progression systems.

Failed attempts do not unlock the lock. Any future damage, noise, time cost, or alert side effects belong to application/gameplay orchestration and must be explicit.

### Forced opening

Forced opening is profile-driven and optional per lock definition. A lock without a force profile cannot be forced.

A force profile defines:
- whether force is allowed;
- applicable actor attribute/skill threshold;
- optional required tool or weapon tags;
- durability/condition consequences, if any;
- whether success destroys, jams, or simply unlocks the lock.

No universal “force any lock” fallback is allowed. Container break profiles remain responsible for container structural durability; lock force profiles are responsible only for lock-specific consequences. The application service coordinates any combined consequence.

## State and invariants

- Definitions are immutable; instances are mutable runtime state.
- Runtime lock IDs and key IDs are unique within their respective registries.
- Entity references must resolve to existing Core entities at the application/persistence boundary.
- One entity has at most one lock capability in this stage.
- A key matches exactly one lock definition; no implicit master keys.
- Failed key, pick, or force attempts leave lock state unchanged unless an explicit profile consequence says otherwise.
- An unlocked lock cannot be unlocked again through a state-changing operation; idempotent query behavior is allowed.
- A broken or permanently jammed lock cannot be opened through ordinary key use or lockpicking.
- The lock manager owns domain state and invariants; GameplayService owns actor/inventory resolution and gameplay action costs.
- ContainerManager remains unaware of key possession and lockpicking rules. It may be queried by GameplayService when opening a locked container.

## Persistence

Use a dedicated versioned snapshot (proposed schema: `rpg-locks`, version 1) for lock definitions, key definitions, lock instances, ownership bindings, and runtime lock state. Restore must validate all references and reject duplicate IDs, unknown definitions, invalid state combinations, and orphaned entity references.

Do not bump the outer save schema merely to add an optional lock snapshot if the existing save document supports optional domain snapshots. If the save envelope requires a schema change, add an explicit backward-compatible migration and preserve old saves without lock data.

## Application integration

GameplayService is the public mutation boundary. Planned operations include:
- register lock/key definitions and lock instances;
- inspect lock state through immutable view objects;
- unlock with a matching key;
- attempt lockpicking with explicit actor skill and inventory/tool evidence;
- attempt forced opening through the selected force profile;
- open/inspect a container only after the lock gate permits it.

The service must validate the entity exists before attaching a lock. UI screens and widgets must never mutate LockManager directly.

## Implementation sequence and acceptance criteria

1. Domain primitives and profiles: immutable definitions, runtime instance, registry/manager, validation and state transitions.
2. Domain tests: exact key matching, duplicate/unknown references, key reuse, skill/tool routes, failed-attempt immutability, force profile allow/deny, broken/jammed states.
3. Application integration: entity attachment, actor/inventory checks, read-only views, action boundary, container lock gate.
4. Persistence: versioned snapshot, restore validation, optional-save compatibility and round-trip tests.
5. CI: full Linux and Windows test matrix plus release verification. Stage 6 is complete only after all required checks pass.

## Explicitly out of scope

- Pygame lock UI, animations, sound, and visual feedback.
- Content Editor screens and authoring workflows.
- Master keys, skeleton keys, key rings, multi-lock keys, consumable keys.
- Multiplayer ownership/permissions.
- Generic lock crafting or lock manufacturing.
