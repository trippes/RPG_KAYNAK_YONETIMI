"""Temporary in-game fixture for manual Container/Lock UI verification.

Remove this fixture after the Container UI playtest phase is complete.
"""

from core.entity import Entity, EntityType, Position as EntityPosition
from containers import ContainerDefinition, ContainerInstance
from locks import (
    ForceProfile,
    LockDefinition,
    LockInstance,
    LockpickProfile,
)


PLAYTEST_CONTAINER_ID = "ui_playtest_locked_chest"
PLAYTEST_ENTITY_ID = "ui_playtest_chest_entity"
PLAYTEST_LOCK_ID = "ui_playtest_chest_lock"


def register_container_playtest_fixture(service) -> str:
    """Place one locked test chest beside the player's village starting tile."""
    bundle = service.application.holder.current
    existing = bundle.containers.get(PLAYTEST_CONTAINER_ID)
    if existing is not None:
        return PLAYTEST_CONTAINER_ID

    world = service.application.aktif_dunya()
    if world is None:
        raise RuntimeError("An active world is required for the container playtest fixture.")

    entity = Entity(
        EntityType.ESYA,
        "Sandık (Test)",
        entity_id=PLAYTEST_ENTITY_ID,
        position=EntityPosition(15, 28),
    )
    bundle.session.add_entity(entity, world.world_id)

    service.register_container_definition(
        ContainerDefinition(
            definition_id="ui_playtest_chest_definition",
            name="Kilitli Test Sandığı",
            empty_weight_kg=8.0,
            outer_volume_liters=24.0,
            max_contents_weight_kg=20.0,
            max_slots=8,
            max_contents_volume_liters=18.0,
            nesting_enabled=False,
        )
    )
    service.register_container(
        ContainerInstance(
            container_id=PLAYTEST_CONTAINER_ID,
            entity_id=PLAYTEST_ENTITY_ID,
            definition_id="ui_playtest_chest_definition",
        )
    )

    service.register_lockpick_profile(
        LockpickProfile(
            profile_id="ui_playtest_lockpick",
            require_skill=True,
            require_tool=False,
            minimum_skill=0,
            difficulty_class=10,
        )
    )
    service.register_force_profile(
        ForceProfile(
            profile_id="ui_playtest_force",
            allowed=True,
            minimum_strength=0,
            difficulty_class=10,
        )
    )
    service.register_lock_definition(
        LockDefinition(
            definition_id="ui_playtest_chest_lock_definition",
            name="Basit Demir Kilit",
            lockpick_profile_id="ui_playtest_lockpick",
            force_profile_id="ui_playtest_force",
        )
    )
    service.register_lock(
        LockInstance(
            lock_id=PLAYTEST_LOCK_ID,
            entity_id=PLAYTEST_ENTITY_ID,
            definition_id="ui_playtest_chest_lock_definition",
            locked=True,
        )
    )
    service.place_container(
        PLAYTEST_CONTAINER_ID,
        "village",
        15,
        28,
        blocks_movement=True,
        tags=("container", "playtest"),
    )
    return PLAYTEST_CONTAINER_ID


__all__ = [
    "PLAYTEST_CONTAINER_ID",
    "PLAYTEST_ENTITY_ID",
    "PLAYTEST_LOCK_ID",
    "register_container_playtest_fixture",
]
