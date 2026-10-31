import json
import tempfile
import unittest
from pathlib import Path

from application import GameApplication, GameplayService
from character import Attribute, CharacterClass, CharacterFactory, Race
from core.domain.spatial import Position
from resources import Inventory, Quantity, ResourceType, ResourceUnit, WorldResourceNode
from world import Location, WorldMap


class TestCharacterActorIntegration(unittest.TestCase):
    def setUp(self):
        self.application = GameApplication.create_default()
        self.world = self.application.dunya_olustur("Başlangıç", world_id="world_start")
        self.factory = CharacterFactory(
            {"human": Race("human", "İnsan")},
            {"fighter": CharacterClass("fighter", "Savaşçı", hit_points=10)},
        )

    def test_character_creation_creates_and_binds_actor_both_ways(self):
        character = self.application.karakter_olustur(
            self.factory, "char_1", "Arin", "human", "fighter"
        )
        actor = self.application.holder.current.actors.get("char_1")

        self.assertEqual(character.actor_id, "char_1")
        self.assertEqual(actor.character_id, "char_1")
        self.assertEqual(actor.world_id, self.world.world_id)

    def test_actor_reads_character_stats(self):
        self.application.karakter_olustur(
            self.factory, "char_1", "Arin", "human", "fighter"
        )
        stats = GameplayService(self.application).actor_stats("char_1")

        self.assertEqual(stats["character_id"], "char_1")
        self.assertEqual(stats["attributes"][Attribute.STRENGTH.value], 10)
        self.assertEqual(stats["max_hit_points"], 20)

    def test_register_actor_with_character_id_binds_both_sides(self):
        character = self.application.karakter_olustur(
            self.factory, "char_1", "Arin", "human", "fighter", "initial_actor"
        )
        self.application.holder.current.actors.remove("initial_actor")
        character.actor_id = None

        service = GameplayService(self.application)
        actor = service.register_actor(
            "actor_1", "fighter", self.world.world_id, character_id="char_1"
        )

        self.assertEqual(actor.character_id, "char_1")
        self.assertEqual(character.actor_id, "actor_1")
        self.assertEqual(service.actor_stats("actor_1")["name"], "Arin")

    def test_register_actor_rejects_character_bound_to_another_actor(self):
        character = self.application.karakter_olustur(
            self.factory, "char_1", "Arin", "human", "fighter", "actor_1"
        )
        service = GameplayService(self.application)

        with self.assertRaises(ValueError):
            service.register_actor(
                "actor_2", "fighter", self.world.world_id, character_id=character.character_id
            )

        self.assertIsNone(self.application.holder.current.actors.get("actor_2"))
        self.assertEqual(character.actor_id, "actor_1")

    def test_save_load_preserves_reciprocal_link_and_stats(self):
        self.application.karakter_olustur(
            self.factory, "char_1", "Arin", "human", "fighter", "actor_1"
        )
        service = GameplayService(self.application)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "character-save.json"
            service.save(path)
            service.load(path)

        bundle = self.application.holder.current
        self.assertEqual(bundle.characters["char_1"].actor_id, "actor_1")
        self.assertEqual(bundle.actors.get("actor_1").character_id, "char_1")
        self.assertEqual(service.actor_stats("actor_1")["name"], "Arin")

    def test_load_rejects_one_sided_actor_character_link(self):
        self.application.karakter_olustur(
            self.factory, "char_1", "Arin", "human", "fighter"
        )
        service = GameplayService(self.application)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "character-save.json"
            service.save(path)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["actors"]["actors"][0]["character_id"] = "missing"
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaises(Exception):
                service.load(path)

        self.assertIsNotNone(self.application.holder.current.characters["char_1"])

    def test_actor_can_interact_at_current_location_and_gather_there(self):
        self.application.karakter_olustur(
            self.factory, "char_1", "Arin", "human", "fighter"
        )
        bundle = self.application.holder.current
        # The default bundle has immutable registries; install the test inventory
        # using the same application-level setup convention as the demo.
        from types import MappingProxyType
        object.__setattr__(bundle, "inventories", MappingProxyType({"main": Inventory()}))
        resource = ResourceType("ore")
        bundle.resource_nodes.add(WorldResourceNode(
            "ore-node", self.world.world_id, resource,
            Quantity(2, ResourceUnit.ITEM), Quantity(2, ResourceUnit.ITEM),
            Quantity(0, ResourceUnit.ITEM),
        ))
        world_map = WorldMap(self.world.world_id)
        world_map.add_location(Location("mine", "Maden", Position(0, 0)))
        service = GameplayService(self.application)
        service.register_world_map(world_map)
        service.place_actor("char_1", "mine")

        interaction = service.interact_with_location("char_1", "mine")
        self.assertEqual(interaction.character_id, "char_1")
        self.assertEqual(interaction.location_name, "Maden")
        result = service.start_gathering_at_location(
            "char_1", "mine", "ore-node", "main",
            Quantity(1, ResourceUnit.ITEM), "mine-gather",
        )
        self.assertEqual(result.state, "completed")


if __name__ == "__main__":
    unittest.main()
