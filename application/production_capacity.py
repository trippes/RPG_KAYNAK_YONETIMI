"""Opt-in application-level capacity reservations for production jobs."""

from core.simulation.event_types import CanonicalEventType
from core.simulation.events import SimulationEvent

from resources import Inventory, ProductionJob, ProductionJobManager, ProductionJobState, Recipe


class ProductionCapacityError(ValueError):
    """Capacity configuration, reservation or lifecycle error."""


class ProductionCapacity:
    """A deterministic shared slot pool for capacity-aware production jobs.

    Capacity is deliberately independent from physical facilities. Existing
    jobs remain unrestricted unless they are started through this pool or a
    ProductionChain configured with it.
    """

    def __init__(self, capacity: int) -> None:
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise TypeError("capacity must be an integer.")
        if capacity <= 0:
            raise ValueError("capacity must be positive.")
        self._capacity = capacity
        self._reservations: dict[str, int] = {}
        self._jobs: dict[object, str] = {}
        self._runtime = None

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def reserved(self) -> int:
        return sum(self._reservations.values())

    @property
    def available(self) -> int:
        return self._capacity - self.reserved

    def reservation_count(self) -> int:
        return len(self._reservations)

    def reserve(self, reservation_id: str, amount: int = 1) -> None:
        self._validate_reservation(reservation_id, amount)
        if reservation_id in self._reservations:
            raise ProductionCapacityError(f"Reservation already exists: {reservation_id}")
        if amount > self.available:
            raise ProductionCapacityError("Production capacity is unavailable.")
        self._reservations[reservation_id] = amount

    def release(self, reservation_id: str) -> bool:
        if not isinstance(reservation_id, str) or not reservation_id.strip():
            raise TypeError("reservation_id must be a non-empty string.")
        return self._reservations.pop(reservation_id, None) is not None

    def start(
        self,
        production_jobs: ProductionJobManager,
        recipe: Recipe,
        inventory: Inventory,
        duration,
        job_id: str,
        amount: int = 1,
    ) -> ProductionJob:
        """Reserve capacity, then start one existing production job atomically."""
        if not isinstance(production_jobs, ProductionJobManager):
            raise TypeError("production_jobs must be ProductionJobManager.")
        if self._runtime is not None and self._runtime is not production_jobs.runtime:
            raise ProductionCapacityError("Capacity cannot span multiple runtimes.")
        self.reserve(job_id, amount)
        try:
            job = production_jobs.start(recipe, inventory, duration, job_id=job_id)
        except Exception:
            self.release(job_id)
            raise
        self._jobs[job.action_id] = job_id
        if self._runtime is None:
            self._runtime = production_jobs.runtime
            self._runtime.dispatcher.register(self)
        return job

    def cancel(self, production_jobs: ProductionJobManager, job_id: str, cancellation: str = "cancelled") -> None:
        if not isinstance(production_jobs, ProductionJobManager):
            raise TypeError("production_jobs must be ProductionJobManager.")
        production_jobs.cancel(job_id, cancellation)
        self.release(job_id)

    def attach_existing(
        self,
        production_jobs: ProductionJobManager,
        job_ids: tuple[str, ...] | list[str],
        amount: int = 1,
    ) -> None:
        """Rebuild runtime reservations for explicitly selected restored jobs.

        Capacity is runtime-only. A caller restoring a capacity-aware job must
        explicitly identify those jobs; generic restored jobs are not silently
        assigned to a capacity pool.
        """
        if not isinstance(production_jobs, ProductionJobManager):
            raise TypeError("production_jobs must be ProductionJobManager.")
        if self._runtime is not None and self._runtime is not production_jobs.runtime:
            raise ProductionCapacityError("Capacity cannot span multiple runtimes.")
        normalized = tuple(job_ids)
        attached: list[tuple[str, object, int]] = []
        try:
            for job_id in normalized:
                job = production_jobs.get(job_id)
                if job is None:
                    raise KeyError(f"Production job not found: {job_id}")
                if job.state not in {ProductionJobState.PLANNED, ProductionJobState.RUNNING}:
                    raise ProductionCapacityError("Only active jobs can be attached to capacity.")
                self.reserve(job_id, amount)
                attached.append((job_id, job.action_id, amount))
            for job_id, action_id, _ in attached:
                self._jobs[action_id] = job_id
            if self._runtime is None:
                self._runtime = production_jobs.runtime
                self._runtime.dispatcher.register(self)
        except Exception:
            for job_id, _, _ in attached:
                self.release(job_id)
            raise

    def consume(self, event: SimulationEvent) -> None:
        if not isinstance(event, SimulationEvent) or event.action_id is None:
            return
        reservation_id = self._jobs.get(event.action_id)
        if reservation_id is None:
            return
        if event.event_type in {
            CanonicalEventType.ACTION_COMPLETED,
            CanonicalEventType.ACTION_CANCELLED,
            CanonicalEventType.ACTION_FAILED,
        }:
            self.release(reservation_id)
            self._jobs.pop(event.action_id, None)

    def dispose(self) -> None:
        if self._runtime is not None:
            self._runtime.dispatcher.unregister(self)
            self._runtime = None

    @staticmethod
    def _validate_reservation(reservation_id: str, amount: int) -> None:
        if not isinstance(reservation_id, str) or not reservation_id.strip():
            raise TypeError("reservation_id must be a non-empty string.")
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("reservation amount must be an integer.")
        if amount <= 0:
            raise ValueError("reservation amount must be positive.")


__all__ = ["ProductionCapacity", "ProductionCapacityError"]
