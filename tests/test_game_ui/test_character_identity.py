import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from game_ui.input import InputState
from game_ui.screens.character_creation import CharacterCreationScreen
from game_ui.screens.character_screen import CharacterScreen
from game_ui.screens.dialogue_screen import DialogueScreen


class FakeCharacter:
    def __init__(self, name="Traveler"):
        self.name = name
        self.race = SimpleNamespace(race_id="human", name="Human")
        self.character_class = SimpleNamespace(class_id="fighter", name="Fighter")
        self.age = 25
        self.appearance = {}
        self.skills = SimpleNamespace(to_dict=lambda: {"sword": 1})
        self.progression = SimpleNamespace(
            level=1,
            experience=0,
            experience_to_next_level=100,
            unspent_points=1,
        )


class FakePlayerService:
    def __init__(self):
        self.player_actor_id = "traveler_actor"
        self.player_character_id = "traveler_character"
        self.character = FakeCharacter()
        self.actor_character_calls = []
        self.actor_stats_calls = []
        self.skill_calls = []
        self.customization_calls = []
        self.relationship_changes = []
        self._character_factory = None
        self._creation_from_eren = False
        self._player_name_confirmed = False
        self.application = SimpleNamespace(
            customize_character=self.customize_character,
            holder=SimpleNamespace(
                current=SimpleNamespace(
                    social=SimpleNamespace(
                        npcs=SimpleNamespace(
                            get=lambda npc_id: (
                                SimpleNamespace(npc_id=npc_id)
                                if npc_id == "warden_lyra"
                                else None
                            ),
                        ),
                    ),
                ),
            ),
        )

    @property
    def character_creation_from_dialogue(self):
        return self._creation_from_eren

    def character_creation_options(self):
        return (
            (SimpleNamespace(race_id="human", name="Human"),),
            (SimpleNamespace(class_id="fighter", name="Fighter"),),
        )

    def customize_player_character(self, name, age, attributes, **kwargs):
        self.customize_character(
            self.player_character_id, name, age, attributes, **kwargs,
        )
        self.change_relationship(self.player_actor_id, "warden_lyra", trust=1)
        from_dialogue = self._creation_from_eren
        self._player_name_confirmed = True
        self._creation_from_eren = False
        return from_dialogue

    def actor_character(self, actor_id):
        self.actor_character_calls.append(actor_id)
        return self.character if actor_id == self.player_actor_id else None

    def actor_stats(self, actor_id):
        self.actor_stats_calls.append(actor_id)
        return {"level": 1, "attributes": {}, "modifiers": {}}

    def improve_skill(self, actor_id, skill):
        self.skill_calls.append((actor_id, skill))
        return 2

    def customize_character(self, character_id, *args, **kwargs):
        self.customization_calls.append((character_id, args, kwargs))

    def change_relationship(self, source_id, target_id, value=0, trust=0):
        self.relationship_changes.append((source_id, target_id, value, trust))

    @property
    def player_name_confirmed(self):
        return self._player_name_confirmed

    def confirm_player_name(self):
        self._player_name_confirmed = True

    def begin_character_creation_from_dialogue(self):
        self._creation_from_eren = True

    def dialogue_npc_name(self, npc_id):
        npc = self.application.holder.current.social.npcs.get(npc_id)
        return getattr(npc, "name", None) if npc is not None else None

    def dialogue_session_for_npc(self, target_npc_id):
        bundle = self.application.holder.current
        actors = bundle.actors.actors()
        actor = next(
            (item for item in actors if item.actor_id == self.player_actor_id),
            None,
        )
        if actor is None:
            raise RuntimeError("Oyuncu aktörü etkin dünyada bulunamadı.")
        npcs = bundle.social.npcs.all()
        dialogue_ids = tuple(sorted(bundle.social.dialogues))
        if not npcs or not dialogue_ids:
            raise RuntimeError("Konuşulacak NPC veya diyalog bulunamadı.")
        npc = next((item for item in npcs if item.npc_id == target_npc_id), npcs[0])
        preferred = {
            "village_carpenter": "carpenter_dialogue",
            "caravan_merchant": "caravan_merchant_dialogue",
        }.get(npc.npc_id)
        dialogue_id = (
            preferred if preferred in bundle.social.dialogues
            else next(
                (item for item in dialogue_ids
                 if npc.npc_id in bundle.social.dialogues[item].speakers),
                dialogue_ids[0],
            )
        )
        return SimpleNamespace(
            actor_id=actor.actor_id,
            npc_id=npc.npc_id,
            npc_name=npc.name,
            dialogue_id=dialogue_id,
        )


class CharacterIdentityTests(unittest.TestCase):
    def setUp(self):
        self.service = FakePlayerService()

    def test_creation_resolves_character_through_player_actor_and_customizes_character_id(self):
        screen = CharacterCreationScreen(self.service)
        screen.name = "Traveler"
        screen.age = "25"
        screen.scores.update({
            screen.ATTRIBUTES[0][0]: 15,
            screen.ATTRIBUTES[1][0]: 15,
            screen.ATTRIBUTES[2][0]: 12,
        })

        result = screen._finish()

        self.assertEqual(result, "world")
        self.assertEqual(
            self.service.actor_character_calls,
            ["traveler_actor", "traveler_actor"],
        )
        self.assertEqual(
            self.service.customization_calls[0][0],
            "traveler_character",
        )

    def test_creation_persists_eren_recognition_for_normal_new_game(self):
        screen = CharacterCreationScreen(self.service)
        screen.name = "Traveler"
        screen.age = "25"
        screen.scores.update({
            screen.ATTRIBUTES[0][0]: 15,
            screen.ATTRIBUTES[1][0]: 15,
            screen.ATTRIBUTES[2][0]: 12,
        })

        result = screen._finish()

        self.assertEqual(result, "world")
        self.assertEqual(
            self.service.relationship_changes,
            [("traveler_actor", "warden_lyra", 0, 1)],
        )
        self.assertTrue(self.service._player_name_confirmed)
        self.assertFalse(self.service._creation_from_eren)

    def test_character_screen_reads_character_and_stats_by_player_actor_id(self):
        screen = CharacterScreen(self.service)

        self.assertIs(self.service.character, screen._character())
        self.assertEqual(screen._stats()["level"], 1)
        self.assertEqual(
            self.service.actor_character_calls,
            ["traveler_actor"],
        )
        self.assertEqual(self.service.actor_stats_calls, ["traveler_actor"])

    def test_character_screen_skill_upgrade_targets_player_actor(self):
        screen = CharacterScreen(self.service)

        screen.handle(InputState(actions={"confirm"}))

        self.assertEqual(
            self.service.skill_calls,
            [("traveler_actor", "sword")],
        )

    def test_character_screen_render_selects_player_actor_not_first_actor(self):
        npc = SimpleNamespace(actor_id="npc_guard")
        player = SimpleNamespace(actor_id="traveler_actor")
        self.service.state = Mock(
            return_value=SimpleNamespace(actors=(npc, player)),
        )
        screen = CharacterScreen(self.service)
        screen._layout = Mock(
            return_value={
                "outer": (0, 0, 100, 100),
                "identity": (0, 0, 10, 10),
                "combat": None,
                "attributes": (0, 0, 10, 10),
                "skills": (0, 0, 10, 10),
            },
        )
        screen._render_identity = Mock()
        screen._render_attributes = Mock()
        screen._render_skills = Mock()
        renderer = SimpleNamespace(
            pg=SimpleNamespace(
                Rect=lambda bounds: SimpleNamespace(
                    x=bounds[0],
                    y=bounds[1],
                ),
            ),
            panel=Mock(),
            text=Mock(),
        )

        screen.render(renderer)

        self.assertEqual(
            self.service.actor_character_calls,
            ["traveler_actor"],
        )
        self.assertEqual(self.service.actor_stats_calls, ["traveler_actor"])
        screen._render_identity.assert_called_once()
        identity_args = screen._render_identity.call_args.args
        self.assertIs(identity_args[1], self.service.character)
        self.assertEqual(identity_args[2]["level"], 1)
        self.assertEqual(identity_args[3], (0, 0, 10, 10))

    def test_dialogue_resume_resolves_character_through_player_actor(self):
        screen = DialogueScreen(self.service)

        screen.resume_after_creation()

        self.assertEqual(self.service.actor_character_calls, ["traveler_actor"])
        self.assertEqual(screen.character_name, "Traveler")
        self.assertEqual(screen.opening_stage, "ask_reason")

    def test_dialogue_name_confirmation_uses_player_actor_character(self):
        screen = DialogueScreen(self.service)
        screen.opening_stage = "dialogue"
        screen.context = ("traveler_actor", "warden_lyra", "warden_intro")
        screen.name_entry_active = True
        screen.character_name = "New Name"

        screen.handle(InputState(actions={"confirm"}))

        self.assertEqual(self.service.actor_character_calls, ["traveler_actor"])
        self.assertEqual(self.service.character.name, "New Name")
        self.assertEqual(screen.opening_stage, "ask_reason")
        self.assertEqual(
            self.service.relationship_changes,
            [("traveler_actor", "warden_lyra", 0, 1)],
        )

    def test_dialogue_uses_returning_node_after_npc_introduction(self):
        actor = SimpleNamespace(actor_id="traveler_actor")
        npc = SimpleNamespace(npc_id="warden_lyra", name="Eren")
        dialogue = SimpleNamespace(
            speakers=frozenset({"warden_lyra"}),
        )
        bundle = SimpleNamespace(
            actors=SimpleNamespace(actors=lambda: (actor,)),
            social=SimpleNamespace(
                npcs=SimpleNamespace(
                    all=lambda: (npc,),
                    get=lambda npc_id: npc if npc_id == "warden_lyra" else None,
                ),
                dialogues={"warden_intro": dialogue},
            ),
        )
        self.service.application.holder = SimpleNamespace(
            current=bundle,
        )
        self.service.relationship = Mock(
            return_value=SimpleNamespace(trust=1),
        )
        self.service.talk_to_npc = Mock(
            return_value=SimpleNamespace(
                node_id="returning", text="Tekrar hoş geldin.", choices=(),
            ),
        )
        screen = DialogueScreen(self.service)
        screen.set_target_npc("warden_lyra")

        screen._open_default()

        self.service.talk_to_npc.assert_called_once_with(
            "traveler_actor", "warden_lyra", "warden_intro",
            node_id="returning",
        )
        self.assertEqual(screen.node.node_id, "returning")
        self.assertEqual(screen.opening_stage, "dialogue")

    def test_dialogue_keeps_first_meeting_for_unknown_npc(self):
        actor = SimpleNamespace(actor_id="traveler_actor")
        npc = SimpleNamespace(npc_id="warden_lyra", name="Eren")
        dialogue = SimpleNamespace(speakers=frozenset({"warden_lyra"}))
        bundle = SimpleNamespace(
            actors=SimpleNamespace(actors=lambda: (actor,)),
            social=SimpleNamespace(
                npcs=SimpleNamespace(
                    all=lambda: (npc,),
                    get=lambda npc_id: npc if npc_id == "warden_lyra" else None,
                ),
                dialogues={"warden_intro": dialogue},
            ),
        )
        self.service.application.holder = SimpleNamespace(current=bundle)
        self.service.relationship = Mock(return_value=SimpleNamespace(trust=0))
        self.service.talk_to_npc = Mock(
            return_value=SimpleNamespace(
                node_id="start", text="Seni tanımıyorum.", choices=(),
            ),
        )
        screen = DialogueScreen(self.service)
        screen.set_target_npc("warden_lyra")

        screen._open_default()

        self.service.talk_to_npc.assert_called_once_with(
            "traveler_actor", "warden_lyra", "warden_intro",
            node_id=None,
        )
        self.assertEqual(screen.opening_stage, "creation")

    def test_dialogue_does_not_treat_first_actor_as_player(self):
        npc_actor = SimpleNamespace(actor_id="guard_actor")
        bundle = SimpleNamespace(
            actors=SimpleNamespace(actors=lambda: (npc_actor,)),
            social=SimpleNamespace(
                npcs=SimpleNamespace(all=lambda: (), get=lambda _npc_id: None),
                dialogues={},
            ),
        )
        self.service.application.holder = SimpleNamespace(current=bundle)
        screen = DialogueScreen(self.service)
        screen._open_default()

        self.assertIn("Oyuncu aktörü", screen.message)

if __name__ == "__main__":
    unittest.main()
