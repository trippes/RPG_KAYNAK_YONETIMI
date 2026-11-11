"""Temporary NPC and quest fixture for the quest-journal UI playtest.

Remove this module and its GameWindow hooks when the demo quest playtest ends.
No production content definitions or quest-domain rules belong here.
"""

from core.domain.spatial import Position
from npc import NPC
from quests import Dialogue, DialogueChoice, DialogueNode, Objective, ObjectiveType, Quest, QuestState, Reward


PLAYTEST_NPC_ID = "village_carpenter"
PLAYTEST_DIALOGUE_ID = "carpenter_intro"
PLAYTEST_QUEST_ID = "ui_playtest_forest_scouting"


def register_quest_playtest_fixture(service):
    """Idempotently add one temporary village quest giver and an accept-able quest."""
    bundle = service.application.holder.current

    npc = bundle.social.npcs.get(PLAYTEST_NPC_ID)
    if npc is None:
        service.register_npc(NPC(
            PLAYTEST_NPC_ID,
            "Hilmi",
            "carpenter",
            ("wardens",),
            "village",
            position=Position(14, 29),
        ))

    quest = bundle.quest_log.get(PLAYTEST_QUEST_ID)
    if quest is None:
        quest = Quest(
            PLAYTEST_QUEST_ID,
            "Orman Yolundaki İzler",
            (
                Objective(
                    "reach_forest_path",
                    "Köyün kuzeyindeki orman yoluna ulaş.",
                    ObjectiveType.REACH,
                    target_id="forest",
                ),
            ),
            Reward(experience=35, currency=12),
            state=QuestState.AVAILABLE,
        )
        bundle.quest_log.add(quest)

    service.carpenter_quest = quest

    if PLAYTEST_DIALOGUE_ID not in bundle.social.dialogues:
        service.register_dialogue(Dialogue(
            PLAYTEST_DIALOGUE_ID,
            (
                DialogueNode(
                    "carpenter_start",
                    PLAYTEST_NPC_ID,
                    "Köyün kuzeyindeki orman yolundan geceleri tuhaf sesler geliyor. "
                    "Ne olduğunu öğrenip bana haber verebilir misin?",
                    (
                        DialogueChoice(
                            "accept_carpenter_quest",
                            "Elbette. Orman yolunu araştıracağım.",
                            next_node_id="quest_accepted",
                            action="accept_carpenter_quest",
                        ),
                        DialogueChoice(
                            "decline_carpenter_quest",
                            "Şimdilik başka işlerim var.",
                            next_node_id="quest_declined",
                        ),
                    ),
                ),
                DialogueNode(
                    "quest_accepted",
                    PLAYTEST_NPC_ID,
                    "İyi. Orman yoluna kadar git ve çevreyi dikkatlice incele. "
                    "Döndüğünde gördüklerini anlat.",
                ),
                DialogueNode(
                    "quest_declined",
                    PLAYTEST_NPC_ID,
                    "Anlıyorum. Fikrini değiştirirsen beni burada bulabilirsin.",
                ),
            ),
            "carpenter_start",
        ))

    return PLAYTEST_QUEST_ID


__all__ = [
    "PLAYTEST_NPC_ID",
    "PLAYTEST_DIALOGUE_ID",
    "PLAYTEST_QUEST_ID",
    "register_quest_playtest_fixture",
]
