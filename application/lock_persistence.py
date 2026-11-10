"""Versioned persistence for lock definitions, keys and runtime lock state."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from locks import (
    ForceProfile, KeyDefinition, LockDefinition, LockInstance,
    LockManager, LockManagerError, LockpickProfile,
)

LOCK_SCHEMA = "rpg-locks"
LOCK_SCHEMA_VERSION = 1


class LockPersistenceError(ValueError):
    """Invalid lock snapshot or restore input."""


@dataclass(frozen=True)
class LockSnapshot:
    data: Mapping[str, object]

    @classmethod
    def from_runtime(cls, manager: LockManager):
        if not isinstance(manager, LockManager):
            raise TypeError("manager must be LockManager.")
        manager.validate()
        payload = {
            "schema": LOCK_SCHEMA,
            "schema_version": LOCK_SCHEMA_VERSION,
            "lockpick_profiles": [
                {
                    "profile_id": p.profile_id,
                    "allowed_tool_tags": list(p.allowed_tool_tags),
                    "require_skill": p.require_skill,
                    "require_tool": p.require_tool,
                    "minimum_skill": p.minimum_skill,
                }
                for p in manager.lockpick_profiles()
            ],
            "force_profiles": [
                {
                    "profile_id": p.profile_id,
                    "allowed": p.allowed,
                    "minimum_strength": p.minimum_strength,
                    "required_tool_tags": list(p.required_tool_tags),
                    "success_effect": p.success_effect,
                }
                for p in manager.force_profiles()
            ],
            "definitions": [
                {
                    "definition_id": d.definition_id,
                    "name": d.name,
                    "required_key_id": d.required_key_id,
                    "lockpick_profile_id": d.lockpick_profile_id,
                    "force_profile_id": d.force_profile_id,
                    "tags": list(d.tags),
                }
                for d in manager.lock_definitions()
            ],
            "keys": [
                {
                    "key_id": k.key_id,
                    "name": k.name,
                    "lock_definition_id": k.lock_definition_id,
                    "owner_bound": k.owner_bound,
                }
                for k in manager.key_definitions()
            ],
            "instances": [
                {
                    "lock_id": i.lock_id,
                    "entity_id": i.entity_id,
                    "definition_id": i.definition_id,
                    "locked": i.locked,
                    "jammed": i.jammed,
                    "broken": i.broken,
                }
                for i in manager.instances()
            ],
            "owner_bindings": [
                {"key_id": key_id, "actor_id": actor_id}
                for key_id, actor_id in manager.owner_bindings()
            ],
        }
        snapshot = cls(payload)
        snapshot._validate()
        return snapshot

    def to_dict(self):
        return _copy(dict(self.data))

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping):
            raise LockPersistenceError("Lock snapshot must be an object.")
        expected = {
            "schema", "schema_version", "lockpick_profiles", "force_profiles",
            "definitions", "keys", "instances", "owner_bindings",
        }
        if set(data) != expected:
            raise LockPersistenceError("Lock snapshot has missing or unknown fields.")
        if data.get("schema") != LOCK_SCHEMA or data.get("schema_version") != LOCK_SCHEMA_VERSION:
            raise LockPersistenceError("Unsupported lock persistence schema.")
        if any(not isinstance(data[key], list) for key in expected - {"schema", "schema_version"}):
            raise LockPersistenceError("Lock snapshot collections must be lists.")
        try:
            snapshot = cls(_copy(dict(data)))
            snapshot._validate()
            return snapshot
        except (KeyError, TypeError, ValueError) as error:
            if isinstance(error, LockPersistenceError):
                raise
            raise LockPersistenceError("Invalid lock snapshot record.") from error

    def _validate(self):
        _unique(self.data["lockpick_profiles"], "profile_id")
        _unique(self.data["force_profiles"], "profile_id")
        _unique(self.data["definitions"], "definition_id")
        _unique(self.data["keys"], "key_id")
        _unique(self.data["instances"], "lock_id")
        _unique(self.data["owner_bindings"], "key_id")
        if len({r.get("entity_id") for r in self.data["instances"]}) != len(self.data["instances"]):
            raise LockPersistenceError("A Core entity cannot have multiple lock capabilities.")

        lockpick_ids = {r["profile_id"] for r in self.data["lockpick_profiles"]}
        force_ids = {r["profile_id"] for r in self.data["force_profiles"]}
        definitions = {r["definition_id"]: r for r in self.data["definitions"]}
        keys = {r["key_id"]: r for r in self.data["keys"]}
        for definition in definitions.values():
            if definition.get("lockpick_profile_id") not in (None, *lockpick_ids):
                raise LockPersistenceError("Lock definition references an unknown lockpick profile.")
            if definition.get("force_profile_id") not in (None, *force_ids):
                raise LockPersistenceError("Lock definition references an unknown force profile.")
            key_id = definition.get("required_key_id")
            if key_id is not None and key_id not in keys:
                raise LockPersistenceError("Lock definition references an unknown required key.")
        for key_id, key in keys.items():
            definition = definitions.get(key.get("lock_definition_id"))
            if definition is None or definition.get("required_key_id") != key_id:
                raise LockPersistenceError("Key must match exactly one lock definition.")
            if not isinstance(key.get("owner_bound"), bool):
                raise LockPersistenceError("Key owner_bound must be boolean.")
        for instance in self.data["instances"]:
            if instance.get("definition_id") not in definitions:
                raise LockPersistenceError("Lock instance references an unknown definition.")
            for field in ("locked", "jammed", "broken"):
                if not isinstance(instance.get(field), bool):
                    raise LockPersistenceError(f"Lock instance {field} must be boolean.")
            if instance["jammed"] and instance["broken"]:
                raise LockPersistenceError("Lock cannot be both jammed and broken.")
            if (instance["jammed"] or instance["broken"]) and instance["locked"]:
                raise LockPersistenceError("Jammed or broken lock cannot remain locked.")
        for binding in self.data["owner_bindings"]:
            key = keys.get(binding.get("key_id"))
            actor_id = binding.get("actor_id")
            if key is None or not key.get("owner_bound") or not isinstance(actor_id, str) or not actor_id.strip():
                raise LockPersistenceError("Invalid owner-bound key binding.")

    def restore(self):
        self._validate()
        try:
            manager = LockManager(
                lockpick_profiles=(
                    LockpickProfile(
                        r["profile_id"], tuple(r.get("allowed_tool_tags", ())),
                        r.get("require_skill", True), r.get("require_tool", False),
                        r.get("minimum_skill", 0),
                    )
                    for r in self.data["lockpick_profiles"]
                ),
                force_profiles=(
                    ForceProfile(
                        r["profile_id"], r.get("allowed", True),
                        r.get("minimum_strength", 0),
                        tuple(r.get("required_tool_tags", ())),
                        r.get("success_effect", "unlock"),
                    )
                    for r in self.data["force_profiles"]
                ),
            )
            for r in self.data["definitions"]:
                manager.register_lock_definition(LockDefinition(
                    r["definition_id"], r["name"], r.get("required_key_id"),
                    r.get("lockpick_profile_id"), r.get("force_profile_id"),
                    tuple(r.get("tags", ())),
                ))
            for r in self.data["keys"]:
                manager.register_key_definition(KeyDefinition(
                    r["key_id"], r["name"], r["lock_definition_id"],
                    r.get("owner_bound", False),
                ))
            for r in self.data["instances"]:
                manager.register(LockInstance(
                    r["lock_id"], r["entity_id"], r["definition_id"],
                    r.get("locked", True), r.get("jammed", False), r.get("broken", False),
                ))
            for r in self.data["owner_bindings"]:
                manager.bind_key_owner(r["key_id"], r["actor_id"])
            manager.validate()
            return manager
        except (KeyError, TypeError, ValueError, LockManagerError) as error:
            if isinstance(error, LockPersistenceError):
                raise
            raise LockPersistenceError("Lock state could not be restored safely.") from error


def _unique(records, key):
    if any(not isinstance(record, Mapping) for record in records):
        raise LockPersistenceError("Snapshot collections must contain objects.")
    values = [record.get(key) for record in records]
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise LockPersistenceError(f"Invalid {key} values.")
    if len(values) != len(set(values)):
        raise LockPersistenceError(f"Duplicate {key} values.")


def _copy(value):
    if isinstance(value, Mapping):
        return {str(k): _copy(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_copy(v) for v in value]
    return value


__all__ = ["LOCK_SCHEMA", "LOCK_SCHEMA_VERSION", "LockPersistenceError", "LockSnapshot"]
