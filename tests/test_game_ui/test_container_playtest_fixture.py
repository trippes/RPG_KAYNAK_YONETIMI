from application.container_playtest_content import (
    PLAYTEST_CONTAINER_ID,
    PLAYTEST_ENTITY_ID,
    PLAYTEST_LOCK_ID,
    register_container_playtest_fixture,
)
from application.content_pack import populate_opening_content
from application.game_application import GameApplication


def test_playtest_fixture_registers_a_locked_world_container():
    application = GameApplication.create_default()
    service, _ids = populate_opening_content(application)

    container_id = register_container_playtest_fixture(service)

    assert container_id == PLAYTEST_CONTAINER_ID
    assert service.container_for_entity(PLAYTEST_ENTITY_ID) == PLAYTEST_CONTAINER_ID

    container = service.container_state(PLAYTEST_CONTAINER_ID)
    assert container.name == "Kilitli Test Sandığı"

    lock = service.container_lock_state(PLAYTEST_CONTAINER_ID)
    assert lock is not None
    assert lock.lock_id == PLAYTEST_LOCK_ID
    assert lock.locked is True
    assert lock.lockpick_profile_id == "ui_playtest_lockpick"
    assert lock.force_profile_id == "ui_playtest_force"

    placements = service.world_objects_for_location("demo_valley", "village")
    placement = next(item for item in placements if item.object_id == PLAYTEST_ENTITY_ID)
    assert (placement.x, placement.y) == (15, 28)


def test_playtest_fixture_registration_is_idempotent():
    application = GameApplication.create_default()
    service, _ids = populate_opening_content(application)

    first = register_container_playtest_fixture(service)
    second = register_container_playtest_fixture(service)

    assert first == second == PLAYTEST_CONTAINER_ID
    assert len([
        item for item in service.world_objects_for_location("demo_valley", "village")
        if item.object_id == PLAYTEST_ENTITY_ID
    ]) == 1
