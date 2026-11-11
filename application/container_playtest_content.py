"""Temporary three-chest fixture for manual Container/Lock UI verification.

The fixture deliberately keeps all tools and keys inside the chests so the
player starts with an empty inventory and must progress through the sequence.
Remove this fixture after the Container/Lock playtest phase is complete.
"""

from types import MappingProxyType

from character import ItemDefinition
from core.entity import Entity, EntityType, Position as EntityPosition
from containers import ContainerDefinition, ContainerInstance
from locks import (
    KeyDefinition,
    LockDefinition,
    LockInstance,
    LockpickProfile,
)

# Keep the original public constants as aliases for the second (lockpick) chest.
PLAYTEST_CONTAINER_ID = "ui_playtest_lockpick_chest"
PLAYTEST_ENTITY_ID = "ui_playtest_lockpick_chest_entity"
PLAYTEST_LOCK_ID = "ui_playtest_lockpick_chest_lock"

UNLOCKED_CHEST_ID = "ui_playtest_unlocked_chest"
UNLOCKED_CHEST_ENTITY_ID = "ui_playtest_unlocked_chest_entity"
LOCKPICK_CHEST_ID = PLAYTEST_CONTAINER_ID
LOCKPICK_CHEST_ENTITY_ID = PLAYTEST_ENTITY_ID
KEYED_CHEST_ID = "ui_playtest_keyed_chest"
KEYED_CHEST_ENTITY_ID = "ui_playtest_keyed_chest_entity"

LOCKPICK_CHEST_LOCK_ID = PLAYTEST_LOCK_ID
KEYED_CHEST_LOCK_ID = "ui_playtest_keyed_chest_lock"
LOCKPICK_ITEM_ID = "ui_playtest_lockpick"
KEY_ITEM_ID = "ui_playtest_keyed_chest_key"


def _register_item_catalog(service) -> None:
    bundle = service.application.holder.current
    items = dict(bundle.items)
    definitions = (
        ItemDefinition(
            item_id=LOCKPICK_ITEM_ID,
            name="Maymuncuk",
            weight=0.2,
            volume_liters=0.1,
            description="Kilitleri açmak için kullanılan ince metal alet.",
            category="tool",
            tags=("tool", "lockpick"),
        ),
        ItemDefinition(
            item_id=KEY_ITEM_ID,
            name="Üçüncü Sandığın Anahtarı",
            weight=0.1,
            volume_liters=0.05,
            description="Üçüncü test sandığının kilidini açan özel anahtar.",
            category="key",
            tags=("key",),
        ),
    )
    changed = False
    for definition in definitions:
        if definition.item_id not in items:
            items[definition.item_id] = definition
            changed = True
    if changed:
        object.__setattr__(bundle, "items", MappingProxyType(items))
        for character in bundle.characters.values():
            character.bind_item_catalog(items)
        bundle.containers.bind_catalogs(items, bundle.resource_definitions)


def _ensure_chest_item(service, container_id: str, item_id: str) -> None:
    inventory = service.application.holder.current.containers.inventory(container_id)
    if inventory.item_quantity(item_id) == 0:
        service.application.holder.current.containers.add_item(container_id, item_id, 1)


def _register_chest(service, *, container_id, entity_id, name, position):
    world = service.application.aktif_dunya()
    entity = Entity(
        EntityType.ESYA,
        name,
        entity_id=entity_id,
        position=EntityPosition(*position),
    )
    service.application.holder.current.session.add_entity(entity, world.world_id)
    service.register_container_definition(
        ContainerDefinition(
            definition_id=f"{container_id}_definition",
            name=name,
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
            container_id=container_id,
            entity_id=entity_id,
            definition_id=f"{container_id}_definition",
        )
    )
    service.place_container(
        container_id,
        "village",
        position[0],
        position[1],
        blocks_movement=True,
        tags=("container", "playtest"),
    )


def register_container_playtest_fixture(service) -> str:
    """Place three sequentially testable chests in the village."""
    bundle = service.application.holder.current
    if bundle.containers.get(UNLOCKED_CHEST_ID) is not None:
        _register_item_catalog(service)
        _ensure_chest_item(service, UNLOCKED_CHEST_ID, LOCKPICK_ITEM_ID)
        _ensure_chest_item(service, LOCKPICK_CHEST_ID, KEY_ITEM_ID)
        return PLAYTEST_CONTAINER_ID

    world = service.application.aktif_dunya()
    if world is None:
        raise RuntimeError("An active world is required for the container playtest fixture.")

    _register_item_catalog(service)

    _register_chest(
        service,
        container_id=UNLOCKED_CHEST_ID,
        entity_id=UNLOCKED_CHEST_ENTITY_ID,
        name="Açık Sandık",
        position=(14, 28),
    )
    _register_chest(
        service,
        container_id=LOCKPICK_CHEST_ID,
        entity_id=LOCKPICK_CHEST_ENTITY_ID,
        name="Maymuncuklu Sandık",
        position=(16, 27),
    )
    _register_chest(
        service,
        container_id=KEYED_CHEST_ID,
        entity_id=KEYED_CHEST_ENTITY_ID,
        name="Anahtarlı Sandık",
        position=(18, 28),
    )

    service.register_lockpick_profile(
        LockpickProfile(
            profile_id="ui_playtest_lockpick",
            allowed_tool_tags=("lockpick",),
            require_skill=True,
            require_tool=True,
            minimum_skill=0,
            difficulty_class=10,
        )
    )
    service.register_lock_definition(
        LockDefinition(
            definition_id="ui_playtest_lockpick_lock_definition",
            name="Basit Demir Kilit",
            lockpick_profile_id="ui_playtest_lockpick",
        )
    )
    service.register_lock(
        LockInstance(
            lock_id=LOCKPICK_CHEST_LOCK_ID,
            entity_id=LOCKPICK_CHEST_ENTITY_ID,
            definition_id="ui_playtest_lockpick_lock_definition",
            locked=True,
        )
    )

    service.register_lock_definition(
        LockDefinition(
            definition_id="ui_playtest_keyed_lock_definition",
            name="Özel Anahtarlı Kilit",
            required_key_id=KEY_ITEM_ID,
        )
    )
    service.register_key_definition(
        KeyDefinition(
            key_id=KEY_ITEM_ID,
            name="Üçüncü Sandığın Anahtarı",
            lock_definition_id="ui_playtest_keyed_lock_definition",
        )
    )
    service.register_lock(
        LockInstance(
            lock_id=KEYED_CHEST_LOCK_ID,
            entity_id=KEYED_CHEST_ENTITY_ID,
            definition_id="ui_playtest_keyed_lock_definition",
            locked=True,
        )
    )

    _ensure_chest_item(service, UNLOCKED_CHEST_ID, LOCKPICK_ITEM_ID)
    _ensure_chest_item(service, LOCKPICK_CHEST_ID, KEY_ITEM_ID)
    return PLAYTEST_CONTAINER_ID


__all__ = [
    "PLAYTEST_CONTAINER_ID",
    "PLAYTEST_ENTITY_ID",
    "PLAYTEST_LOCK_ID",
    "UNLOCKED_CHEST_ID",
    "UNLOCKED_CHEST_ENTITY_ID",
    "LOCKPICK_CHEST_ID",
    "LOCKPICK_CHEST_ENTITY_ID",
    "KEYED_CHEST_ID",
    "KEYED_CHEST_ENTITY_ID",
    "LOCKPICK_CHEST_LOCK_ID",
    "KEYED_CHEST_LOCK_ID",
    "LOCKPICK_ITEM_ID",
    "KEY_ITEM_ID",
    "register_container_playtest_fixture",
]
