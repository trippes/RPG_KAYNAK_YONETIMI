import unittest

from locks import (
    ForceProfile, KeyDefinition, LockDefinition, LockInstance,
    LockManager, LockManagerError, LockpickProfile,
)


class TestLockDomain(unittest.TestCase):
    def setUp(self):
        self.manager = LockManager(
            lockpick_profiles=(LockpickProfile("iron_pick", ("lockpick",), True, True, 3),),
            force_profiles=(ForceProfile("wood_force", True, 5, ("axe",), "break"),),
        )
        self.manager.register_lock_definition(LockDefinition(
            "wood_chest_lock", "Wood chest lock", "wood_key",
            "iron_pick", "wood_force",
        ))
        self.manager.register_lock_definition(LockDefinition("iron_door_lock", "Iron door lock"))
        self.manager.register_key_definition(KeyDefinition("wood_key", "Wood key", "wood_chest_lock"))
        self.manager.register_key_definition(KeyDefinition("iron_key", "Iron key", "iron_door_lock"))
        self.manager.register(LockInstance("lock_01", "entity_chest", "wood_chest_lock"))

    def test_matching_key_unlocks_and_key_is_reusable(self):
        self.assertTrue(self.manager.unlock_with_key("lock_01", "wood_key"))
        self.assertFalse(self.manager.get("lock_01").locked)
        self.manager.register(LockInstance("lock_02", "entity_chest_2", "wood_chest_lock"))
        self.assertTrue(self.manager.unlock_with_key("lock_02", "wood_key"))

    def test_wrong_key_does_not_mutate_lock(self):
        self.assertFalse(self.manager.unlock_with_key("lock_01", "iron_key"))
        self.assertTrue(self.manager.get("lock_01").locked)

    def test_key_requires_inventory_availability(self):
        self.assertFalse(self.manager.unlock_with_key("lock_01", "wood_key", key_available=False))
        self.assertTrue(self.manager.get("lock_01").locked)

    def test_owner_bound_key_requires_matching_owner(self):
        self.manager.register_lock_definition(LockDefinition("owner_lock", "Owner lock", "owner_key"))
        self.manager.register_key_definition(KeyDefinition("owner_key", "Owner key", "owner_lock", True))
        self.manager.register(LockInstance("owner_lock_01", "entity_owner_chest", "owner_lock"))
        self.manager.bind_key_owner("owner_key", "actor_1")
        self.assertFalse(self.manager.unlock_with_key("owner_lock_01", "owner_key", "actor_2"))
        self.assertTrue(self.manager.get("owner_lock_01").locked)
        self.assertTrue(self.manager.unlock_with_key("owner_lock_01", "owner_key", "actor_1"))

    def test_lockpick_requires_skill_and_tool(self):
        self.assertFalse(self.manager.attempt_lockpick("lock_01", skill=5, tool_tags=(), success=True))
        self.assertFalse(self.manager.attempt_lockpick("lock_01", skill=2, tool_tags=("lockpick",), success=True))
        self.assertTrue(self.manager.attempt_lockpick("lock_01", skill=5, tool_tags=("lockpick",), success=True))

    def test_failed_lockpick_does_not_mutate(self):
        self.assertFalse(self.manager.attempt_lockpick("lock_01", skill=5, tool_tags=("lockpick",), success=False))
        self.assertTrue(self.manager.get("lock_01").locked)

    def test_force_requires_profile_strength_and_tool(self):
        self.assertFalse(self.manager.attempt_force("lock_01", strength=9, tool_tags=("hammer",), success=True))
        self.assertFalse(self.manager.attempt_force("lock_01", strength=4, tool_tags=("axe",), success=True))
        self.assertTrue(self.manager.attempt_force("lock_01", strength=9, tool_tags=("axe",), success=True))
        lock = self.manager.get("lock_01")
        self.assertTrue(lock.broken)
        self.assertFalse(lock.locked)

    def test_lock_without_force_profile_cannot_be_forced(self):
        self.manager.register(LockInstance("door_lock", "entity_door", "iron_door_lock"))
        self.assertFalse(self.manager.attempt_force("door_lock", strength=99, success=True))

    def test_broken_or_jammed_lock_rejects_normal_opening(self):
        lock = self.manager.get("lock_01")
        lock.broken = True
        lock.locked = False
        with self.assertRaises(LockManagerError):
            self.manager.unlock_with_key("lock_01", "wood_key")

    def test_duplicate_entity_lock_capability_is_rejected(self):
        with self.assertRaises(LockManagerError):
            self.manager.register(LockInstance("second", "entity_chest", "wood_chest_lock"))

    def test_owner_binding_rejects_ordinary_keys(self):
        with self.assertRaises(LockManagerError):
            self.manager.bind_key_owner("wood_key", "actor_1")

    def test_invalid_profile_and_state_are_rejected(self):
        with self.assertRaises(ValueError):
            LockpickProfile("invalid", (), False, False)
        with self.assertRaises(ValueError):
            LockInstance("bad", "entity_bad", "wood_chest_lock", locked=True, broken=True)


if __name__ == "__main__":
    unittest.main()
