from application.content_pack import populate_opening_content
from application.game_application import GameApplication
from application.quest_playtest_content import (
    PLAYTEST_DIALOGUE_ID,
    PLAYTEST_NPC_ID,
    PLAYTEST_QUEST_ID,
    register_quest_playtest_fixture,
)
from game_ui.screens.main_screen import MainScreen
from game_ui.screens.quest_log_screen import QuestLogScreen


def _service():
    service, _ = populate_opening_content(GameApplication.create_default())
    register_quest_playtest_fixture(service)
    return service


def test_quest_playtest_fixture_places_talkable_npc_and_available_quest():
    service = _service()
    bundle = service.application.holder.current
    npc = bundle.social.npcs.get(PLAYTEST_NPC_ID)
    assert npc is not None
    assert npc.location_id == "village"
    assert (int(npc.position.x), int(npc.position.y)) == (14, 29)
    assert bundle.quest_log.get(PLAYTEST_QUEST_ID).state.value == "available"
    assert PLAYTEST_DIALOGUE_ID in bundle.social.dialogues

    local_map = MainScreen(service)
    assert local_map._npc_at((14, 29)) is npc


def test_accepting_playtest_dialogue_adds_active_quest_to_journal():
    service = _service()
    service.talk_to_npc("hero", PLAYTEST_NPC_ID, PLAYTEST_DIALOGUE_ID)
    service.choose_dialogue(
        "hero", PLAYTEST_NPC_ID, PLAYTEST_DIALOGUE_ID,
        "carpenter_start", "accept_carpenter_quest",
    )

    quest = service.application.holder.current.quest_log.get(PLAYTEST_QUEST_ID)
    assert quest.state.value == "active"
    assert quest.objectives[0].progress == 0
    assert quest.reward.experience == 35
    assert quest.reward.currency == 12

    journal = QuestLogScreen(service)
    assert journal._quests() == (quest,)
    assert journal._quests()[0].title == "Orman Yolundaki İzler"


def test_quest_playtest_fixture_is_idempotent():
    service = _service()
    first = register_quest_playtest_fixture(service)
    second = register_quest_playtest_fixture(service)
    bundle = service.application.holder.current

    assert first == second == PLAYTEST_QUEST_ID
    assert len([npc for npc in bundle.social.npcs.all() if npc.npc_id == PLAYTEST_NPC_ID]) == 1
    assert len([quest for quest in bundle.quest_log.all() if quest.quest_id == PLAYTEST_QUEST_ID]) == 1
