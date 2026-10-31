"""Data-driven content loading for the playable demo slice."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, fields
from pathlib import Path
from types import MappingProxyType

from application import GameplayService
from application import ProductionFacility
from character import Ability, CharacterClass, CharacterFactory, Race
from combat import Combatant
from core.domain.spatial import Position
from economy import Currency, Merchant, Money
from npc import Faction, NPC
from quests import Dialogue, DialogueChoice, DialogueNode, Objective, ObjectiveType, Quest, Reward
from resources import Inventory, Quantity, Recipe, ResourceType, ResourceUnit, WorldResourceNode
from world import Location, WorldMap


DEFAULT_CONTENT_PATH = Path(__file__).resolve().parent.parent / "data" / "demo_content.json"
CONTENT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class DemoContentIds:
    world_id: str = "demo_valley"
    hero_id: str = "hero"
    village_id: str = "village"
    forest_id: str = "forest"
    faction_id: str = "wardens"
    npc_id: str = "warden_lyra"
    quest_id: str = "forest_supplies"
    carpenter_id: str = "village_carpenter"
    carpenter_quest_id: str = "carpenter_repair"
    blacksmith_id: str = "village_blacksmith"
    blacksmith_quest_id: str = "blacksmith_iron"
    iron_node_id: str = "north_iron_mine"
    inn_quest_id: str = "inn_supplies"
    node_id: str = "forest_wood"
    inventory_id: str = "player"
    merchant_id: str = "village_merchant"
    merchant_inventory_id: str = "merchant"
    market_offer_id: str = "market_plank"
    bread_offer_id: str = "market_bread"
    water_offer_id: str = "market_water"
    innkeeper_id: str = "village_innkeeper"
    enemy_id: str = "forest_wolf"
    encounter_id: str = "forest_wolf_encounter"
    


class ContentDefinitionError(ValueError):
    """Raised when a content definition cannot safely enter the runtime."""


def load_demo_content(path: str | Path | None = None) -> dict:
    """Load and validate a JSON content definition without mutating it."""
    if path is None:
        candidates = (
            DEFAULT_CONTENT_PATH,
            Path(sys.prefix) / "data" / "demo_content.json",
            Path(sys.prefix) / "demo_content.json",
        )
        source = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    else:
        source = Path(path)
    try:
        definition = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContentDefinitionError(f"Content definition could not be loaded: {source}") from error
    if not isinstance(definition, dict):
        raise ContentDefinitionError("Content definition must be a JSON object.")
    if definition.get("schema_version") != CONTENT_SCHEMA_VERSION:
        raise ContentDefinitionError("Unsupported content definition schema version.")
    required = {"ids", "world", "character", "resources", "recipe", "locations", "faction", "npc", "dialogue", "quest", "merchant", "market_offer", "combat"}
    missing = sorted(required - definition.keys())
    if missing:
        raise ContentDefinitionError(f"Content definition is missing sections: {', '.join(missing)}")
    return definition


def _id_resolver(definition: dict, ids: DemoContentIds):
    configured = definition["ids"]
    valid_fields = {field.name for field in fields(DemoContentIds)}
    if set(configured) != valid_fields:
        raise ContentDefinitionError("Content ids must match DemoContentIds fields.")
    replacements = {key: getattr(ids, key) for key in valid_fields}
    return lambda key: replacements.get(key, key)


def _quantity(raw: dict) -> Quantity:
    return Quantity(int(raw["amount"]), ResourceUnit(raw.get("unit", "item")))

def build_demo_world_map(
    world_id: str,
    ids: DemoContentIds = DemoContentIds(),
    definition_path=None,
):
    """Rebuild the static demo map without resetting saved gameplay state."""
    definition = load_demo_content(definition_path)
    resolve_id = _id_resolver(definition, ids)

    world_map = WorldMap(world_id)

    for location in definition["locations"]:
        world_map.add_location(
            Location(
                resolve_id(location["id"]),
                location["name"],
                tuple(location["position"])
                if location.get("position") is not None
                else None,
                location.get("description", ""),
                location.get("type", "unknown"),
                tuple(location.get("activities", ())),
                tuple(
                    (
                        landmark["id"],
                        landmark["name"],
                        tuple(landmark.get("position", (180, 180))),
                        tuple(landmark.get("activities", ())),
                        landmark.get("description", ""),
                    )
                    for landmark in location.get("landmarks", ())
                ),
            )
        )

    for connection in definition.get("connections", ()):
        world_map.connect(resolve_id(connection[0]), resolve_id(connection[1]))

    return world_map


def populate_demo_content(application, ids: DemoContentIds = DemoContentIds(), definition_path=None):
    """Build a deterministic playable session from a JSON content definition."""
    definition = load_demo_content(definition_path)
    resolve_id = _id_resolver(definition, ids)
    world_data = definition["world"]
    world = application.aktif_dunya() or application.dunya_olustur(
        world_data["name"], width=world_data["width"], height=world_data["height"], world_id=resolve_id("world_id")
    )
    bundle = application.holder.current

    resource_types = {item["id"]: ResourceType(item["id"]) for item in definition["resources"]}
    inventory = Inventory()
    merchant_inventory = Inventory()
    recipe_data = definition["recipe"]
    output = _quantity(recipe_data["outputs"][0])
    merchant_inventory.add(
        resource_types[recipe_data["outputs"][0]["resource"]],
        Quantity(definition["merchant"]["stock_amount"], output.unit),
    )
    for offer in definition.get("market_offers", ()):
        merchant_inventory.add(
            resource_types[offer["resource"]],
            Quantity(offer.get("stock_amount", offer["quantity"]), ResourceUnit.ITEM),
        )
    object.__setattr__(bundle, "inventories", MappingProxyType({
        ids.inventory_id: inventory,
        ids.merchant_inventory_id: merchant_inventory,
    }))
    inputs = tuple((resource_types[item["resource"]], _quantity(item)) for item in recipe_data["inputs"])
    outputs = tuple((resource_types[item["resource"]], _quantity(item)) for item in recipe_data["outputs"])
    object.__setattr__(bundle, "recipes", MappingProxyType({
        recipe_data["id"]: Recipe(recipe_data["id"], inputs, outputs, recipe_data["duration"], recipe_data["output_tag"]),
    }))
    facility_data = recipe_data["facility"]
    if bundle.facilities.get(facility_data["id"]) is None:
        bundle.facilities.add(ProductionFacility(facility_data["id"], facility_data["type"], facility_data["capacity"]))

    node_data = definition["resources"][0]
    zero_regeneration = Quantity(0, _quantity(node_data["regeneration_rate"]).unit)
    bundle.resource_nodes.add(WorldResourceNode(
        resolve_id("node_id"), world.world_id, resource_types[node_data["id"]], _quantity(node_data["node_quantity"]),
        _quantity(node_data["node_capacity"]), zero_regeneration,
        location_id=resolve_id(node_data["location_id"]),
    ))
    for location in definition["locations"]:
        resource_landmarks = [
            landmark for landmark in location.get("landmarks", ())
            if (
                "tree" in landmark["id"]
                or "ağaç" in landmark["name"].lower()
                or "mine" in landmark["id"]
                or "maden" in landmark["name"].lower()
            )
        ]
        for index, landmark in enumerate(resource_landmarks):
            is_iron = "mine" in landmark["id"] or "maden" in landmark["name"].lower()
            resource_data = next(
                item for item in definition["resources"]
                if item["id"] == ("iron_ore" if is_iron else "wood")
            )
            node_id = (
                resolve_id("node_id")
                if location["id"] == "forest_id" and not is_iron and index == 0
                else (
                    resolve_id("iron_node_id")
                    if location["id"] == "forest_id" and is_iron
                    else landmark["id"] if is_iron else f"{landmark['id']}_wood"
                )
            )
            if bundle.resource_nodes.get(node_id) is not None:
                continue
            bundle.resource_nodes.add(WorldResourceNode(
                node_id,
                world.world_id,
                resource_types[resource_data["id"]],
                _quantity(resource_data["node_quantity"]),
                _quantity(resource_data["node_capacity"]),
                Quantity(0, _quantity(resource_data["regeneration_rate"]).unit),
                location_id=resolve_id(location["id"]),
            ))

    character_data = definition["character"]
    race_data = character_data["race"]
    class_data = character_data["class"]
    factory = CharacterFactory(
        {race_data["id"]: Race(race_data["id"], race_data["name"], abilities=(Ability(race_data["ability_id"], race_data["ability_name"]),))},
        {class_data["id"]: CharacterClass(class_data["id"], class_data["name"], hit_points=class_data["hit_points"])},
    )
    if not bundle.characters:
        application.karakter_olustur(factory, resolve_id("hero_id"), character_data["name"], race_data["id"], class_data["id"], resolve_id("hero_id"))
    service = GameplayService(application)
    service.register_character_factory(factory)

    faction_data = definition["faction"]
    service.register_faction(Faction(resolve_id("faction_id"), faction_data["name"]))
    npc_data = definition["npc"]
    service.register_npc(
        NPC(
            resolve_id("npc_id"),
            npc_data["name"],
            npc_data["role"],
            (resolve_id("faction_id"),),
            resolve_id(npc_data["location_id"]),
            position=Position(*(npc_data.get("position") or (16, 30))),
        )
    )
    service.register_npc(
        NPC(
            resolve_id("innkeeper_id"),
            definition.get("innkeeper_npc", {}).get("name", "Han İşletmecisi Ayşe"),
            "innkeeper",
            (resolve_id("faction_id"),),
            resolve_id("village_id"),
            position=Position(*(definition.get("innkeeper_npc", {}).get("position") or (20, 23))),
        )
    )
    carpenter_data = definition.get("carpenter_npc", {})
    service.register_npc(
        NPC(
            resolve_id("carpenter_id"),
            carpenter_data.get("name", "Marangoz Hilmi"),
            carpenter_data.get("role", "carpenter"),
            (resolve_id("faction_id"),),
            resolve_id(carpenter_data.get("location_id", "village_id")),
            position=Position(*(carpenter_data.get("position") or (21, 15))),
        )
    )
    blacksmith_data = definition.get("blacksmith_npc", {})
    service.register_npc(
        NPC(
            resolve_id("blacksmith_id"),
            blacksmith_data.get("name", "Demirci Usta"),
            blacksmith_data.get("role", "blacksmith"),
            (resolve_id("faction_id"),),
            resolve_id(blacksmith_data.get("location_id", "village_id")),
            position=Position(*(blacksmith_data.get("position") or (27, 15))),
        )
    )

    dialogue_data = definition["dialogue"]
    nodes = []
    for node_data in dialogue_data["nodes"]:
        choices = tuple(DialogueChoice(choice["id"], choice["text"], choice.get("next")) for choice in node_data.get("choices", ()))
        nodes.append(DialogueNode(node_data["id"], resolve_id("npc_id"), node_data["text"], choices))
    service.register_dialogue(Dialogue(dialogue_data["id"], tuple(nodes), dialogue_data["start_node"]))
    carpenter_dialogue = Dialogue(
        "carpenter_intro",
        (
            DialogueNode(
                "carpenter_start",
                resolve_id("carpenter_id"),
                "Ben köyün marangoz ustasıyım. Yardım edecek birini arıyordum. "
                "Benim için çalışmak ister misin?",
                (
                    DialogueChoice(
                        "accept_carpenter_quest",
                        "Evet, işi kabul ediyorum.",
                        action="accept_carpenter_quest",
                    ),
                    DialogueChoice(
                        "deliver_carpenter_wood",
                        "İstediğin odunları getirdim.",
                        action="deliver_carpenter_wood",
                    ),
                    DialogueChoice(
                        "accept_inn_quest",
                        "Han için ekmek ve su alabilirim.",
                        action="accept_inn_quest",
                    ),
                    DialogueChoice(
                        "deliver_inn_supplies",
                        "Ekmek ve suyu getirdim.",
                        action="deliver_inn_supplies",
                    ),
                    DialogueChoice(
                        "decline_carpenter_quest",
                        "Şimdilik hayır.",
                    ),
                ),
            ),
        ),
        "carpenter_start",
    )
    service.register_dialogue(carpenter_dialogue)
    service.register_dialogue(Dialogue(
        "blacksmith_intro",
        (
            DialogueNode(
                "blacksmith_start",
                resolve_id("blacksmith_id"),
                "Demir ocağından demir cevheri getirirsen onu dövüp sana sağlam bir demir kılıç yapabilirim.",
                (
                    DialogueChoice(
                        "accept_blacksmith_quest",
                        "Demir cevheri toplamaya gidiyorum.",
                        action="accept_blacksmith_quest",
                    ),
                    DialogueChoice(
                        "deliver_blacksmith_ore",
                        "İstediğin demir cevherini getirdim.",
                        action="deliver_blacksmith_ore",
                    ),
                ),
            ),
        ),
        "blacksmith_start",
    ))
    service.register_dialogue(Dialogue(
        "innkeeper_intro",
        (
            DialogueNode(
                "innkeeper_start",
                resolve_id("innkeeper_id"),
                "Hoş geldin. Hanımızda taze ekmek ve temiz su bulunur.",
                (
                    DialogueChoice(
                        "open_inn_market",
                        "Ekmek ve su satın almak istiyorum.",
                        action="open_market",
                    ),
                    DialogueChoice("leave_inn", "Teşekkürler, birazdan bakarım."),
                ),
            ),
        ),
        "innkeeper_start",
    ))

    quest_data = definition["quest"]
    objectives = tuple(
        Objective(item["id"], item["description"], ObjectiveType(item["type"]), resolve_id(item["target_id"]))
        for item in quest_data["objectives"]
    )
    reward_data = quest_data["reward"]
    quest = Quest(
        resolve_id("quest_id"), quest_data["title"], objectives,
        Reward(currency=reward_data["currency"], items=tuple(tuple(item) for item in reward_data["items"]), reputation=((resolve_id("faction_id"), reward_data["reputation"]),)),
    )
    service.available_forest_quest = quest
    carpenter_quest = Quest(
        resolve_id("carpenter_quest_id"),
        "Marangozun Yardımcısı",
        (
            Objective(
                "collect_wood",
                "Marangoz için odun topla",
                ObjectiveType.COLLECT,
                resolve_id("node_id"),
                required=3,
            ),
            Objective(
                "deliver_wood",
                "Odunları Marangoz Hilmi'ye teslim et",
                ObjectiveType.CUSTOM,
                resolve_id("carpenter_id"),
                required=1,
            ),
        ),
        Reward(
            currency=15,
            items=(),
            reputation=((resolve_id("faction_id"), 5),),
        ),
    )
    service.carpenter_quest = carpenter_quest
    service.carpenter_quest_reward_inventory_id = resolve_id("inventory_id")
    service.inn_quest = Quest(
        resolve_id("inn_quest_id"),
        "Handan Erzak Al",
        (
            Objective("buy_bread", "Handan ekmek al", ObjectiveType.COLLECT, "bread"),
            Objective("buy_water", "Handan su al", ObjectiveType.COLLECT, "water"),
            Objective("deliver_supplies", "Ekmek ve suyu Hilmi'ye teslim et", ObjectiveType.CUSTOM, "carpenter_id"),
        ),
        Reward(currency=10),
    )
    service.blacksmith_quest = Quest(
        resolve_id("blacksmith_quest_id"),
        "Demirciye Cevher Getir",
        (
            Objective(
                "collect_iron_ore",
                "Demir madenlerinden demir cevheri topla",
                ObjectiveType.COLLECT,
                resolve_id("iron_node_id"),
                required=3,
            ),
            Objective(
                "deliver_iron_ore",
                "Demir cevherini demirciye teslim et",
                ObjectiveType.CUSTOM,
                resolve_id("blacksmith_id"),
                required=1,
            ),
        ),
        Reward(items=(("iron_sword", 1),)),
    )
    bundle.quest_log.add(quest)
    bundle.quest_log.add(carpenter_quest)
    bundle.quest_log.add(service.inn_quest)
    bundle.quest_log.add(service.blacksmith_quest)
    
    world_map = WorldMap(world.world_id)
    for location in definition["locations"]:
        world_map.add_location(Location(
            resolve_id(location["id"]), location["name"],
            tuple(location["position"]) if location.get("position") is not None else None,
            location.get("description", ""),
            location.get("type", "unknown"),
            tuple(location.get("activities", ())),
            tuple(
                (
                    landmark["id"], landmark["name"], tuple(landmark.get("position", (180, 180))),
                    tuple(landmark.get("activities", ())), landmark.get("description", ""),
                )
                for landmark in location.get("landmarks", ())
            ),
        ))
    for connection in definition.get("connections", ()):
        world_map.connect(resolve_id(connection[0]), resolve_id(connection[1]))
    service.register_world_map(world_map)
    service.place_actor(resolve_id("hero_id"), resolve_id("village_id"))

    merchant_data = definition["merchant"]
    service.register_merchant(Merchant(resolve_id("merchant_id"), account_id=resolve_id("merchant_id"), inventory_id=resolve_id("merchant_inventory_id")))
    offer_data = definition["market_offer"]
    service.publish_offer(
        resolve_id("market_offer_id"), resolve_id("merchant_id"), resolve_id("merchant_inventory_id"),
        resource_types[offer_data["resource"]], offer_data["quantity"],
        Money(offer_data["price"], Currency(offer_data["currency"])),
    )
    for offer in definition.get("market_offers", ()):
        service.publish_offer(
            resolve_id(offer["id"]),
            resolve_id("merchant_id"),
            resolve_id("merchant_inventory_id"),
            resource_types[offer["resource"]],
            offer["quantity"],
            Money(offer["price"], Currency(offer["currency"])),
        )

    combat_data = definition["combat"]
    service.add_combatant(Combatant(resolve_id("hero_id"), combat_data["hero"]["hp"], attack=combat_data["hero"]["attack"], defense=combat_data["hero"]["defense"]))
    service.add_combatant(Combatant(resolve_id("enemy_id"), combat_data["enemy"]["hp"], attack=combat_data["enemy"]["attack"], defense=combat_data["enemy"]["defense"]))
    service.create_combat_encounter(resolve_id("encounter_id"), (resolve_id("hero_id"), resolve_id("enemy_id")), {resolve_id("hero_id"): combat_data["hero"]["initiative"], resolve_id("enemy_id"): combat_data["enemy"]["initiative"]})
    return service, ids


__all__ = [
    "CONTENT_SCHEMA_VERSION",
    "ContentDefinitionError",
    "DemoContentIds",
    "load_demo_content",
    "populate_demo_content",
    "build_demo_world_map",
]