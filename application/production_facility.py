"""Application-level production facilities backed by ProductionCapacity."""

from __future__ import annotations

from dataclasses import dataclass

from core.simulation.event_types import CanonicalEventType
from core.simulation.events import SimulationEvent

from resources import Inventory, ProductionJob, ProductionJobManager, Recipe

from .production_capacity import ProductionCapacity, ProductionCapacityError


class ProductionFacilityError(ValueError):
    """Invalid facility, recipe compatibility or facility lifecycle operation."""


class ProductionFacility:
    """One explicit production facility with an owned shared capacity pool."""

    def __init__(
        self,
        facility_id: str,
        facility_type: str,
        capacity: int,
        capabilities: tuple[str, ...] | list[str] = (),
        active: bool = True,
    ) -> None:
        self._validate_text(facility_id, "facility_id")
        self._validate_text(facility_type, "facility_type")
        if not isinstance(active, bool):
            raise TypeError("active must be boolean.")
        normalized = tuple(capabilities)
        if any(not isinstance(capability, str) or not capability.strip() for capability in normalized):
            raise ValueError("capabilities must contain non-empty strings.")
        if len(set(normalized)) != len(normalized):
            raise ValueError("capabilities cannot contain duplicates.")

        self._facility_id = facility_id
        self._facility_type = facility_type
        self._capabilities = tuple(sorted(normalized))
        self._active = active
        self._capacity = ProductionCapacity(capacity)
        self._active_jobs: dict[object, tuple[str, int]] = {}
        self._runtime = None
        self._next_job_number = 1

    @property
    def facility_id(self) -> str:
        return self._facility_id

    @property
    def facility_type(self) -> str:
        return self._facility_type

    @property
    def capabilities(self) -> tuple[str, ...]:
        return self._capabilities

    @property
    def active(self) -> bool:
        return self._active

    @property
    def capacity(self) -> ProductionCapacity:
        return self._capacity

    @property
    def active_job_ids(self) -> tuple[str, ...]:
        return tuple(sorted(job_id for job_id, _ in self._active_jobs.values()))

    def capacity_amount_for(self, job_id: str) -> int:
        for registered_job_id, amount in self._active_jobs.values():
            if registered_job_id == job_id:
                return amount
        raise KeyError(f"Active facility job not found: {job_id}")

    def set_active(self, active: bool) -> None:
        if not isinstance(active, bool):
            raise TypeError("active must be boolean.")
        self._active = active

    def supports(self, recipe: Recipe) -> bool:
        if not isinstance(recipe, Recipe):
            raise TypeError("recipe must be Recipe.")
        if recipe.facility_type is not None and recipe.facility_type != self._facility_type:
            return False
        return set(recipe.required_capabilities).issubset(self._capabilities)

    def start(
        self,
        production_jobs: ProductionJobManager,
        recipe: Recipe,
        inventory: Inventory,
        duration=None,
        job_id: str | None = None,
        capacity_amount: int = 1,
    ) -> ProductionJob:
        if not self._active:
            raise ProductionFacilityError(f"Facility is inactive: {self._facility_id}")
        if not isinstance(recipe, Recipe):
            raise TypeError("recipe must be Recipe.")
        if not self.supports(recipe):
            raise ProductionFacilityError(
                f"Facility does not support recipe: {recipe.recipe_id}"
            )
        if duration is None:
            duration = recipe.processing_time
        if job_id is None:
            while True:
                job_id = f"facility:{self._facility_id}:job:{self._next_job_number:06d}"
                self._next_job_number += 1
                if production_jobs.get(job_id) is None:
                    break
        try:
            job = self._capacity.start(
                production_jobs,
                recipe,
                inventory,
                duration,
                job_id=job_id,
                amount=capacity_amount,
            )
        except ProductionCapacityError:
            raise
        self._active_jobs[job.action_id] = (job.job_id, capacity_amount)
        self._bind_runtime(production_jobs)
        return job

    def cancel(self, production_jobs: ProductionJobManager, job_id: str, cancellation: str = "cancelled") -> None:
        self._capacity.cancel(production_jobs, job_id, cancellation)
        self._remove_job_id(job_id)

    def consume(self, event: SimulationEvent) -> None:
        if not isinstance(event, SimulationEvent) or event.action_id is None:
            return
        if event.action_id not in self._active_jobs:
            return
        if event.event_type in {
            CanonicalEventType.ACTION_COMPLETED,
            CanonicalEventType.ACTION_CANCELLED,
            CanonicalEventType.ACTION_FAILED,
        }:
            self._active_jobs.pop(event.action_id, None)

    def restore_active_jobs(
        self,
        production_jobs: ProductionJobManager,
        jobs: tuple[tuple[str, int], ...],
    ) -> None:
        if not self._active:
            raise ProductionFacilityError("Cannot restore jobs into an inactive facility.")
        attached: list[str] = []
        try:
            for job_id, capacity_amount in jobs:
                job = production_jobs.get(job_id)
                if job is None:
                    raise ProductionFacilityError(f"Production job not found: {job_id}")
                self._capacity.attach_existing(production_jobs, (job_id,), capacity_amount)
                attached.append(job_id)
                self._active_jobs[job.action_id] = (job.job_id, capacity_amount)
        except Exception:
            for job_id in attached:
                self._capacity.release(job_id)
                self._remove_job_id(job_id)
            raise
        if jobs:
            self._bind_runtime(production_jobs)

    def dispose(self) -> None:
        self._capacity.dispose()
        if self._runtime is not None:
            self._runtime.dispatcher.unregister(self)
            self._runtime = None

    def _bind_runtime(self, production_jobs: ProductionJobManager) -> None:
        if self._runtime is None:
            self._runtime = production_jobs.runtime
            self._runtime.dispatcher.register(self)
        elif self._runtime is not production_jobs.runtime:
            raise ProductionFacilityError("Facility cannot span multiple runtimes.")

    def _remove_job_id(self, job_id: str) -> None:
        for action_id, (registered_job_id, _) in tuple(self._active_jobs.items()):
            if registered_job_id == job_id:
                self._active_jobs.pop(action_id, None)

    @staticmethod
    def _validate_text(value: str, name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise TypeError(f"{name} must be a non-empty string.")


class ProductionFacilityRegistry:
    """Deterministic registry for explicit facility selection."""

    def __init__(self) -> None:
        self._facilities: dict[str, ProductionFacility] = {}

    def add(self, facility: ProductionFacility) -> None:
        if not isinstance(facility, ProductionFacility):
            raise TypeError("facility must be ProductionFacility.")
        if facility.facility_id in self._facilities:
            raise ValueError(f"Duplicate facility ID: {facility.facility_id}")
        self._facilities[facility.facility_id] = facility

    def get(self, facility_id: str) -> ProductionFacility | None:
        if not isinstance(facility_id, str) or not facility_id.strip():
            raise TypeError("facility_id must be a non-empty string.")
        return self._facilities.get(facility_id)

    def facilities(self) -> tuple[ProductionFacility, ...]:
        return tuple(self._facilities[key] for key in sorted(self._facilities))

    def count(self) -> int:
        return len(self._facilities)

    def validate(self) -> None:
        for facility in self.facilities():
            if facility.capacity.reserved > facility.capacity.capacity:
                raise ProductionFacilityError(
                    f"Facility capacity exceeded: {facility.facility_id}"
                )
            expected = sum(
                facility.capacity_amount_for(job_id)
                for job_id in facility.active_job_ids
            )
            if expected != facility.capacity.reserved:
                raise ProductionFacilityError(
                    f"Facility reservation mismatch: {facility.facility_id}"
                )


@dataclass(frozen=True)
class FacilityBinding:
    job_id: str
    facility_id: str
    capacity_amount: int


__all__ = [
    "ProductionFacility",
    "ProductionFacilityError",
    "ProductionFacilityRegistry",
    "FacilityBinding",
]
