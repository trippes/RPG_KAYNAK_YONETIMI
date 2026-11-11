"""Playable multi-stage caravan quest demo content."""

from __future__ import annotations

from dataclasses import replace

from core.domain.spatial import Position
from npc import NPC
from quests import Dialogue, DialogueChoice, DialogueNode, Objective, ObjectiveType, Quest, Reward
from resources import Inventory, Quantity, ResourceType, ResourceUnit, WorldResourceNode


CARAVAN_QUEST_ID = "lost_caravan"
CARAVAN_NPC_ID = "caravan_merchant"
CARAVAN_DIALOGUE_ID = "caravan_merchant_dialogue"


def populate_caravan_quest_demo(service) -> Quest:
    """Register Yadigar, the long quest, and its test resources in a fresh game."""
    bundle = service.application.holder.current
    if "player" not in bundle.inventories:
        bundle = replace(
            bundle,
            inventories={**bundle.inventories, "player": Inventory()},
        )
        service.application.holder.publish(bundle)
    if bundle.quest_log.get(CARAVAN_QUEST_ID) is not None:
        service.caravan_quest = bundle.quest_log.get(CARAVAN_QUEST_ID)
        return service.caravan_quest

    world = bundle.session.worlds.get_active()
    if world is None:
        raise RuntimeError("Caravan quest demo requires an active world.")

    # Restore a genuinely playable first quest so the journal has two
    # independently selectable entries in a fresh game.
    carpenter = NPC(
        "village_carpenter",
        "Marangoz Hilmi",
        "carpenter",
        ("wardens",),
        "village",
        position=Position(21, 15),
    )
    service.register_npc(carpenter)
    carpenter_quest = Quest(
        "carpenter_wood",
        "Marangozun Odun İsteği",
        (
            Objective(
                "collect_wood",
                "Kuzey Ormanı'ndan marangoz atölyesi için 3 odun topla.",
                ObjectiveType.COLLECT,
                target_id="forest_wood",
                required=3,
            ),
            Objective(
                "deliver_wood",
                "Topladığın 3 odunu Marangoz Hilmi'ye teslim et.",
                ObjectiveType.CUSTOM,
            ),
        ),
        Reward(experience=35, currency=12),
    )
    bundle.quest_log.add(carpenter_quest)
    service.carpenter_quest = carpenter_quest
    service._quest_reward_accounts[carpenter_quest.quest_id] = "hero"
    service._quest_reward_inventories[carpenter_quest.quest_id] = "player"
    service.register_dialogue(Dialogue(
        "carpenter_dialogue",
        (
            DialogueNode(
                "start",
                "village_carpenter",
                "Marangoz Hilmi: Atölyenin çatısı fırtınada hasar gördü. "
                "Onarmak için üç oduna ihtiyacım var. Yardım edebilir misin?",
                (
                    DialogueChoice(
                        "accept_carpenter_quest",
                        "Elbette. Üç odun getiririm.",
                        "accepted",
                        action="accept_carpenter_quest",
                    ),
                    DialogueChoice(
                        "deliver_carpenter_wood",
                        "İstediğin odunları getirdim.",
                        None,
                        action="deliver_carpenter_wood",
                    ),
                    DialogueChoice("decline_carpenter_quest", "Şimdi değil.", None),
                ),
            ),
            DialogueNode(
                "accepted",
                "village_carpenter",
                "Harika. Kuzey Ormanı'ndaki ağaçlardan üç odun topla ve "
                "atölyeye geri dön. Malzemeleri teslim ettiğinde ödülünü alacaksın.",
                (),
            ),
        ),
        "start",
    ))

    npc = NPC(
        CARAVAN_NPC_ID,
        "Tüccar Yadigar",
        "merchant",
        ("wardens",),
        "village",
        position=Position(20, 20),
    )
    service.register_npc(npc)

    wood_node_id = "forest_wood"
    iron_node_id = "north_iron_mine"
    wood_node_ids = (wood_node_id,) + tuple(
        f"forest_tree_{index:02d}_wood" for index in range(2, 6)
    )
    for node_id in wood_node_ids:
        if bundle.resource_nodes.get(node_id) is None:
            bundle.resource_nodes.add(WorldResourceNode(
                node_id, world.world_id, ResourceType("wood"),
                Quantity(8, ResourceUnit.ITEM), Quantity(8, ResourceUnit.ITEM),
                Quantity(0, ResourceUnit.ITEM), location_id="forest",
            ))
    for node_id, location_id in (
        (iron_node_id, "forest"),
        ("north_mine_iron", "north_mine"),
    ):
        if bundle.resource_nodes.get(node_id) is None:
            bundle.resource_nodes.add(WorldResourceNode(
                node_id, world.world_id, ResourceType("iron_ore"),
                Quantity(6, ResourceUnit.ITEM), Quantity(6, ResourceUnit.ITEM),
                Quantity(0, ResourceUnit.ITEM), location_id=location_id,
            ))

    objectives = (
        Objective(
            "caravan_wood",
            "Kervanın kırılmış tekerleklerini onarmak için Kuzey Ormanı'ndan 3 odun topla.",
            ObjectiveType.COLLECT,
            target_id=wood_node_id,
            required=3,
        ),
        Objective(
            "caravan_ore",
            "Hasarlı yük kasalarını güçlendirmek için madenden 2 demir cevheri çıkar.",
            ObjectiveType.COLLECT,
            target_id=iron_node_id,
            required=2,
        ),
        Objective(
            "caravan_eren",
            "Topladığın izleri ve malzemeleri köy muhafızı Eren'e anlat.",
            ObjectiveType.TALK,
            target_id="warden_lyra",
        ),
        Objective(
            "caravan_return",
            "Araştırmanın sonucunu Tüccar Yadigar'a bildir ve kervanın akıbetini öğren.",
            ObjectiveType.TALK,
            target_id=CARAVAN_NPC_ID,
        ),
        Objective(
            "caravan_clue_wagons",
            "İsteğe bağlı: Orman yolundaki devrilmiş yük arabalarının izlerini incele.",
            ObjectiveType.CUSTOM,
            optional=True,
        ),
        Objective(
            "caravan_clue_tracks",
            "İsteğe bağlı: Çamurda kalan at ve tekerlek izlerini araştır.",
            ObjectiveType.CUSTOM,
            optional=True,
        ),
        Objective(
            "caravan_clue_camp",
            "İsteğe bağlı: Terk edilmiş kamp alanında geride kalan eşyaları ara.",
            ObjectiveType.CUSTOM,
            optional=True,
        ),
    )
    quest = Quest(
        CARAVAN_QUEST_ID,
        "Kayıp Kervanın İzinde",
        objectives,
        Reward(
            experience=120,
            currency=45,
            items=(("iron_ore", 1),),
            reputation=(("wardens", 5),),
        ),
        sequential_objectives=True,
    )
    bundle.quest_log.add(quest)
    service.caravan_quest = quest
    service._quest_reward_accounts[CARAVAN_QUEST_ID] = "hero"
    service._quest_reward_inventories[CARAVAN_QUEST_ID] = "player"

    service.register_dialogue(Dialogue(
        CARAVAN_DIALOGUE_ID,
        (
            DialogueNode(
                "start",
                CARAVAN_NPC_ID,
                (
                    "Tüccar Yadigar: Kuzey yolunda üç arabadan oluşan kervanım "
                    "kayboldu. Son haberci, ormandaki eski patikanın yakınında "
                    "kırılmış tekerlekler ve dağılmış yükler gördüğünü söyledi. "
                    "Tek başıma araştırmaya cesaret edemiyorum. Bana yardım eder misin?"
                ),
                (
                    DialogueChoice(
                        "accept_caravan_quest",
                        "Kervanın izini süreceğim. Bana bildiklerini anlat.",
                        "accepted",
                        action="accept_caravan_quest",
                    ),
                    DialogueChoice(
                        "decline_caravan_quest",
                        "Şimdilik başka işlerim var.",
                        None,
                    ),
                ),
            ),
            DialogueNode(
                "accepted",
                CARAVAN_NPC_ID,
                (
                    "Önce ormandan üç sağlam odun ve kuzey madeninden iki demir "
                    "cevheri getir. Bu malzemelerle kırılmış yük arabasının "
                    "izlerini güvenle takip edebiliriz. Sonra Eren'le konuş; "
                    "kervanın kaybolduğu gece nöbet ondaydı."
                ),
                (),
            ),
            DialogueNode(
                "report",
                CARAVAN_NPC_ID,
                (
                    "Demek izleri buldun ve Eren'in anlattıklarını doğruladın. "
                    "Bu bilgiler kervanın başına gelenleri aydınlatmamı sağladı. "
                    "Söz verdiğim ödül senindir. Yolculuğunda dikkatli ol."
                ),
                (),
            ),
        ),
        "start",
    ))
    return quest
