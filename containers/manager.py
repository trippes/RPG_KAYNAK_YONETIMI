"""Container registry, containment graph and capacity-safe content operations."""
from collections.abc import Mapping
from .definition import ContainerDefinition
from .instance import ContainerInstance
from .capacity import ContainerCapacityUsage, capacity_for
from .break_profiles import BreakProfileRegistry
from resources import Inventory, ResourceType


class ContainerManagerError(ValueError):
    """A container operation would violate a domain invariant."""


class ContainerManager:
    """Owns container instances and their separate content inventories."""

    def __init__(self, item_catalog=None, resource_catalog=None, break_profiles=None, max_global_nesting_depth=8):
        if item_catalog is not None and not isinstance(item_catalog, Mapping):
            raise TypeError("item_catalog must be a mapping.")
        if resource_catalog is not None and not isinstance(resource_catalog, Mapping):
            raise TypeError("resource_catalog must be a mapping.")
        self._definitions = {}
        self._instances = {}
        self._inventories = {}
        self._parents = {}
        self._item_catalog = dict(item_catalog or {})
        self._resource_catalog = dict(resource_catalog or {})
        self.break_profiles = break_profiles or BreakProfileRegistry()
        if not isinstance(self.break_profiles, BreakProfileRegistry):
            raise TypeError("break_profiles must be BreakProfileRegistry.")
        if isinstance(max_global_nesting_depth, bool) or not isinstance(max_global_nesting_depth, int) or max_global_nesting_depth < 1:
            raise ValueError("max_global_nesting_depth must be a positive integer.")
        self.max_global_nesting_depth = max_global_nesting_depth

    def bind_catalogs(self, item_catalog=None, resource_catalog=None):
        """Bind the authoritative physical metadata catalogs for this session."""
        if item_catalog is not None and not isinstance(item_catalog, Mapping):
            raise TypeError("item_catalog must be a mapping.")
        if resource_catalog is not None and not isinstance(resource_catalog, Mapping):
            raise TypeError("resource_catalog must be a mapping.")
        previous_items = self._item_catalog
        previous_resources = self._resource_catalog
        self._item_catalog = dict(item_catalog or {})
        self._resource_catalog = dict(resource_catalog or {})
        try:
            self.validate()
        except Exception:
            self._item_catalog = previous_items
            self._resource_catalog = previous_resources
            raise

    def all_inventories(self):
        """Return the distinct inventories owned by registered containers."""
        return tuple(self._inventories[key] for key in sorted(self._inventories))

    def register_definition(self, definition):
        if not isinstance(definition, ContainerDefinition):
            raise TypeError("definition must be ContainerDefinition.")
        if definition.definition_id in self._definitions:
            raise ContainerManagerError(f"Duplicate container definition: {definition.definition_id}")
        if definition.break_profile_id and self.break_profiles.get(definition.break_profile_id) is None:
            raise ContainerManagerError(f"Unknown break profile: {definition.break_profile_id}")
        self._definitions[definition.definition_id] = definition
        return definition

    def register(self, instance, inventory=None):
        if not isinstance(instance, ContainerInstance):
            raise TypeError("instance must be ContainerInstance.")
        if instance.container_id in self._instances:
            raise ContainerManagerError(f"Duplicate container instance: {instance.container_id}")
        definition = self._definitions.get(instance.definition_id)
        if definition is None:
            raise ContainerManagerError(f"Unknown container definition: {instance.definition_id}")
        if any(existing.entity_id == instance.entity_id for existing in self._instances.values()):
            raise ContainerManagerError(f"Entity already has a container capability: {instance.entity_id}")
        if inventory is None:
            inventory = Inventory()
        if not isinstance(inventory, Inventory):
            raise TypeError("inventory must be Inventory.")
        if any(existing is inventory for existing in self._inventories.values()):
            raise ContainerManagerError("An Inventory cannot be owned by multiple containers.")
        if definition.break_profile_id:
            profile = self.break_profiles.get(definition.break_profile_id)
            if instance.durability is None:
                instance.durability = profile.max_durability
            elif instance.durability > profile.max_durability:
                raise ContainerManagerError("Instance durability exceeds its break profile.")
        self._instances[instance.container_id] = instance
        self._inventories[instance.container_id] = inventory
        try:
            self._validate_capacity(instance.container_id)
        except Exception:
            del self._instances[instance.container_id]
            del self._inventories[instance.container_id]
            raise
        return instance

    def definition(self, definition_id):
        return self._definitions.get(definition_id)

    def get(self, container_id):
        return self._instances.get(container_id)

    def inventory(self, container_id):
        self._require(container_id)
        return self._inventories[container_id]

    def instances(self):
        return tuple(self._instances[key] for key in sorted(self._instances))

    def contain(self, parent_id, child_id):
        parent = self._require(parent_id)
        self._require(child_id)
        if parent_id == child_id:
            raise ContainerManagerError("A container cannot contain itself.")
        if child_id in self._parents:
            raise ContainerManagerError("Container already has a custody location.")
        if parent_id in self._descendants(child_id):
            raise ContainerManagerError("Containment would create a cycle.")
        parent_definition = self._definitions[parent.definition_id]
        child_definition = self._definitions[self._instances[child_id].definition_id]
        if not parent_definition.nesting_enabled or parent_definition.max_nesting_depth == 0:
            raise ContainerManagerError("This container does not allow nested containers.")
        child_tags = set(child_definition.container_tags)
        if set(parent_definition.denied_container_tags).intersection(child_tags):
            raise ContainerManagerError("Nested container is denied by tag policy.")
        if parent_definition.allowed_container_tags and not set(parent_definition.allowed_container_tags).intersection(child_tags):
            raise ContainerManagerError("Nested container does not satisfy allowed tags.")
        self._parents[child_id] = parent_id
        try:
            self._validate_nesting_chain(parent_id)
            self._validate_capacity_chain(parent_id)
        except Exception:
            del self._parents[child_id]
            raise
        return self._instances[child_id]

    def release(self, child_id):
        self._require(child_id)
        return self._parents.pop(child_id, None)

    def parent_of(self, container_id):
        self._require(container_id)
        parent_id = self._parents.get(container_id)
        return self._instances.get(parent_id) if parent_id else None

    def children_of(self, container_id):
        self._require(container_id)
        return tuple(self._instances[key] for key in sorted(self._parents) if self._parents[key] == container_id)

    def add_item(self, container_id, item_id, quantity=1):
        definition = self._require_definition(container_id)
        item = self._item_catalog.get(item_id)
        if item is None:
            raise ContainerManagerError(f"Missing item definition: {item_id}")
        self._check_tags(definition, item.tags, "item")
        inventory = self._inventories[container_id]
        before = inventory.item_snapshot()
        inventory.add_item(item_id, quantity)
        try:
            self._validate_capacity_chain(container_id)
        except Exception:
            inventory._restore_item_snapshot(before)
            raise
        return inventory.item_quantity(item_id)

    def remove_item(self, container_id, item_id, quantity=1):
        self.inventory(container_id).remove_item(item_id, quantity)

    def add_resource(self, container_id, resource_type, quantity):
        definition = self._require_definition(container_id)
        if not isinstance(resource_type, ResourceType):
            raise TypeError("resource_type must be ResourceType.")
        resource = self._resource_catalog.get(resource_type.value)
        if resource is None:
            raise ContainerManagerError(f"Missing resource definition: {resource_type.value}")
        self._check_tags(definition, resource.tags, "resource")
        inventory = self._inventories[container_id]
        before = inventory.snapshot()
        inventory.add(resource_type, quantity)
        try:
            self._validate_capacity_chain(container_id)
        except Exception:
            inventory._restore_snapshot(before)
            raise

    def remove_resource(self, container_id, resource_type, quantity):
        self.inventory(container_id).remove(resource_type, quantity)

    def usage(self, container_id):
        self._require(container_id)
        inventory = self._inventories[container_id]
        weight = inventory.total_weight(self._item_catalog, self._resource_catalog)
        volume = inventory.total_volume(self._item_catalog, self._resource_catalog)
        children = self.children_of(container_id)
        weight += sum(self._total_container_weight(child.container_id) for child in children)
        volume += sum(self._definitions[child.definition_id].outer_volume_liters for child in children)
        return ContainerCapacityUsage(weight, inventory.slot_count() + len(children), volume)

    def validate(self):
        for child_id, parent_id in self._parents.items():
            self._require(child_id)
            self._require(parent_id)
        for container_id in self._instances:
            self._validate_nesting(container_id)
            self._validate_capacity_chain(container_id)
        return True

    def _validate_capacity(self, container_id):
        instance = self._require(container_id)
        definition = self._definitions[instance.definition_id]
        usage = self.usage(container_id)
        if not capacity_for(definition).fits(usage):
            raise ContainerManagerError(
                f"Container capacity exceeded: {container_id} "
                f"(weight={usage.weight_kg}, slots={usage.slots}, volume={usage.volume_liters})."
            )

    def _validate_capacity_chain(self, container_id):
        current = container_id
        while current is not None:
            self._validate_capacity(current)
            current = self._parents.get(current)

    def _validate_nesting_chain(self, container_id):
        current = container_id
        while self._parents.get(current) is not None:
            current = self._parents[current]
        self._validate_nesting(current)

    def _validate_nesting(self, container_id):
        definition = self._definitions[self._instances[container_id].definition_id]
        descendants = self._descendants(container_id)
        max_relative_depth = max((self._relative_depth(container_id, child) for child in descendants), default=0)
        if max_relative_depth > definition.max_nesting_depth:
            raise ContainerManagerError("Container nesting depth exceeds its definition.")
        if self._relative_depth_from_root(container_id) + max_relative_depth > self.max_global_nesting_depth:
            raise ContainerManagerError("Global container nesting depth exceeded.")
        for child in self.children_of(container_id):
            self._validate_nesting(child.container_id)

    def _relative_depth(self, ancestor_id, descendant_id):
        depth = 0
        current = descendant_id
        while current != ancestor_id:
            current = self._parents.get(current)
            if current is None:
                raise ContainerManagerError("Invalid containment graph.")
            depth += 1
        return depth

    def _relative_depth_from_root(self, container_id):
        return self._depth(container_id)

    def _depth(self, container_id):
        depth = 0
        seen = set()
        current = container_id
        while current in self._parents:
            if current in seen:
                raise ContainerManagerError("Containment cycle detected.")
            seen.add(current)
            current = self._parents[current]
            depth += 1
        return depth

    def _descendants(self, container_id):
        result = set()
        pending = [container_id]
        while pending:
            current = pending.pop()
            for child_id, parent_id in self._parents.items():
                if parent_id == current and child_id not in result:
                    result.add(child_id)
                    pending.append(child_id)
        return result

    def _total_container_weight(self, container_id):
        instance = self._instances[container_id]
        definition = self._definitions[instance.definition_id]
        return definition.empty_weight_kg + self.usage(container_id).weight_kg

    @staticmethod
    def _check_tags(definition, tags, kind):
        tags = set(tags)
        allowed = set(definition.allowed_item_tags if kind == "item" else definition.allowed_resource_tags)
        denied = set(definition.denied_item_tags if kind == "item" else definition.denied_resource_tags)
        if denied.intersection(tags):
            raise ContainerManagerError(f"{kind.title()} denied by container tag policy.")
        if allowed and not allowed.intersection(tags):
            raise ContainerManagerError(f"{kind.title()} does not satisfy container allowed tags.")

    def _require(self, container_id):
        instance = self._instances.get(container_id)
        if instance is None:
            raise KeyError(f"Container not found: {container_id}")
        return instance

    def _require_definition(self, container_id):
        instance = self._require(container_id)
        return self._definitions[instance.definition_id]
