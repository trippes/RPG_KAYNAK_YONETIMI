import unittest

from application import (
    GameSaveDocument, LockPersistenceError, LockSnapshot, SaveJsonCodec,
)
from core.application import GameSession
from core.persistence import CanonicalSessionState, PersistenceDocument
from locks import (
    ForceProfile, KeyDefinition, LockDefinition, LockInstance,
    LockManager, LockpickProfile,
)
from resources import GameplaySnapshot, ProductionJobManager, WorldResourceNodeManager


class TestLockPersistence(unittest.TestCase):
    def _manager(self):
        manager = LockManager(
            lockpick_profiles=(LockpickProfile(
                "fine_pick", ("lockpick",), True, True, 4,
            ),),
            force_profiles=(ForceProfile(
                "wood_force", True, 6, ("axe",), "break",
            ),),
        )
        manager.register_lock_definition(LockDefinition(
            "vault_lock", "Vault lock", "vault_key", "fine_pick", "wood_force",
        ))
        manager.register_key_definition(KeyDefinition(
            "vault_key", "Vault key", "vault_lock", True,
        ))
        manager.register(LockInstance(
            "vault_lock_01", "vault_entity", "vault_lock",
            locked=False, broken=True,
        ))
        manager.bind_key_owner("vault_key", "actor_01")
        return manager

    def test_snapshot_round_trip_preserves_profiles_keys_instances_and_ownership(self):
        snapshot = LockSnapshot.from_runtime(self._manager())
        restored = LockSnapshot.from_dict(snapshot.to_dict()).restore()

        self.assertEqual(restored.lock_definitions()[0].definition_id, "vault_lock")
        self.assertEqual(restored.key_definitions()[0].key_id, "vault_key")
        self.assertEqual(restored.lockpick_profiles()[0].minimum_skill, 4)
        self.assertEqual(restored.force_profiles()[0].success_effect, "break")
        self.assertEqual(restored.instances()[0].entity_id, "vault_entity")
        self.assertTrue(restored.instances()[0].broken)
        self.assertEqual(restored.owner_bindings(), (("vault_key", "actor_01"),))

    def test_snapshot_rejects_unknown_definition_reference(self):
        data = LockSnapshot.from_runtime(self._manager()).to_dict()
        data["instances"][0]["definition_id"] = "missing"
        with self.assertRaises(LockPersistenceError):
            LockSnapshot.from_dict(data)

    def test_snapshot_rejects_key_that_does_not_match_exact_lock(self):
        data = LockSnapshot.from_runtime(self._manager()).to_dict()
        data["keys"][0]["lock_definition_id"] = "other_lock"
        with self.assertRaises(LockPersistenceError):
            LockSnapshot.from_dict(data)

    def test_outer_save_document_round_trips_optional_lock_section(self):
        session = GameSession()
        core = PersistenceDocument.from_state(CanonicalSessionState.from_session(session))
        gameplay = GameplaySnapshot.from_runtime(
            {}, WorldResourceNodeManager(), ProductionJobManager(session.simulation),
        )
        snapshot = LockSnapshot.from_runtime(self._manager())
        document = GameSaveDocument(core=core, gameplay=gameplay, locks=snapshot)

        encoded = SaveJsonCodec.encode(document)
        decoded = SaveJsonCodec.decode(encoded)

        self.assertEqual(decoded.schema_version, 2)
        self.assertEqual(decoded.locks.to_dict(), snapshot.to_dict())
        self.assertEqual(SaveJsonCodec.encode(decoded), encoded)

    def test_legacy_save_without_lock_section_remains_valid(self):
        session = GameSession()
        core = PersistenceDocument.from_state(CanonicalSessionState.from_session(session))
        gameplay = GameplaySnapshot.from_runtime(
            {}, WorldResourceNodeManager(), ProductionJobManager(session.simulation),
        )
        document = GameSaveDocument(core=core, gameplay=gameplay)
        decoded = SaveJsonCodec.decode(SaveJsonCodec.encode(document))
        self.assertIsNone(decoded.locks)


if __name__ == "__main__":
    unittest.main()
