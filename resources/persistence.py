"""Canonical gameplay snapshots, JSON codec and isolated file adapter."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from core.simulation import SimulationRuntime
from core.time import Tick

from .gathering import WorldResourceNodeManager
from .inventory import Inventory
from .jobs import ProductionJobManager, ProductionJobState, production_action_id
from .node import WorldResourceNode
from .recipe import Recipe
from .resource import Quantity, ResourceType, ResourceUnit


GAMEPLAY_SCHEMA = "rpg-gameplay"
GAMEPLAY_SCHEMA_VERSION = 1


class GameplayPersistenceError(ValueError):
    """Invalid gameplay snapshot or restore input."""


class GameplayFileError(OSError):
    """Gameplay snapshot filesystem failure."""


@dataclass(frozen=True)
class InventoryRecord:
    inventory_id: str
    stocks: tuple[tuple[str, int, str], ...]


@dataclass(frozen=True)
class NodeRecord:
    node_id: str
    world_id: str
    resource_type: str
    quantity: tuple[int, str]
    capacity: tuple[int, str]
    regeneration_rate: tuple[int, str]
    last_simulation_tick: int
    location_id: str | None = None


@dataclass(frozen=True)
class RecipeRecord:
    recipe_id: str
    inputs: tuple[tuple[str, int, str], ...]
    outputs: tuple[tuple[str, int, str], ...]
    processing_time: int = 1
    facility_type: str | None = None
    required_capabilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    recipe_id: str
    inventory_id: str
    state: str
    start_tick: int
    duration: int
    end_tick: int
    action_id: str
    inputs_refunded: bool


@dataclass(frozen=True)
class GameplaySnapshot:
    """Runtime-free, deterministic gameplay state."""

    simulation_tick: int
    inventories: tuple[InventoryRecord, ...]
    nodes: tuple[NodeRecord, ...]
    recipes: tuple[RecipeRecord, ...]
    jobs: tuple[JobRecord, ...]

    @classmethod
    def from_runtime(
        cls,
        inventories: Mapping[str, Inventory],
        node_manager: WorldResourceNodeManager,
        job_manager: ProductionJobManager,
        recipes: Mapping[str, Recipe] | None = None,
    ) -> "GameplaySnapshot":
        if not isinstance(inventories, Mapping):
            raise TypeError("inventories must be a mapping of stable IDs to Inventory.")
        if not isinstance(node_manager, WorldResourceNodeManager):
            raise TypeError("node_manager must be WorldResourceNodeManager.")
        node_manager.validate_world_references()
        if not isinstance(job_manager, ProductionJobManager):
            raise TypeError("job_manager must be ProductionJobManager.")
        if recipes is not None and not isinstance(recipes, Mapping):
            raise TypeError("recipes must be a mapping of stable IDs to Recipe.")

        inventory_records: list[InventoryRecord] = []
        inventory_ids: dict[int, str] = {}
        for inventory_id, inventory in inventories.items():
            _validate_id(inventory_id, "inventory_id")
            if not isinstance(inventory, Inventory):
                raise TypeError("inventory values must be Inventory.")
            if inventory_id in {record.inventory_id for record in inventory_records}:
                raise GameplayPersistenceError(f"Duplicate inventory ID: {inventory_id}")
            if id(inventory) in inventory_ids:
                raise GameplayPersistenceError(
                    "The same Inventory cannot be registered under multiple IDs."
                )
            inventory_ids[id(inventory)] = inventory_id
            stocks = tuple(
                (resource.value, quantity.value, quantity.unit.value)
                for resource, quantity in inventory.snapshot()
            )
            inventory_records.append(InventoryRecord(inventory_id, stocks))

        node_records = [
            _node_record(node)
            for node in node_manager.nodes()
        ]
        recipe_records: dict[str, RecipeRecord] = {}
        if recipes is not None:
            for recipe_id, recipe in recipes.items():
                _validate_id(recipe_id, "recipe_id")
                if not isinstance(recipe, Recipe):
                    raise TypeError("recipe values must be Recipe.")
                if recipe.recipe_id != recipe_id:
                    raise GameplayPersistenceError(
                        f"Recipe registry key must match recipe ID: {recipe_id}"
                    )
                recipe_records[recipe_id] = _recipe_record(recipe)
        job_records: list[JobRecord] = []
        for job in job_manager.jobs():
            inventory_id = inventory_ids.get(id(job.inventory))
            if inventory_id is None:
                raise GameplayPersistenceError(
                    f"Job {job.job_id} references an unregistered inventory."
                )
            recipe_records[job.recipe.recipe_id] = _recipe_record(job.recipe)
            if job.state in {ProductionJobState.PLANNED, ProductionJobState.RUNNING} and job.end_tick.value <= job_manager.runtime.current_tick.value:
                raise GameplayPersistenceError(
                    f"Active job has no future completion tick: {job.job_id}"
                )
            job_records.append(JobRecord(
                job.job_id,
                job.recipe.recipe_id,
                inventory_id,
                job.state.value,
                job.start_tick.value,
                job.duration.value,
                job.end_tick.value,
                str(job.action_id),
                job.inputs_refunded,
            ))

        return cls(
            simulation_tick=job_manager.runtime.current_tick.value,
            inventories=tuple(sorted(inventory_records, key=lambda record: record.inventory_id)),
            nodes=tuple(sorted(node_records, key=lambda record: record.node_id)),
            recipes=tuple(sorted(recipe_records.values(), key=lambda record: record.recipe_id)),
            jobs=tuple(sorted(job_records, key=lambda record: record.job_id)),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": GAMEPLAY_SCHEMA,
            "schema_version": GAMEPLAY_SCHEMA_VERSION,
            "simulation_tick": self.simulation_tick,
            "inventories": [
                {"inventory_id": record.inventory_id, "stocks": [
                    {"resource_type": resource, "value": value, "unit": unit}
                    for resource, value, unit in record.stocks
                ]}
                for record in self.inventories
            ],
            "nodes": [
                {
                    "node_id": record.node_id,
                    "world_id": record.world_id,
                    "resource_type": record.resource_type,
                    "quantity": _quantity_dict(record.quantity),
                    "capacity": _quantity_dict(record.capacity),
                    "regeneration_rate": _quantity_dict(record.regeneration_rate),
                    "last_simulation_tick": record.last_simulation_tick,
                    "location_id": record.location_id,
                }
                for record in self.nodes
            ],
            "recipes": [_recipe_dict(record) for record in self.recipes],
            "jobs": [
                {
                    "job_id": record.job_id,
                    "recipe_id": record.recipe_id,
                    "inventory_id": record.inventory_id,
                    "state": record.state,
                    "start_tick": record.start_tick,
                    "duration": record.duration,
                    "end_tick": record.end_tick,
                    "action_id": record.action_id,
                    "inputs_refunded": record.inputs_refunded,
                }
                for record in self.jobs
            ],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "GameplaySnapshot":
        if not isinstance(data, Mapping):
            raise GameplayPersistenceError("Gameplay snapshot must be an object.")
        if data.get("schema") != GAMEPLAY_SCHEMA:
            raise GameplayPersistenceError("Unknown gameplay persistence schema.")
        if data.get("schema_version") != GAMEPLAY_SCHEMA_VERSION:
            raise GameplayPersistenceError("Unsupported gameplay schema version.")
        simulation_tick = _non_negative_int(data.get("simulation_tick"), "simulation_tick")
        inventories = tuple(_inventory_record(item) for item in _list(data, "inventories"))
        nodes = tuple(_node_record_from_dict(item) for item in _list(data, "nodes"))
        recipes = tuple(_recipe_record_from_dict(item) for item in _list(data, "recipes"))
        jobs = tuple(_job_record(item) for item in _list(data, "jobs"))
        _unique((record.inventory_id for record in inventories), "inventory")
        _unique((record.node_id for record in nodes), "node")
        _unique((record.recipe_id for record in recipes), "recipe")
        _unique((record.job_id for record in jobs), "job")
        _unique((record.action_id for record in jobs), "action")
        recipe_ids = {record.recipe_id for record in recipes}
        inventory_ids = {record.inventory_id for record in inventories}
        for job in jobs:
            if job.recipe_id not in recipe_ids:
                raise GameplayPersistenceError(f"Unknown recipe reference: {job.recipe_id}")
            if job.inventory_id not in inventory_ids:
                raise GameplayPersistenceError(f"Unknown inventory reference: {job.inventory_id}")
            if job.start_tick > simulation_tick:
                raise GameplayPersistenceError("Production job starts after snapshot tick.")
            if job.end_tick < job.start_tick or job.end_tick != job.start_tick + job.duration or job.duration <= 0:
                raise GameplayPersistenceError("Inconsistent production job ticks.")
            try:
                job_state = ProductionJobState(job.state)
            except ValueError as error:
                raise GameplayPersistenceError(f"Unknown production job state: {job.state}") from error
            expected_action_id = str(production_action_id(job.job_id))
            if job.action_id != expected_action_id:
                raise GameplayPersistenceError(
                    f"Inconsistent production job action ID: expected {expected_action_id}"
                )
            if job_state in {ProductionJobState.PLANNED, ProductionJobState.RUNNING} and simulation_tick > job.end_tick:
                raise GameplayPersistenceError("Active production job has no future completion tick.")
        for node in nodes:
            if not (node.quantity[1] == node.capacity[1] == node.regeneration_rate[1]):
                raise GameplayPersistenceError("Node quantities must use one resource unit.")
            if node.quantity[0] > node.capacity[0]:
                raise GameplayPersistenceError("Node quantity exceeds capacity.")
        return cls(
            simulation_tick=simulation_tick,
            inventories=tuple(sorted(inventories, key=lambda record: record.inventory_id)),
            nodes=tuple(sorted(nodes, key=lambda record: record.node_id)),
            recipes=tuple(sorted(recipes, key=lambda record: record.recipe_id)),
            jobs=tuple(sorted(jobs, key=lambda record: record.job_id)),
        )

    def restore(
        self,
        runtime: SimulationRuntime | None = None,
    ) -> "RestoredGameplayState":
        """Construct a complete new gameplay runtime graph before returning it."""
        if runtime is not None:
            if not isinstance(runtime, SimulationRuntime):
                raise TypeError("runtime must be SimulationRuntime.")
            if runtime.current_tick.value != self.simulation_tick:
                raise GameplayPersistenceError(
                    "Gameplay snapshot tick does not match the supplied runtime tick."
                )

            for record in self.jobs:
                if record.state in {
                    ProductionJobState.PLANNED.value,
                    ProductionJobState.RUNNING.value,
                }:
                    action_id = _action_id(record.action_id)
                    if runtime.actions.get(action_id) is not None:
                        raise GameplayPersistenceError(
                            f"Action already exists in supplied runtime: {record.action_id}"
                        )

        inventories: dict[str, Inventory] = {}
        for record in self.inventories:
            inventory = Inventory()
            for resource, value, unit in record.stocks:
                inventory.add(ResourceType(resource), Quantity(value, ResourceUnit(unit)))
            inventories[record.inventory_id] = inventory

        nodes = WorldResourceNodeManager()
        for record in self.nodes:
            node = WorldResourceNode(
                record.node_id,
                record.world_id,
                ResourceType(record.resource_type),
                _quantity(record.quantity),
                _quantity(record.capacity),
                _quantity(record.regeneration_rate),
                Tick(record.last_simulation_tick),
                record.location_id,
            )
            nodes.add(node)

        recipes = {
            record.recipe_id: Recipe(
                record.recipe_id,
                tuple((ResourceType(resource), _quantity((value, unit))) for resource, value, unit in record.inputs),
                tuple((ResourceType(resource), _quantity((value, unit))) for resource, value, unit in record.outputs),
                processing_time=Tick(record.processing_time),
                facility_type=record.facility_type,
                required_capabilities=record.required_capabilities,
            )
            for record in self.recipes
        }
        owns_runtime = runtime is None
        if owns_runtime:
            runtime = SimulationRuntime(start_tick=Tick(self.simulation_tick))
        jobs = ProductionJobManager(runtime)
        created_action_ids = []
        try:
            for record in self.jobs:
                job = jobs.restore_job(
                    record.job_id,
                    recipes[record.recipe_id],
                    inventories[record.inventory_id],
                    Tick(record.start_tick),
                    Tick(record.duration),
                    _action_id(record.action_id),
                    ProductionJobState(record.state),
                    record.inputs_refunded,
                )
                if record.state in {
                    ProductionJobState.PLANNED.value,
                    ProductionJobState.RUNNING.value,
                }:
                    created_action_ids.append(job.action_id)
        except Exception as error:
            # A supplied runtime is a candidate boundary. There is no Core
            # rollback API for scheduler entries, so callers must not supply
            # the active runtime when restore can fail.
            for action_id in created_action_ids:
                try:
                    runtime.actions.cancel(action_id, "gameplay restore failed")
                except Exception:
                    pass
            raise GameplayPersistenceError("Could not restore production jobs.") from error
        return RestoredGameplayState(
            simulation_tick=Tick(self.simulation_tick),
            inventories=MappingProxyType(inventories),
            nodes=nodes,
            jobs=jobs,
            recipes=MappingProxyType(recipes),
        )


@dataclass(frozen=True)
class RestoredGameplayState:
    simulation_tick: Tick
    inventories: Mapping[str, Inventory]
    nodes: WorldResourceNodeManager
    jobs: ProductionJobManager
    recipes: Mapping[str, Recipe]


class GameplayJsonCodec:
    @staticmethod
    def encode(snapshot: GameplaySnapshot) -> str:
        if not isinstance(snapshot, GameplaySnapshot):
            raise TypeError("snapshot must be GameplaySnapshot.")
        try:
            return json.dumps(snapshot.to_dict(), ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as error:
            raise GameplayPersistenceError("Gameplay snapshot is not JSON-compatible.") from error

    @staticmethod
    def decode(payload: str) -> GameplaySnapshot:
        if not isinstance(payload, str):
            raise TypeError("JSON payload must be a string.")
        try:
            data = json.loads(payload, parse_constant=_reject_constant)
        except json.JSONDecodeError as error:
            raise GameplayPersistenceError("Invalid gameplay JSON.") from error
        return GameplaySnapshot.from_dict(data)


class GameplayFileAdapter:
    @staticmethod
    def save(snapshot: GameplaySnapshot, path) -> Path:
        target = Path(path)
        payload = GameplayJsonCodec.encode(snapshot)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False) as file:
                temporary = Path(file.name)
                file.write(payload)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, target)
            temporary = None
            return target
        except OSError as error:
            raise GameplayFileError(f"Could not write gameplay snapshot: {target}") from error
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass

    @staticmethod
    def load(path) -> GameplaySnapshot:
        target = Path(path)
        try:
            payload = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise GameplayFileError(f"Could not read gameplay snapshot: {target}") from error
        return GameplayJsonCodec.decode(payload)


def _node_record(node: WorldResourceNode) -> NodeRecord:
    return NodeRecord(node.node_id, node.world_id, node.resource_type.value, _quantity_tuple(node.quantity), _quantity_tuple(node.capacity), _quantity_tuple(node.regeneration_rate), node.last_simulation_tick.value)


def _recipe_record(recipe: Recipe) -> RecipeRecord:
    return RecipeRecord(
        recipe.recipe_id,
        _components(recipe.inputs),
        _components(recipe.outputs),
        recipe.processing_time.value,
        recipe.facility_type,
        recipe.required_capabilities,
    )


def _components(components) -> tuple[tuple[str, int, str], ...]:
    return tuple((resource.value, quantity.value, quantity.unit.value) for resource, quantity in components)


def _inventory_record(data) -> InventoryRecord:
    if not isinstance(data, Mapping):
        raise GameplayPersistenceError("Inventory record must be an object.")
    inventory_id = _validate_id(data.get("inventory_id"), "inventory_id")
    stock_records = []
    for item in _list(data, "stocks"):
        if not isinstance(item, Mapping):
            raise GameplayPersistenceError("Inventory stock must be an object.")
        stock_records.append((
            _validate_id(item.get("resource_type"), "resource_type"),
            _non_negative_int(item.get("value"), "value"),
            _unit(item.get("unit")),
        ))
    stocks = tuple(stock_records)
    _unique((resource for resource, _, _ in stocks), "inventory resource")
    return InventoryRecord(inventory_id, stocks)


def _node_record_from_dict(data) -> NodeRecord:
    if not isinstance(data, Mapping):
        raise GameplayPersistenceError("Node record must be an object.")
    return NodeRecord(
        _validate_id(data.get("node_id"), "node_id"),
        _validate_id(data.get("world_id"), "world_id"),
        _validate_id(data.get("resource_type"), "resource_type"),
        _quantity_tuple_from_dict(data.get("quantity")),
        _quantity_tuple_from_dict(data.get("capacity")),
        _quantity_tuple_from_dict(data.get("regeneration_rate")),
        _non_negative_int(data.get("last_simulation_tick"), "last_simulation_tick"),
        _optional_text(data.get("location_id"), "location_id"),
    )


def _recipe_record_from_dict(data) -> RecipeRecord:
    if not isinstance(data, Mapping):
        raise GameplayPersistenceError("Recipe record must be an object.")
    processing_time = _positive_int(data.get("processing_time", 1), "processing_time")
    facility_type = data.get("facility_type")
    if facility_type is not None:
        facility_type = _validate_id(facility_type, "facility_type")
    capabilities = data.get("required_capabilities", [])
    if not isinstance(capabilities, list) or any(not isinstance(item, str) or not item.strip() for item in capabilities):
        raise GameplayPersistenceError("required_capabilities must be a list of strings.")
    if len(set(capabilities)) != len(capabilities):
        raise GameplayPersistenceError("Duplicate required capability.")
    return RecipeRecord(
        _validate_id(data.get("recipe_id"), "recipe_id"),
        _components_from_dict(data.get("inputs")),
        _components_from_dict(data.get("outputs")),
        processing_time,
        facility_type,
        tuple(sorted(capabilities)),
    )


def _job_record(data) -> JobRecord:
    if not isinstance(data, Mapping):
        raise GameplayPersistenceError("Job record must be an object.")
    return JobRecord(
        _validate_id(data.get("job_id"), "job_id"),
        _validate_id(data.get("recipe_id"), "recipe_id"),
        _validate_id(data.get("inventory_id"), "inventory_id"),
        _validate_id(data.get("state"), "state"),
        _non_negative_int(data.get("start_tick"), "start_tick"),
        _positive_int(data.get("duration"), "duration"),
        _non_negative_int(data.get("end_tick"), "end_tick"),
        _validate_id(data.get("action_id"), "action_id"),
        _boolean(data.get("inputs_refunded"), "inputs_refunded"),
    )


def _components_from_dict(data) -> tuple[tuple[str, int, str], ...]:
    if not isinstance(data, list):
        raise GameplayPersistenceError("Recipe components must be a list.")
    result = tuple((_validate_id(item.get("resource_type"), "resource_type"), _positive_int(item.get("value"), "value"), _unit(item.get("unit"))) for item in data if isinstance(item, Mapping))
    if len(result) != len(data):
        raise GameplayPersistenceError("Recipe component must be an object.")
    _unique((resource for resource, _, _ in result), "recipe resource")
    if not result:
        raise GameplayPersistenceError("Recipe components cannot be empty.")
    return result


def _quantity_tuple_from_dict(data) -> tuple[int, str]:
    if not isinstance(data, Mapping):
        raise GameplayPersistenceError("Quantity must be an object.")
    return _positive_or_zero_int(data.get("value"), "quantity value"), _unit(data.get("unit"))


def _quantity_tuple(quantity: Quantity) -> tuple[int, str]:
    return quantity.value, quantity.unit.value


def _quantity_dict(quantity: tuple[int, str]) -> dict[str, object]:
    return {"value": quantity[0], "unit": quantity[1]}


def _quantity(data: tuple[int, str]) -> Quantity:
    return Quantity(data[0], ResourceUnit(data[1]))


def _recipe_dict(record: RecipeRecord) -> dict[str, object]:
    result = {
        "recipe_id": record.recipe_id,
        "inputs": _components_dict(record.inputs),
        "outputs": _components_dict(record.outputs),
    }
    if record.processing_time != 1:
        result["processing_time"] = record.processing_time
    if record.facility_type is not None:
        result["facility_type"] = record.facility_type
    if record.required_capabilities:
        result["required_capabilities"] = list(record.required_capabilities)
    return result


def _components_dict(components):
    return [{"resource_type": resource, "value": value, "unit": unit} for resource, value, unit in components]


def _list(data, key):
    value = data.get(key)
    if not isinstance(value, list):
        raise GameplayPersistenceError(f"{key} must be a list.")
    return value


def _unique(values, kind):
    values = tuple(values)
    if len(set(values)) != len(values):
        raise GameplayPersistenceError(f"Duplicate {kind} identity.")


def _validate_id(value, name):
    if not isinstance(value, str):
        raise GameplayPersistenceError(f"{name} must be a string.")
    if not value.strip():
        raise GameplayPersistenceError(f"{name} cannot be empty.")
    return value


def _optional_text(value, name):
    if value is None:
        return None
    return _validate_id(value, name)


def _non_negative_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GameplayPersistenceError(f"{name} must be a non-negative integer.")
    return value


def _positive_int(value, name):
    value = _non_negative_int(value, name)
    if value == 0:
        raise GameplayPersistenceError(f"{name} must be positive.")
    return value


def _positive_or_zero_int(value, name):
    return _non_negative_int(value, name)


def _unit(value):
    if not isinstance(value, str):
        raise GameplayPersistenceError("unit must be a string.")
    try:
        return ResourceUnit(value).value
    except ValueError as error:
        raise GameplayPersistenceError(f"Unsupported resource unit: {value}") from error


def _boolean(value, name):
    if not isinstance(value, bool):
        raise GameplayPersistenceError(f"{name} must be boolean.")
    return value


def _action_id(value):
    from core.foundation import ActionId
    return ActionId(value)


def _reject_constant(value):
    raise GameplayPersistenceError(f"Non-standard JSON number is not allowed: {value}")
