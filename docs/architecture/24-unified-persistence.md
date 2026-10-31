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
then replaces the target with `os.replace()`. A failure before replacement
leaves the previous target file in place. The adapter does not provide a lock
or concurrent-writer ordering guarantee.

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
