from application.content_pack import populate_gameplay_resources, populate_opening_content
from application.game_application import GameApplication
from application.carpenter_quest_content import populate_carpenter_quest_demo
from application.caravan_quest_content import (
    CARAVAN_DIALOGUE_ID,
    CARAVAN_NPC_ID,
    CARAVAN_QUEST_ID,
    populate_caravan_quest_demo,
)
from quests.persistence import QuestSnapshot
from resources import Quantity, ResourceUnit


def _gameplay_service():
    service, _ = populate_opening_content(GameApplication.create_default())
    populate_carpenter_quest_demo(service)
    populate_gameplay_resources(service)
    populate_caravan_quest_demo(service)
    return service


def test_caravan_quest_registers_yadigar_and_sequential_objectives():
    service = _gameplay_service()
    bundle = service.application.holder.current

    npc = bundle.social.npcs.get(CARAVAN_NPC_ID)
    quest = bundle.quest_log.get(CARAVAN_QUEST_ID)

    assert npc is not None
    assert npc.name == "Tüccar Yadigar"
    assert npc.location_id == "village"
    assert CARAVAN_DIALOGUE_ID in bundle.social.dialogues
    assert quest is service.caravan_quest
    assert quest.sequential_objectives is True
    assert quest.state.value == "available"


def test_caravan_quest_advances_one_mandatory_objective_at_a_time():
    service = _gameplay_service()
    quest = service.accept_caravan_quest("hero", "player")

    service.collect("forest_wood", "player", Quantity(3, ResourceUnit.ITEM))
    assert quest.objectives[0].progress == 3
    assert quest.objectives[1].progress == 0

    service.collect("north_iron_mine", "player", Quantity(2, ResourceUnit.ITEM))
    assert quest.objectives[1].progress == 2
    assert quest.objectives[2].progress == 0

    service.talk_to_npc("hero", "warden_lyra", "warden_intro")
    assert quest.objectives[2].completed
    assert not quest.objectives[3].completed

    service.talk_to_npc("hero", CARAVAN_NPC_ID, CARAVAN_DIALOGUE_ID)
    assert quest.state.value == "completed"
    report = service.choose_dialogue(
        "hero", CARAVAN_NPC_ID, CARAVAN_DIALOGUE_ID,
        "start", "caravan_report",
    )
    assert report.node_id == "report"


def test_caravan_sequential_flag_survives_quest_snapshot_round_trip():
    service = _gameplay_service()
    quest = service.accept_caravan_quest("hero", "player")
    service.collect("forest_wood", "player", Quantity(2, ResourceUnit.ITEM))

    snapshot = QuestSnapshot.from_log(service.application.holder.current.quest_log)
    restored = QuestSnapshot.from_dict(snapshot.to_dict()).restore({})

    restored_quest = restored.get(CARAVAN_QUEST_ID)
    assert restored_quest.sequential_objectives is True
    assert restored_quest.objectives[0].progress == 2
    assert restored_quest.objectives[1].progress == 0



def test_caravan_dialogue_accepts_the_quest_through_the_social_runtime():
    service = _gameplay_service()
    service.talk_to_npc("hero", CARAVAN_NPC_ID, CARAVAN_DIALOGUE_ID)

    next_node = service.choose_dialogue(
        "hero", CARAVAN_NPC_ID, CARAVAN_DIALOGUE_ID,
        "start", "accept_caravan_quest",
    )

    assert next_node.node_id == "accepted"
    assert service.caravan_quest.state.value == "active"



def test_carpenter_quest_collects_and_delivers_wood_for_a_reward():
    service = _gameplay_service()
    quest = service.accept_carpenter_quest("hero", "player")
    initial_balance = service.balance("hero", "gold").amount
    initial_experience = service.actor_character("hero").progression.experience

    service.collect("forest_wood", "player", Quantity(3, ResourceUnit.ITEM))
    assert quest.objectives[0].completed
    assert not quest.objectives[1].completed

    service.deliver_carpenter_wood("hero", "village_carpenter", "player")

    assert quest.state.value == "completed"
    assert service.balance("hero", "gold").amount == initial_balance + 12
    assert service.actor_character("hero").progression.experience == initial_experience + 35
