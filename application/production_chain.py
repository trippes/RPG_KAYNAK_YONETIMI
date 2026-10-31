"""Application-level orchestration for sequential production jobs."""

from dataclasses import dataclass
from enum import Enum

from core.simulation.event_types import CanonicalEventType
from core.simulation.events import SimulationEvent
from core.time import Tick

from resources import Inventory, ProductionJob, ProductionJobManager, Recipe

from .production_capacity import ProductionCapacity
from .production_facility import ProductionFacilityRegistry


class ProductionChainState(Enum):
    """Lifecycle state of one non-persistent production chain."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ProductionChainStage:
    """One recipe execution request in a sequential chain."""

    recipe: Recipe
    inventory: Inventory
    duration: Tick | int | None = None
    capacity_amount: int = 1
    facility_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.recipe, Recipe):
            raise TypeError("stage recipe must be Recipe.")
        if not isinstance(self.inventory, Inventory):
            raise TypeError("stage inventory must be Inventory.")
        duration = None if self.duration is None else (
            self.duration if isinstance(self.duration, Tick) else Tick(self.duration)
        )
        if duration is not None and duration.value <= 0:
            raise ValueError("stage duration must be positive.")
        if isinstance(self.capacity_amount, bool) or not isinstance(self.capacity_amount, int):
            raise TypeError("stage capacity_amount must be an integer.")
        if self.capacity_amount <= 0:
            raise ValueError("stage capacity_amount must be positive.")
        if self.facility_id is not None and (not isinstance(self.facility_id, str) or not self.facility_id.strip()):
            raise ValueError("facility_id must be a non-empty string or None.")
        object.__setattr__(self, "duration", duration)


class ProductionChain:
    """Run ordered stages through an existing ProductionJobManager.

    The chain owns orchestration state only. Resource consumption and output
    creation remain exclusively owned by ProductionJobManager and Recipe.
    Chain state is runtime-only and intentionally outside persistence.
    """

    def __init__(
        self,
        production_jobs: ProductionJobManager,
        stages: tuple[ProductionChainStage, ...] | list[ProductionChainStage],
        chain_id: str,
        capacity: ProductionCapacity | None = None,
        facilities: ProductionFacilityRegistry | None = None,
    ) -> None:
        if not isinstance(production_jobs, ProductionJobManager):
            raise TypeError("production_jobs must be ProductionJobManager.")
        if not isinstance(chain_id, str) or not chain_id.strip():
            raise ValueError("chain_id cannot be empty.")
        try:
            normalized = tuple(stages)
        except TypeError as error:
            raise TypeError("stages must be an iterable of ProductionChainStage.") from error
        if not normalized:
            raise ValueError("production chain must contain at least one stage.")
        if any(not isinstance(stage, ProductionChainStage) for stage in normalized):
            raise TypeError("stages must contain ProductionChainStage values.")
        if capacity is not None and not isinstance(capacity, ProductionCapacity):
            raise TypeError("capacity must be ProductionCapacity or None.")
        if facilities is not None and not isinstance(facilities, ProductionFacilityRegistry):
            raise TypeError("facilities must be ProductionFacilityRegistry or None.")

        self._production_jobs = production_jobs
        self._stages = normalized
        self._chain_id = chain_id
        self._capacity = capacity
        self._facilities = facilities
        self._state = ProductionChainState.PENDING
        self._current_stage_index = None
        self._stage_jobs: dict[int, ProductionJob] = {}
        self._job_to_stage = {}
        self._failure: Exception | None = None
        self._flush_required = False
        production_jobs.runtime.dispatcher.register(self)

    @property
    def chain_id(self) -> str:
        return self._chain_id

    @property
    def stages(self) -> tuple[ProductionChainStage, ...]:
        return self._stages

    @property
    def state(self) -> ProductionChainState:
        return self._state

    @property
    def current_stage_index(self) -> int | None:
        return self._current_stage_index

    @property
    def current_job(self) -> ProductionJob | None:
        if self._current_stage_index is None:
            return None
        return self._stage_jobs.get(self._current_stage_index)

    @property
    def jobs(self) -> tuple[ProductionJob, ...]:
        return tuple(self._stage_jobs[index] for index in sorted(self._stage_jobs))

    @property
    def failure(self) -> Exception | None:
        return self._failure

    def start(self) -> ProductionJob:
        """Start stage zero, or fail deterministically without partial chaining."""
        if self._state != ProductionChainState.PENDING:
            raise ValueError("Production chain can only start from pending state.")
        try:
            job = self._start_stage(0)
        except Exception as error:
            self._fail(error)
            raise
        self._state = ProductionChainState.RUNNING
        return job

    def advance_to(self, target_tick: Tick | int):
        """Advance jobs through the existing manager and dispatch chain events."""
        if self._state == ProductionChainState.PENDING:
            raise ValueError("Production chain must be started before advancing.")
        if self._state in {ProductionChainState.COMPLETED, ProductionChainState.FAILED, ProductionChainState.CANCELLED}:
            return ()

        try:
            events = self._production_jobs.advance_to(target_tick)
            # A completion consumer can schedule the next job while the
            # current dispatcher cycle is running. Let the existing scheduler
            # process its start event at the same tick.
            while self._flush_required and self._state == ProductionChainState.RUNNING:
                self._flush_required = False
                events = events + self._production_jobs.advance_to(target_tick)
            return events
        except Exception as error:
            if self.current_job is not None and self.current_job.state.value == "failed":
                self._fail(error)
            raise

    def advance_by(self, delta: Tick | int):
        delta = delta if isinstance(delta, Tick) else Tick(delta)
        return self.advance_to(self._production_jobs.runtime.current_tick + delta)

    def cancel(self, cancellation: str = "cancelled") -> None:
        """Cancel the current job and prevent all later stages."""
        if self._state != ProductionChainState.RUNNING:
            raise ValueError("Only a running production chain can be cancelled.")
        job = self.current_job
        if job is None:
            raise RuntimeError("Running production chain has no current job.")
        if self._capacity is None:
            self._production_jobs.cancel(job.job_id, cancellation)
        else:
            self._capacity.cancel(self._production_jobs, job.job_id, cancellation)
        self._state = ProductionChainState.CANCELLED

    def consume(self, event: SimulationEvent) -> None:
        """Consume canonical action events for jobs owned by this chain."""
        if not isinstance(event, SimulationEvent) or event.action_id is None:
            return
        stage_index = self._job_to_stage.get(event.action_id)
        if stage_index is None or stage_index != self._current_stage_index:
            return
        if self._state != ProductionChainState.RUNNING:
            return

        job = self._stage_jobs[stage_index]
        if event.action_id != job.action_id:
            return
        if event.event_type == CanonicalEventType.ACTION_COMPLETED:
            if job.state.value != "completed":
                return
            self._complete_stage(stage_index)
        elif event.event_type == CanonicalEventType.ACTION_FAILED:
            self._fail(RuntimeError(f"Production stage failed: {stage_index}"))
        elif event.event_type == CanonicalEventType.ACTION_CANCELLED:
            self._state = ProductionChainState.CANCELLED

    def dispose(self) -> None:
        """Unregister this runtime-only consumer when the chain is discarded."""
        self._production_jobs.runtime.dispatcher.unregister(self)

    def _start_stage(self, index: int) -> ProductionJob:
        if index in self._stage_jobs:
            return self._stage_jobs[index]
        stage = self._stages[index]
        job_id = f"{self._chain_id}:stage:{index}"
        if self._facilities is not None:
            if stage.facility_id is None:
                raise ValueError("Facility-bound chains require an explicit facility_id per stage.")
            facility = self._facilities.get(stage.facility_id)
            if facility is None:
                raise KeyError(f"Production facility not found: {stage.facility_id}")
            job = facility.start(
                self._production_jobs,
                stage.recipe,
                stage.inventory,
                duration=stage.duration,
                job_id=job_id,
                capacity_amount=stage.capacity_amount,
            )
        elif self._capacity is None:
            job = self._production_jobs.start(
                stage.recipe, stage.inventory, stage.duration, job_id=job_id
            )
        else:
            job = self._capacity.start(
                self._production_jobs,
                stage.recipe,
                stage.inventory,
                stage.duration,
                job_id=job_id,
                amount=stage.capacity_amount,
            )
        self._stage_jobs[index] = job
        self._job_to_stage[job.action_id] = index
        self._current_stage_index = index
        return job

    def _complete_stage(self, index: int) -> None:
        if index != self._current_stage_index:
            return
        next_index = index + 1
        if self._capacity is not None:
            self._capacity.release(self._stage_jobs[index].job_id)
        if next_index >= len(self._stages):
            self._state = ProductionChainState.COMPLETED
            return
        try:
            self._start_stage(next_index)
        except Exception as error:
            self._fail(error)
            raise
        self._flush_required = True

    def _fail(self, error: Exception) -> None:
        if self._capacity is not None and self.current_job is not None:
            self._capacity.release(self.current_job.job_id)
        self._failure = error
        self._state = ProductionChainState.FAILED


__all__ = ["ProductionChain", "ProductionChainStage", "ProductionChainState"]
