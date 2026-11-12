from application.content_pack import load_quest_definitions, populate_gameplay_resources, populate_opening_content
from application.game_application import GameApplication
from quests.persistence import QuestSnapshot
from resources import Quantity, ResourceUnit


CARPENTER_QUEST_ID = "carpenter_wood"
CARPENTER_NPC_ID = "village_carpenter"
CARPENTER_DIALOGUE_ID = "carpenter_dialogue"
CARAVAN_QUEST_ID = "lost_caravan"
CARAVAN_NPC_ID = "caravan_merchant"
CARAVAN_DIALOGUE_ID = "caravan_merchant_dialogue"


def _gameplay_service():
    service, _ = populate_opening_content(GameApplication.create_default())
    populate_gameplay_resources(service)
    return service


def test_quest_definitions_and_dialogues_are_loaded_from_content_data():
    service = _gameplay_service()
    bundle = service.application.holder.current
    definitions = {record["id"]: record for record in load_quest_definitions()}

    assert set(definitions) == {CARPENTER_QUEST_ID, CARAVAN_QUEST_ID}
    assert bundle.quest_log.get(CARPENTER_QUEST_ID) is not None
    assert bundle.quest_log.get(CARAVAN_QUEST_ID) is not None
    assert CARPENTER_DIALOGUE_ID in bundle.social.dialogues
    assert CARAVAN_DIALOGUE_ID in bundle.social.dialogues
    assert definitions[CARAVAN_QUEST_ID]["sequential_objectives"] is True


def test_caravan_quest_advances_one_mandatory_objective_at_a_time():
    service = _gameplay_service()
    service.talk_to_npc("hero", CARAVAN_NPC_ID, CARAVAN_DIALOGUE_ID)
    service.choose_dialogue("hero", CARAVAN_NPC_ID, CARAVAN_DIALOGUE_ID, "start", "accept_caravan_quest")
    quest = service.application.holder.current.quest_log.get(CARAVAN_QUEST_ID)

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
    report = service.choose_dialogue("hero", CARAVAN_NPC_ID, CARAVAN_DIALOGUE_ID, "start", "caravan_report")
    assert report.node_id == "report"


def test_caravan_sequential_flag_survives_quest_snapshot_round_trip():
    service = _gameplay_service()
    service.talk_to_npc("hero", CARAVAN_NPC_ID, CARAVAN_DIALOGUE_ID)
    service.choose_dialogue("hero", CARAVAN_NPC_ID, CARAVAN_DIALOGUE_ID, "start", "accept_caravan_quest")
    service.collect("forest_wood", "player", Quantity(2, ResourceUnit.ITEM))

    snapshot = QuestSnapshot.from_log(service.application.holder.current.quest_log)
    restored = QuestSnapshot.from_dict(snapshot.to_dict()).restore({})
    restored_quest = restored.get(CARAVAN_QUEST_ID)
    assert restored_quest.sequential_objectives is True
    assert restored_quest.objectives[0].progress == 2
    assert restored_quest.objectives[1].progress == 0


def test_carpenter_quest_collects_and_delivers_configured_resources_for_a_reward():
    service = _gameplay_service()
    service.talk_to_npc("hero", CARPENTER_NPC_ID, CARPENTER_DIALOGUE_ID)
    service.choose_dialogue("hero", CARPENTER_NPC_ID, CARPENTER_DIALOGUE_ID, "start", "accept_carpenter_quest")
    quest = service.application.holder.current.quest_log.get(CARPENTER_QUEST_ID)
    initial_balance = service.balance("hero", "gold").amount
    initial_experience = service.actor_character("hero").progression.experience

    service.collect("forest_wood", "player", Quantity(3, ResourceUnit.ITEM))
    assert quest.objectives[0].completed
    assert not quest.objectives[1].completed

    service.talk_to_npc("hero", CARPENTER_NPC_ID, CARPENTER_DIALOGUE_ID)
    service.choose_dialogue("hero", CARPENTER_NPC_ID, CARPENTER_DIALOGUE_ID, "start", "deliver_carpenter_wood")

    assert quest.state.value == "completed"
    assert service.balance("hero", "gold").amount == initial_balance + 12
    assert service.actor_character("hero").progression.experience == initial_experience + 35
