"""Versioned persistence for container definitions, instances and custody."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from character import EquipmentSlot, ItemDefinition
from resources import Inventory, Quantity, ResourceDefinition, ResourceType, ResourceUnit
from .world_object_placement import WorldObjectPlacement
from containers import (
    BreakProfile, BreakProfileRegistry, ContainerDefinition, ContainerInstance,
    ContainerManager, ContainerManagerError,
)

CONTAINER_SCHEMA = "rpg-containers"
CONTAINER_SCHEMA_VERSION = 1


class ContainerPersistenceError(ValueError):
    """Invalid container snapshot or restore input."""


@dataclass(frozen=True)
class ContainerSnapshot:
    """Runtime-free container state with all physical metadata required to restore it."""

    data: Mapping[str, object]

    @classmethod
    def from_runtime(cls, manager, placements, item_catalog, resource_catalog):
        if not isinstance(manager, ContainerManager):
            raise TypeError("manager must be ContainerManager.")
        if not isinstance(item_catalog, Mapping) or not isinstance(resource_catalog, Mapping):
            raise TypeError("Physical catalogs must be mappings.")
        manager.validate()
        instances = manager.instances()
        if not instances:
            raise ContainerPersistenceError("An empty container registry has no snapshot.")

        definitions = {}
        profiles = {}
        item_ids = set()
        resource_ids = set()
        instance_records = []
        inventory_records = []
        parent_records = []
        custody_records = []
        placement_records = []

        for instance in instances:
            definition = manager.definition(instance.definition_id)
            if definition is None:
                raise ContainerPersistenceError("Container instance references an unknown definition.")
            definitions[definition.definition_id] = _definition_to_dict(definition)
            if definition.break_profile_id:
                profile = manager.break_profiles.get(definition.break_profile_id)
                if profile is None:
                    raise ContainerPersistenceError("Container definition references an unknown break profile.")
                profiles[profile.profile_id] = {
                    "profile_id": profile.profile_id,
                    "max_durability": profile.max_durability,
                    "damage_resistances": dict(profile.damage_resistances),
                    "breakable": profile.breakable,
                }

            inventory = manager.inventory(instance.container_id)
            item_stacks = list(inventory.item_snapshot())
            stocks = [
                {"resource_id": resource.value, "value": quantity.value, "unit": quantity.unit.value}
                for resource, quantity in inventory.snapshot()
            ]
            item_ids.update(item_id for item_id, _ in item_stacks)
            resource_ids.update(record["resource_id"] for record in stocks)
            instance_records.append({
                "container_id": instance.container_id,
                "entity_id": instance.entity_id,
                "definition_id": instance.definition_id,
                "durability": instance.durability,
                "broken": instance.broken,
            })
            inventory_records.append({
                "container_id": instance.container_id,
                "items": [{"item_id": item_id, "quantity": quantity} for item_id, quantity in item_stacks],
                "resources": stocks,
            })
            parent = manager.parent_of(instance.container_id)
            if parent is not None:
                parent_records.append({"container_id": instance.container_id, "parent_id": parent.container_id})
            owner = manager.inventory_custody(instance.container_id)
            if owner is not None:
                custody_records.append({"container_id": instance.container_id, "inventory_id": owner})
            placement = placements.get(instance.entity_id)
            if placement is not None:
                placement_records.append(_placement_to_dict(placement))

        missing_items = item_ids - set(item_catalog)
        missing_resources = resource_ids - set(resource_catalog)
        if missing_items or missing_resources:
            raise ContainerPersistenceError(
                f"Container contents reference missing physical definitions: items={sorted(missing_items)}, resources={sorted(missing_resources)}"
            )

        payload = {
            "schema": CONTAINER_SCHEMA,
            "schema_version": CONTAINER_SCHEMA_VERSION,
            "definitions": [definitions[key] for key in sorted(definitions)],
            "break_profiles": [profiles[key] for key in sorted(profiles)],
            "instances": sorted(instance_records, key=lambda value: value["container_id"]),
            "inventories": sorted(inventory_records, key=lambda value: value["container_id"]),
            "parents": sorted(parent_records, key=lambda value: value["container_id"]),
            "custodies": sorted(custody_records, key=lambda value: value["container_id"]),
            "placements": sorted(placement_records, key=lambda value: value["object_id"]),
            "item_catalog": [_item_to_dict(item_catalog[key]) for key in sorted(item_ids)],
            "resource_catalog": [_resource_to_dict(resource_catalog[key]) for key in sorted(resource_ids)],
        }
        return cls(payload)

    def to_dict(self):
        return _copy_json_value(dict(self.data))

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping):
            raise ContainerPersistenceError("Container snapshot must be an object.")
        expected = {
            "schema", "schema_version", "definitions", "break_profiles", "instances",
            "inventories", "parents", "custodies", "placements", "item_catalog", "resource_catalog",
        }
        if set(data) != expected:
            raise ContainerPersistenceError("Container snapshot has missing or unknown fields.")
        if data.get("schema") != CONTAINER_SCHEMA or data.get("schema_version") != CONTAINER_SCHEMA_VERSION:
            raise ContainerPersistenceError("Unsupported container persistence schema.")
        for key in expected - {"schema", "schema_version"}:
            if not isinstance(data[key], list):
                raise ContainerPersistenceError(f"{key} must be a list.")
        try:
            snapshot = cls(_copy_json_value(dict(data)))
            snapshot._validate_records()
            return snapshot
        except (KeyError, TypeError, ValueError) as error:
            if isinstance(error, ContainerPersistenceError):
                raise
            raise ContainerPersistenceError("Invalid container snapshot record.") from error

    def _validate_records(self):
        _unique(self.data["definitions"], "definition_id")
        _unique(self.data["break_profiles"], "profile_id")
        _unique(self.data["instances"], "container_id")
        _unique(self.data["inventories"], "container_id")
        _unique(self.data["parents"], "container_id")
        _unique(self.data["custodies"], "container_id")
        _unique(self.data["placements"], "object_id")
        _unique(self.data["item_catalog"], "item_id")
        _unique(self.data["resource_catalog"], "resource_id")
        instance_ids = {record["container_id"] for record in self.data["instances"]}
        if {record["container_id"] for record in self.data["inventories"]} != instance_ids:
            raise ContainerPersistenceError("Every container must have exactly one content inventory.")
        if any(record["container_id"] not in instance_ids for key in ("parents", "custodies", "inventories") for record in self.data[key]):
            raise ContainerPersistenceError("Container relationship references an unknown instance.")
        if set(record["container_id"] for record in self.data["parents"]) & set(record["container_id"] for record in self.data["custodies"]):
            raise ContainerPersistenceError("A container cannot be nested and inventory-held simultaneously.")
        entity_ids = {record["entity_id"] for record in self.data["instances"]}
        if any(record["object_id"] not in entity_ids for record in self.data["placements"]):
            raise ContainerPersistenceError("Placement references an unknown container entity.")
        definitions = {record["definition_id"] for record in self.data["definitions"]}
        if any(record["definition_id"] not in definitions for record in self.data["instances"]):
            raise ContainerPersistenceError("Instance references an unknown definition.")
        known_profiles = {record["profile_id"] for record in self.data["break_profiles"]}
        if any(record.get("break_profile_id") not in (None, *known_profiles) for record in self.data["definitions"]):
            raise ContainerPersistenceError("Definition references an unknown break profile.")

    def restore(self):
        self._validate_records()
        try:
            item_catalog = {item.item_id: item for item in (_item_from_dict(value) for value in self.data["item_catalog"])}
            resource_catalog = {item.resource_id: item for item in (_resource_from_dict(value) for value in self.data["resource_catalog"])}
            profiles = BreakProfileRegistry(
                BreakProfile(value["profile_id"], value["max_durability"], value.get("damage_resistances", {}), value.get("breakable", True))
                for value in self.data["break_profiles"]
            )
            manager = ContainerManager(item_catalog, resource_catalog, profiles)
            for value in self.data["definitions"]:
                manager.register_definition(_definition_from_dict(value))
            inventory_records = {value["container_id"]: value for value in self.data["inventories"]}
            for value in self.data["instances"]:
                inventory = Inventory()
                record = inventory_records[value["container_id"]]
                for item in record["items"]:
                    inventory.add_item(item["item_id"], item["quantity"])
                for resource in record["resources"]:
                    inventory.add(ResourceType(resource["resource_id"]), Quantity(resource["value"], ResourceUnit(resource["unit"])))
                manager.register(ContainerInstance(
                    value["container_id"], value["entity_id"], value["definition_id"],
                    value.get("durability"), value.get("broken", False),
                ), inventory)
            for value in self.data["parents"]:
                manager.contain(value["parent_id"], value["container_id"])
            for value in self.data["custodies"]:
                manager.set_inventory_custody(value["container_id"], value["inventory_id"])
            manager.validate()
            placements = tuple(_placement_from_dict(value) for value in self.data["placements"])
            return manager, item_catalog, resource_catalog, placements
        except (KeyError, TypeError, ValueError, ContainerManagerError) as error:
            if isinstance(error, ContainerPersistenceError):
                raise
            raise ContainerPersistenceError("Container state could not be restored safely.") from error


def _unique(records, key):
    values = [record.get(key) for record in records]
    if any(not isinstance(value, str) or not value.strip() for value in values) or len(values) != len(set(values)):
        raise ContainerPersistenceError(f"Invalid or duplicate {key} values.")


def _definition_to_dict(value):
    return {
        "definition_id": value.definition_id, "name": value.name,
        "empty_weight_kg": value.empty_weight_kg, "outer_volume_liters": value.outer_volume_liters,
        "max_contents_weight_kg": value.max_contents_weight_kg, "max_slots": value.max_slots,
        "max_contents_volume_liters": value.max_contents_volume_liters,
        "nesting_enabled": value.nesting_enabled, "max_nesting_depth": value.max_nesting_depth,
        "allowed_item_tags": list(value.allowed_item_tags), "denied_item_tags": list(value.denied_item_tags),
        "allowed_resource_tags": list(value.allowed_resource_tags), "denied_resource_tags": list(value.denied_resource_tags),
        "allowed_container_tags": list(value.allowed_container_tags), "denied_container_tags": list(value.denied_container_tags),
        "container_tags": list(value.container_tags), "break_profile_id": value.break_profile_id,
    }


def _definition_from_dict(value):
    return ContainerDefinition(**value)


def _item_to_dict(value):
    return {
        "item_id": value.item_id, "name": value.name, "slot": value.slot.value if value.slot else None,
        "weight": value.weight, "attack": value.attack, "defense": value.defense, "damage": value.damage,
        "max_hit_points": value.max_hit_points, "attribute_bonuses": dict(value.attribute_bonuses),
        "description": value.description, "volume_liters": value.volume_liters,
        "category": value.category, "tags": list(value.tags),
    }


def _item_from_dict(value):
    return ItemDefinition(
        value["item_id"], value["name"], EquipmentSlot(value["slot"]) if value.get("slot") else None,
        value.get("weight", 0.0), value.get("attack", 0), value.get("defense", 0), value.get("damage", 0),
        value.get("max_hit_points", 0), value.get("attribute_bonuses", {}), value.get("description", ""),
        value.get("volume_liters", 0.0), value.get("category", "misc"), tuple(value.get("tags", ())),
    )


def _resource_to_dict(value):
    return {
        "resource_id": value.resource_id, "name": value.name, "unit": value.unit.value,
        "weight_kg_per_unit": value.weight_kg_per_unit, "volume_liters_per_unit": value.volume_liters_per_unit,
        "category": value.category, "tags": list(value.tags),
    }


def _resource_from_dict(value):
    return ResourceDefinition(
        value["resource_id"], value["name"], ResourceUnit(value["unit"]),
        value.get("weight_kg_per_unit", 0.0), value.get("volume_liters_per_unit", 0.0),
        value.get("category", "misc"), tuple(value.get("tags", ())),
    )


def _placement_to_dict(value):
    return {
        "object_id": value.object_id, "world_id": value.world_id, "location_id": value.location_id,
        "x": value.x, "y": value.y, "width": value.width, "height": value.height,
        "blocks_movement": value.blocks_movement, "layer": value.layer, "tags": list(value.tags),
    }


def _placement_from_dict(value):
    return WorldObjectPlacement(**value)


def _copy_json_value(value):
    if isinstance(value, Mapping):
        return {str(key): _copy_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_copy_json_value(item) for item in value]
    return value


__all__ = ["CONTAINER_SCHEMA", "CONTAINER_SCHEMA_VERSION", "ContainerPersistenceError", "ContainerSnapshot"]
