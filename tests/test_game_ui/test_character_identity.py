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
        self._character_factory = None
        self._creation_from_eren = False
        self._player_name_confirmed = False
        self.application = SimpleNamespace(
            customize_character=self.customize_character,
        )

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
        self.assertEqual(self.service.actor_character_calls, ["traveler_actor"])
        self.assertEqual(
            self.service.customization_calls[0][0],
            "traveler_character",
        )

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
        self.service.state = lambda: SimpleNamespace(actors=(npc, player))
        screen = CharacterScreen(self.service)
        screen._layout = lambda: {
            "outer": (0, 0, 100, 100),
            "identity": (0, 0, 10, 10),
            "combat": None,
            "attributes": (0, 0, 10, 10),
            "skills": (0, 0, 10, 10),
        }
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
        screen._render_identity.assert_called_once_with(
            renderer,
            self.service.character,
            self.service.actor_stats("traveler_actor"),
            (0, 0, 10, 10),
        )

    def test_dialogue_resume_resolves_character_through_player_actor(self):
        screen = DialogueScreen(self.service)

        screen.resume_after_creation()

        self.assertEqual(self.service.actor_character_calls, ["traveler_actor"])
        self.assertEqual(screen.character_name, "Traveler")
        self.assertEqual(screen.opening_stage, "ask_reason")

    def test_dialogue_name_confirmation_uses_player_actor_character(self):
        screen = DialogueScreen(self.service)
        screen.opening_stage = "dialogue"
        screen.name_entry_active = True
        screen.character_name = "New Name"

        screen.handle(InputState(actions={"confirm"}))

        self.assertEqual(self.service.actor_character_calls, ["traveler_actor"])
        self.assertEqual(self.service.character.name, "New Name")
        self.assertEqual(screen.opening_stage, "ask_reason")


if __name__ == "__main__":
    unittest.main()
