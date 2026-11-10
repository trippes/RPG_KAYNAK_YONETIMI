"""Lock and key registries, ownership bindings and deterministic state transitions."""
from .definition import KeyDefinition, LockDefinition
from .instance import LockInstance
from .profiles import ForceProfile, LockpickProfile


class LockManagerError(ValueError):
    """A lock operation would violate a domain invariant."""


class LockManager:
    def __init__(self, lockpick_profiles=(), force_profiles=()):
        self._lock_definitions = {}
        self._key_definitions = {}
        self._instances = {}
        self._owner_bindings = {}
        self._lockpick_profiles = {}
        self._force_profiles = {}
        for profile in lockpick_profiles:
            self.register_lockpick_profile(profile)
        for profile in force_profiles:
            self.register_force_profile(profile)

    def register_lockpick_profile(self, profile):
        if not isinstance(profile, LockpickProfile):
            raise TypeError("profile must be LockpickProfile.")
        if profile.profile_id in self._lockpick_profiles:
            raise LockManagerError(f"Duplicate lockpick profile: {profile.profile_id}")
        self._lockpick_profiles[profile.profile_id] = profile
        return profile

    def register_force_profile(self, profile):
        if not isinstance(profile, ForceProfile):
            raise TypeError("profile must be ForceProfile.")
        if profile.profile_id in self._force_profiles:
            raise LockManagerError(f"Duplicate force profile: {profile.profile_id}")
        self._force_profiles[profile.profile_id] = profile
        return profile

    def register_lock_definition(self, definition):
        if not isinstance(definition, LockDefinition):
            raise TypeError("definition must be LockDefinition.")
        if definition.definition_id in self._lock_definitions:
            raise LockManagerError(f"Duplicate lock definition: {definition.definition_id}")
        if definition.lockpick_profile_id and definition.lockpick_profile_id not in self._lockpick_profiles:
            raise LockManagerError(f"Unknown lockpick profile: {definition.lockpick_profile_id}")
        if definition.force_profile_id and definition.force_profile_id not in self._force_profiles:
            raise LockManagerError(f"Unknown force profile: {definition.force_profile_id}")
        self._lock_definitions[definition.definition_id] = definition
        return definition

    def register_key_definition(self, definition):
        if not isinstance(definition, KeyDefinition):
            raise TypeError("definition must be KeyDefinition.")
        if definition.key_id in self._key_definitions:
            raise LockManagerError(f"Duplicate key definition: {definition.key_id}")
        if definition.lock_definition_id not in self._lock_definitions:
            raise LockManagerError(f"Unknown lock definition: {definition.lock_definition_id}")
        self._key_definitions[definition.key_id] = definition
        return definition

    def register(self, instance):
        if not isinstance(instance, LockInstance):
            raise TypeError("instance must be LockInstance.")
        if instance.lock_id in self._instances:
            raise LockManagerError(f"Duplicate lock instance: {instance.lock_id}")
        if instance.definition_id not in self._lock_definitions:
            raise LockManagerError(f"Unknown lock definition: {instance.definition_id}")
        if any(value.entity_id == instance.entity_id for value in self._instances.values()):
            raise LockManagerError(f"Entity already has a lock capability: {instance.entity_id}")
        self._instances[instance.lock_id] = instance
        return instance

    def get(self, lock_id):
        return self._instances.get(lock_id)

    def definition(self, definition_id):
        return self._lock_definitions.get(definition_id)

    def key_definition(self, key_id):
        return self._key_definitions.get(key_id)

    def instances(self):
        return tuple(self._instances[key] for key in sorted(self._instances))

    def bind_key_owner(self, key_id, actor_id):
        key = self._key_definitions.get(key_id)
        if key is None:
            raise KeyError(f"Key not found: {key_id}")
        if not key.owner_bound:
            raise LockManagerError("Only owner-bound keys can have an owner binding.")
        if not isinstance(actor_id, str) or not actor_id.strip():
            raise ValueError("actor_id must be a non-empty string.")
        self._owner_bindings[key_id] = actor_id

    def unlock_with_key(self, lock_id, key_id, actor_id=None, *, key_available=True):
        lock = self._require_locked(lock_id)
        definition = self._lock_definitions[lock.definition_id]
        key = self._key_definitions.get(key_id)
        if key is None or definition.required_key_id != key_id or key.lock_definition_id != definition.definition_id:
            return False
        if not key_available:
            return False
        if key.owner_bound and (actor_id is None or self._owner_bindings.get(key_id) != actor_id):
            return False
        lock.locked = False
        return True

    def attempt_lockpick(self, lock_id, *, skill, tool_tags=(), success=False):
        lock = self._require_locked(lock_id)
        definition = self._lock_definitions[lock.definition_id]
        profile = self._lockpick_profiles.get(definition.lockpick_profile_id)
        if profile is None:
            return False
        if isinstance(skill, bool) or not isinstance(skill, int) or skill < 0:
            raise ValueError("skill must be a non-negative integer.")
        tags = set(tool_tags)
        if profile.require_skill and skill < profile.minimum_skill:
            return False
        if profile.require_tool and not tags.intersection(profile.allowed_tool_tags):
            return False
        if not isinstance(success, bool):
            raise TypeError("success must be boolean.")
        if success:
            lock.locked = False
            return True
        return False

    def attempt_force(self, lock_id, *, strength, tool_tags=(), success=False):
        lock = self._require_locked(lock_id)
        definition = self._lock_definitions[lock.definition_id]
        profile = self._force_profiles.get(definition.force_profile_id)
        if profile is None or not profile.allowed:
            return False
        if isinstance(strength, bool) or not isinstance(strength, int) or strength < 0:
            raise ValueError("strength must be a non-negative integer.")
        if strength < profile.minimum_strength:
            return False
        if profile.required_tool_tags and not set(tool_tags).intersection(profile.required_tool_tags):
            return False
        if not isinstance(success, bool):
            raise TypeError("success must be boolean.")
        if not success:
            return False
        if profile.success_effect == "break":
            lock.broken = True
            lock.locked = False
        else:
            lock.locked = False
        return True

    def validate(self):
        for instance in self._instances.values():
            if instance.definition_id not in self._lock_definitions:
                raise LockManagerError("Lock instance references an unknown definition.")
        for key_id, actor_id in self._owner_bindings.items():
            key = self._key_definitions.get(key_id)
            if key is None or not key.owner_bound or not isinstance(actor_id, str) or not actor_id.strip():
                raise LockManagerError("Invalid owner-bound key reference.")
        return True

    def _require_locked(self, lock_id):
        lock = self._instances.get(lock_id)
        if lock is None:
            raise KeyError(f"Lock not found: {lock_id}")
        if lock.broken or lock.jammed:
            raise LockManagerError("Broken or jammed locks cannot be opened by this method.")
        if not lock.locked:
            raise LockManagerError("Lock is already unlocked.")
        return lock
