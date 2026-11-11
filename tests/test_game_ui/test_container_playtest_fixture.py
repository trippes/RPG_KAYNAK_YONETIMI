from application.container_playtest_content import (
    KEYED_CHEST_ID,
    KEYED_CHEST_ENTITY_ID,
    KEYED_CHEST_LOCK_ID,
    KEY_ITEM_ID,
    LOCKPICK_CHEST_ID,
    LOCKPICK_CHEST_ENTITY_ID,
    LOCKPICK_CHEST_LOCK_ID,
    LOCKPICK_ITEM_ID,
    UNLOCKED_CHEST_ID,
    UNLOCKED_CHEST_ENTITY_ID,
    register_container_playtest_fixture,
)
from application.content_pack import populate_gameplay_resources, populate_opening_content
from application.game_application import GameApplication


def test_playtest_fixture_registers_three_chests_and_keeps_tools_out_of_player_inventory():
    application = GameApplication.create_default()
    service, _ids = populate_opening_content(application)
    populate_gameplay_resources(service)

    result = register_container_playtest_fixture(service)

    assert result == LOCKPICK_CHEST_ID
    assert service.container_for_entity(UNLOCKED_CHEST_ENTITY_ID) == UNLOCKED_CHEST_ID
    assert service.container_for_entity(LOCKPICK_CHEST_ENTITY_ID) == LOCKPICK_CHEST_ID
    assert service.container_for_entity(KEYED_CHEST_ENTITY_ID) == KEYED_CHEST_ID

    player_inventory = service.inventory("player")
    assert player_inventory.item_quantity(LOCKPICK_ITEM_ID) == 0
    assert player_inventory.item_quantity(KEY_ITEM_ID) == 0

    unlocked = service.container_state(UNLOCKED_CHEST_ID)
    assert unlocked.name == "Açık Sandık"
    assert unlocked.items == ((LOCKPICK_ITEM_ID, 1),)
    assert service.container_lock_state(UNLOCKED_CHEST_ID) is None

    lockpick_chest = service.container_state(LOCKPICK_CHEST_ID)
    assert lockpick_chest.name == "Maymuncuklu Sandık"
    assert lockpick_chest.items == ((KEY_ITEM_ID, 1),)
    lockpick_lock = service.container_lock_state(LOCKPICK_CHEST_ID)
    assert lockpick_lock is not None
    assert lockpick_lock.lock_id == LOCKPICK_CHEST_LOCK_ID
    assert lockpick_lock.locked is True
    assert lockpick_lock.lockpick_requires_tool is True
    assert lockpick_lock.lockpick_allowed_tool_tags == ("lockpick",)

    keyed_lock = service.container_lock_state(KEYED_CHEST_ID)
    assert keyed_lock is not None
    assert keyed_lock.lock_id == KEYED_CHEST_LOCK_ID
    assert keyed_lock.locked is True
    assert keyed_lock.required_key_id == KEY_ITEM_ID

    lockpick = service.item(LOCKPICK_ITEM_ID)
    key = service.item(KEY_ITEM_ID)
    assert lockpick is not None and {"tool", "lockpick"}.issubset(lockpick.tags)
    assert key is not None and "key" in key.tags

    placements = service.world_objects_for_location("demo_valley", "village")
    positions = {
        item.object_id: (item.x, item.y)
        for item in placements
        if item.object_id in {
            UNLOCKED_CHEST_ENTITY_ID,
            LOCKPICK_CHEST_ENTITY_ID,
            KEYED_CHEST_ENTITY_ID,
        }
    }
    assert positions == {
        UNLOCKED_CHEST_ENTITY_ID: (14, 28),
        LOCKPICK_CHEST_ENTITY_ID: (16, 27),
        KEYED_CHEST_ENTITY_ID: (18, 28),
    }


def test_playtest_fixture_registration_is_idempotent_and_keeps_one_copy_of_each_item():
    application = GameApplication.create_default()
    service, _ids = populate_opening_content(application)

    first = register_container_playtest_fixture(service)
    second = register_container_playtest_fixture(service)

    assert first == second == LOCKPICK_CHEST_ID
    assert service.container_state(UNLOCKED_CHEST_ID).items == ((LOCKPICK_ITEM_ID, 1),)
    assert service.container_state(LOCKPICK_CHEST_ID).items == ((KEY_ITEM_ID, 1),)
    assert service.container_state(KEYED_CHEST_ID).items == ()
    assert len([
        item for item in service.world_objects_for_location("demo_valley", "village")
        if item.object_id in {
            UNLOCKED_CHEST_ENTITY_ID,
            LOCKPICK_CHEST_ENTITY_ID,
            KEYED_CHEST_ENTITY_ID,
        }
    ]) == 3
