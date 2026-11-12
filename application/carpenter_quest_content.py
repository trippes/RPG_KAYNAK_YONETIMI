"""Playable carpenter quest mechanics for the Eldoria demo package."""

from quests import Dialogue, DialogueChoice, DialogueNode, Objective, ObjectiveType, Quest, Reward

CARPENTER_QUEST_ID = "carpenter_wood"
CARPENTER_NPC_ID = "village_carpenter"
CARPENTER_DIALOGUE_ID = "carpenter_dialogue"


def populate_carpenter_quest_demo(service):
    """Register the wood-delivery quest; its giver NPC is content-package data."""
    bundle = service.application.holder.current
    existing = bundle.quest_log.get(CARPENTER_QUEST_ID)

    # NPC identity and placement are loaded from the active content package.
    quest = existing or Quest(
        CARPENTER_QUEST_ID,
        "Marangozun Odun İsteği",
        (
            Objective(
                "collect_wood",
                "Kuzey Ormanı'ndan marangoz atölyesi için 3 odun topla.",
                ObjectiveType.COLLECT, target_id="forest_wood", required=3,
            ),
            Objective(
                "deliver_wood",
                "Topladığın 3 odunu Marangoz Hilmi'ye teslim et.",
                ObjectiveType.CUSTOM,
            ),
        ),
        Reward(experience=35, currency=12),
        sequential_objectives=True,
        giver_npc_id=CARPENTER_NPC_ID,
    )
    if existing is None:
        bundle.quest_log.add(quest)
    service.carpenter_quest = quest
    service._quest_reward_accounts[CARPENTER_QUEST_ID] = "hero"
    service._quest_reward_inventories[CARPENTER_QUEST_ID] = "player"

    if CARPENTER_DIALOGUE_ID not in bundle.social.dialogues:
        service.register_dialogue(Dialogue(
            CARPENTER_DIALOGUE_ID,
            (
                DialogueNode(
                    "start", CARPENTER_NPC_ID,
                    "Marangoz Hilmi: Atölyenin çatısı fırtınada hasar gördü. "
                    "Onarmak için üç oduna ihtiyacım var. Yardım edebilir misin?",
                    (
                        DialogueChoice(
                            "accept_carpenter_quest",
                            "Elbette. Üç odun getiririm.",
                            "accepted", action="accept_carpenter_quest",
                        ),
                        DialogueChoice(
                            "deliver_carpenter_wood",
                            "İstediğin odunları getirdim.",
                            None, action="deliver_carpenter_wood",
                        ),
                        DialogueChoice(
                            "decline_carpenter_quest",
                            "Şimdi değil.", None,
                        ),
                    ),
                ),
                DialogueNode(
                    "accepted", CARPENTER_NPC_ID,
                    "Harika. Kuzey Ormanı'ndaki ağaçlardan üç odun topla ve "
                    "atölyeye geri dön. Malzemeleri teslim ettiğinde ödülünü alacaksın.",
                ),
            ),
            "start",
        ))
    return quest


__all__ = [
    "CARPENTER_QUEST_ID", "CARPENTER_NPC_ID", "CARPENTER_DIALOGUE_ID",
    "populate_carpenter_quest_demo",
]
