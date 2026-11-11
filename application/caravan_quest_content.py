"""Playable caravan quest content for the Eldoria demo branch."""

from core.domain.spatial import Position
from npc import NPC
from quests import Dialogue, DialogueChoice, DialogueNode, Objective, ObjectiveType, Quest, Reward

CARAVAN_QUEST_ID = "lost_caravan"
CARAVAN_NPC_ID = "caravan_merchant"
CARAVAN_DIALOGUE_ID = "caravan_merchant_dialogue"


def populate_caravan_quest_demo(service):
    """Register Yadigar and the sequential caravan quest in a gameplay session."""
    bundle = service.application.holder.current
    if "player" not in bundle.inventories:
        raise RuntimeError("Caravan quest requires the player inventory.")
    existing = bundle.quest_log.get(CARAVAN_QUEST_ID)

    npc = bundle.social.npcs.get(CARAVAN_NPC_ID)
    if npc is None:
        service.register_npc(NPC(
            CARAVAN_NPC_ID, "Tüccar Yadigar", "merchant",
            ("wardens",), "village", position=Position(20, 20),
        ))

    quest = existing or Quest(
        CARAVAN_QUEST_ID,
        "Kayıp Kervanın İzinde",
        (
            Objective(
                "caravan_wood",
                "Kervanın kırılmış tekerleklerini onarmak için Kuzey Ormanı'ndan 3 odun topla.",
                ObjectiveType.COLLECT, target_id="forest_wood", required=3,
            ),
            Objective(
                "caravan_ore",
                "Hasarlı yük kasalarını güçlendirmek için kuzey madeninden 2 demir cevheri çıkar.",
                ObjectiveType.COLLECT, target_id="north_iron_mine", required=2,
            ),
            Objective(
                "caravan_eren",
                "Topladığın malzemeleri ve izleri köy muhafızı Eren'e anlat.",
                ObjectiveType.TALK, target_id="warden_lyra",
            ),
            Objective(
                "caravan_return",
                "Araştırmanın sonucunu Tüccar Yadigar'a bildir.",
                ObjectiveType.TALK, target_id=CARAVAN_NPC_ID,
            ),
            Objective(
                "caravan_clue_wagons",
                "İsteğe bağlı: Orman yolundaki devrilmiş yük arabalarının izlerini incele.",
                ObjectiveType.CUSTOM, optional=True,
            ),
            Objective(
                "caravan_clue_tracks",
                "İsteğe bağlı: Çamurda kalan at ve tekerlek izlerini araştır.",
                ObjectiveType.CUSTOM, optional=True,
            ),
        ),
        Reward(
            experience=120, currency=45,
            items=(("iron_ore", 1),), reputation=(("wardens", 5),),
        ),
        sequential_objectives=True,
    )
    if existing is None:
        bundle.quest_log.add(quest)
    service.caravan_quest = quest
    service._quest_reward_accounts[CARAVAN_QUEST_ID] = "hero"
    service._quest_reward_inventories[CARAVAN_QUEST_ID] = "player"

    if CARAVAN_DIALOGUE_ID not in bundle.social.dialogues:
        service.register_dialogue(Dialogue(
            CARAVAN_DIALOGUE_ID,
            (
                DialogueNode(
                    "start", CARAVAN_NPC_ID,
                    "Tüccar Yadigar: Kuzey yolunda üç arabadan oluşan kervanım kayboldu. "
                    "Son haberci, ormandaki eski patikanın yakınında kırılmış tekerlekler "
                    "ve dağılmış yükler gördüğünü söyledi. Tek başıma araştırmaya "
                    "cesaret edemiyorum. Bana yardım eder misin?",
                    (
                        DialogueChoice(
                            "accept_caravan_quest",
                            "Kervanın izini süreceğim. Bana bildiklerini anlat.",
                            "accepted", action="accept_caravan_quest",
                        ),
                        DialogueChoice(
                            "decline_caravan_quest",
                            "Şimdilik başka işlerim var.", None,
                        ),
                    ),
                ),
                DialogueNode(
                    "accepted", CARAVAN_NPC_ID,
                    "Önce ormandan üç odun ve kuzey madeninden iki demir cevheri getir. "
                    "Bunlarla kırılmış yük arabasının izlerini takip edebiliriz. "
                    "Sonra Eren'le konuş; kervanın kaybolduğu gece nöbet ondaydı.",
                ),
                DialogueNode(
                    "report", CARAVAN_NPC_ID,
                    "Demek izleri buldun ve Eren'in anlattıklarını doğruladın. "
                    "Bu bilgiler kervanın başına gelenleri aydınlattı. "
                    "Söz verdiğim ödül senindir. Yolculuğunda dikkatli ol.",
                ),
            ),
            "start",
        ))
    return quest


__all__ = [
    "CARAVAN_QUEST_ID", "CARAVAN_NPC_ID", "CARAVAN_DIALOGUE_ID",
    "populate_caravan_quest_demo",
]
