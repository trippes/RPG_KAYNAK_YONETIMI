"""Persistence records for application-level facilities and job bindings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from resources import ProductionJobManager, ProductionJobState

from .production_facility import ProductionFacility, ProductionFacilityRegistry, ProductionFacilityError


PRODUCTION_SCHEMA = "rpg-production"
PRODUCTION_SCHEMA_VERSION = 1


class ProductionPersistenceError(ValueError):
    """Invalid facility or facility-job persistence data."""


@dataclass(frozen=True)
class FacilityRecord:
    facility_id: str
    facility_type: str
    capacity: int
    capabilities: tuple[str, ...]
    active: bool


@dataclass(frozen=True)
class FacilityJobRecord:
    job_id: str
    facility_id: str
    capacity_amount: int


@dataclass(frozen=True)
class ProductionSnapshot:
    facilities: tuple[FacilityRecord, ...]
    facility_jobs: tuple[FacilityJobRecord, ...]

    @classmethod
    def from_registry(cls, registry: ProductionFacilityRegistry) -> "ProductionSnapshot":
        if not isinstance(registry, ProductionFacilityRegistry):
            raise TypeError("registry must be ProductionFacilityRegistry.")
        registry.validate()
        facilities = tuple(
            FacilityRecord(
                facility.facility_id,
                facility.facility_type,
                facility.capacity.capacity,
                facility.capabilities,
                facility.active,
            )
            for facility in registry.facilities()
        )
        bindings: list[FacilityJobRecord] = []
        for facility in registry.facilities():
            for job_id in facility.active_job_ids:
                amount = facility.capacity_amount_for(job_id)
                bindings.append(FacilityJobRecord(job_id, facility.facility_id, amount))
        return cls(facilities, tuple(sorted(bindings, key=lambda record: record.job_id)))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": PRODUCTION_SCHEMA,
            "schema_version": PRODUCTION_SCHEMA_VERSION,
            "facilities": [
                {
                    "facility_id": record.facility_id,
                    "facility_type": record.facility_type,
                    "capacity": record.capacity,
                    "capabilities": list(record.capabilities),
                    "active": record.active,
                }
                for record in self.facilities
            ],
            "facility_jobs": [
                {
                    "job_id": record.job_id,
                    "facility_id": record.facility_id,
                    "capacity_amount": record.capacity_amount,
                }
                for record in self.facility_jobs
            ],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "ProductionSnapshot":
        if not isinstance(data, Mapping):
            raise ProductionPersistenceError("Production snapshot must be an object.")
        if data.get("schema") != PRODUCTION_SCHEMA or data.get("schema_version") != PRODUCTION_SCHEMA_VERSION:
            raise ProductionPersistenceError("Unsupported production persistence schema.")
        facilities = tuple(_facility_record(item) for item in _list(data, "facilities"))
        jobs = tuple(_facility_job_record(item) for item in _list(data, "facility_jobs"))
        _unique((record.facility_id for record in facilities), "facility")
        _unique((record.job_id for record in jobs), "facility job")
        facility_ids = {record.facility_id for record in facilities}
        if any(record.facility_id not in facility_ids for record in jobs):
            raise ProductionPersistenceError("Facility job references unknown facility.")
        usage: dict[str, int] = {}
        for record in jobs:
            usage[record.facility_id] = usage.get(record.facility_id, 0) + record.capacity_amount
        limits = {record.facility_id: record.capacity for record in facilities}
        if any(usage[facility_id] > limits[facility_id] for facility_id in usage):
            raise ProductionPersistenceError("Facility capacity reservations exceed capacity.")
        return cls(
            tuple(sorted(facilities, key=lambda record: record.facility_id)),
            tuple(sorted(jobs, key=lambda record: record.job_id)),
        )

    def restore(self, jobs: ProductionJobManager) -> ProductionFacilityRegistry:
        if not isinstance(jobs, ProductionJobManager):
            raise TypeError("jobs must be ProductionJobManager.")
        registry = ProductionFacilityRegistry()
        for record in self.facilities:
            registry.add(ProductionFacility(
                record.facility_id,
                record.facility_type,
                record.capacity,
                record.capabilities,
                record.active,
            ))
        grouped: dict[str, list[tuple[str, int]]] = {}
        for record in self.facility_jobs:
            job = jobs.get(record.job_id)
            if job is None:
                raise ProductionPersistenceError(f"Unknown facility job: {record.job_id}")
            if job.state not in {ProductionJobState.PLANNED, ProductionJobState.RUNNING}:
                raise ProductionPersistenceError("Facility binding must reference an active job.")
            grouped.setdefault(record.facility_id, []).append((record.job_id, record.capacity_amount))
        try:
            for facility_id, bindings in grouped.items():
                facility = registry.get(facility_id)
                if facility is None:
                    raise ProductionPersistenceError(f"Unknown facility: {facility_id}")
                facility.restore_active_jobs(jobs, tuple(bindings))
            registry.validate()
        except (ProductionFacilityError, ValueError, KeyError) as error:
            raise ProductionPersistenceError("Could not restore production facilities.") from error
        return registry


def _facility_record(data) -> FacilityRecord:
    if not isinstance(data, Mapping):
        raise ProductionPersistenceError("Facility record must be an object.")
    capabilities = data.get("capabilities")
    if not isinstance(capabilities, list) or any(not isinstance(item, str) or not item.strip() for item in capabilities):
        raise ProductionPersistenceError("Facility capabilities must be a list of strings.")
    return FacilityRecord(
        _text(data.get("facility_id"), "facility_id"),
        _text(data.get("facility_type"), "facility_type"),
        _positive_int(data.get("capacity"), "capacity"),
        tuple(sorted(set(capabilities))),
        _bool(data.get("active"), "active"),
    )


def _facility_job_record(data) -> FacilityJobRecord:
    if not isinstance(data, Mapping):
        raise ProductionPersistenceError("Facility job record must be an object.")
    return FacilityJobRecord(
        _text(data.get("job_id"), "job_id"),
        _text(data.get("facility_id"), "facility_id"),
        _positive_int(data.get("capacity_amount"), "capacity_amount"),
    )


def _list(data, key):
    value = data.get(key)
    if not isinstance(value, list):
        raise ProductionPersistenceError(f"{key} must be a list.")
    return value


def _unique(values, label):
    values = tuple(values)
    if len(values) != len(set(values)):
        raise ProductionPersistenceError(f"Duplicate {label} identity.")


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ProductionPersistenceError(f"{name} must be a non-empty string.")
    return value


def _positive_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ProductionPersistenceError(f"{name} must be a positive integer.")
    return value


def _bool(value, name):
    if not isinstance(value, bool):
        raise ProductionPersistenceError(f"{name} must be boolean.")
    return value


__all__ = [
    "PRODUCTION_SCHEMA",
    "PRODUCTION_SCHEMA_VERSION",
    "ProductionPersistenceError",
    "FacilityRecord",
    "FacilityJobRecord",
    "ProductionSnapshot",
]
