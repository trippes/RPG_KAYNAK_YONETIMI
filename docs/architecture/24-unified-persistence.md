# Unified Application Persistence

## Scope

The application-level save format combines the existing Core persistence
document and the gameplay snapshot without changing either inner schema.

The outer document is:

- `schema`: `rpg-game-save`
- `schema_version`: `1`
- `core`: a `PersistenceDocument` using `rpg-core`
- `gameplay`: a `GameplaySnapshot` using `rpg-gameplay`

The outer document requires equal Core and gameplay simulation ticks. Core and
gameplay versions remain independently validated by their existing contracts.

## Save flow

`GameApplication.save(path)` reads `holder.current` once and builds both
snapshots from that same `SessionBundle`:

1. `CanonicalSessionState.from_session(bundle.session)` creates the Core state.
2. `PersistenceDocument.from_state(...)` creates the Core document.
3. `GameplaySnapshot.from_runtime(...)` receives the bundle inventory,
   resource-node, production-job and recipe registries.
4. `GameSaveDocument` validates the two ticks.
5. `GameSaveFileAdapter.save(...)` writes the outer document.

The adapter writes a same-directory temporary file, flushes and fsyncs it,
then validates the staged document before replacing the target with
`os.replace()`. When the current target is valid, it first creates a validated
backup through its own temporary file and atomic replacement. A corrupt primary
never overwrites an existing backup. On load, an invalid or missing primary
falls back to a valid `.bak` file and attempts to repair the primary atomically.
  Unsupported future schema versions are surfaced directly and never replaced
  by an older backup.
The adapter does not provide a lock or concurrent-writer ordering guarantee.

## Save-slot lifecycle and overwrite protection

The user-facing save manager exposes exactly ten slots. A slot is considered
occupied when either its primary `slot_N.json` file or its recoverable
`.bak` file exists. This prevents a backup-only slot from being presented as
empty or accidentally selected as a new game. Continue/latest-save discovery
also resolves backup-only slots through the primary path, allowing the file
adapter to perform its normal backup recovery.

Every manual save entry point, including the save shortcut, opens the slot
picker. Selecting an occupied slot opens an explicit overwrite confirmation.
The screen records the primary/backup file identities and metadata when the
prompt is shown, then checks them again on confirmation. If the slot changes,
the player must review and confirm the new state; if it disappears, the stale
confirmation is cancelled. The actual write still goes through the atomic file
adapter, which preserves a validated previous primary as `.bak`.

Deleting a slot requires confirmation and removes both the primary and backup.
The primary is removed first; if backup removal fails, the backup remains
available for recovery and the UI reports the deletion error. Empty slots can
be selected for a new save without an overwrite prompt.

## Load and candidate publication

`GameApplication.load(path)` never restores into `holder.current`:

1. The outer document is read and validated.
2. A new `GameSession` is created.
3. Core `RestoreContract.prepare()` and `activate_restore()` run on that
   candidate session.
4. Gameplay restore uses `candidate_session.simulation`.
5. Resource-node world IDs are checked against candidate Core worlds.
6. A candidate `SessionBundle` is built and validated.
7. Only then is `SessionHolder.publish(candidate)` called.

Any failure before publication leaves the previous bundle, session, runtime and
gameplay objects active. Gameplay restore does not create a second runtime in
this path.

## Error contract

- Missing or unreadable files produce `SaveFileReadError`.
- Malformed outer JSON produces `SaveDocumentError`.
- Unsupported outer schema versions produce `UnsupportedSaveSchemaError`.
- Core schema/state failures use the existing Core persistence exceptions.
- Gameplay schema/state failures use `GameplayPersistenceError`.
- Candidate world/reference failures use application validation errors.
- Atomic write failures produce `SaveFileWriteError`.
- If both the primary save and its backup are invalid or unreadable, loading
  produces `SaveFileReadError`; a valid backup is loaded and used to repair
  the primary when possible.

Errors are propagated to the caller; they are not converted into successful
save/load results.

## Persistence boundaries

The unified document covers Core session state and gameplay bundle state. It
does not include:

- legacy `ActionManager` state,
- legacy event queues,
- `GameApplication.state` / `GameState`,
- legacy action timing,
- automatic resource-node regeneration during load.

The legacy objects remain application-owned when a bundle is published. This
is an explicit scope boundary, not a claim that legacy state is restored.

## Tests

Persistence-related verification includes:

- unified document and deterministic codec tests,
- atomic adapter failure tests,
- candidate restore and publication tests,
- Core persistence/restore tests,
- resources persistence and gameplay integration tests,
- full `python -m unittest` regression coverage,
- `python main.py` smoke verification.

No Core file or Core persistence schema is changed by the application-level
unified persistence implementation.
