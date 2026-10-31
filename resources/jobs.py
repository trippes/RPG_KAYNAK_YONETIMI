"""Tick-bound production jobs built on the canonical simulation runtime."""

from enum import Enum

from core.foundation import ActionId, Identifier
from core.simulation import SimulationRuntime
from core.simulation.event_types import CanonicalEventType
from core.simulation.events import SimulationEvent
from core.time import Tick

from .inventory import Inventory
from .production import consume_resources
from .recipe import Recipe


class ProductionJobState(Enum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


def production_action_id(job_id: str) -> ActionId:
    """Return the deterministic action identity reserved for one job."""
    if not isinstance(job_id, str) or not job_id.strip():
        raise ValueError("job_id cannot be empty.")
    return ActionId(f"production_job:{job_id}")


class ProductionJob:
    """Runtime production job state, intentionally outside persistence state."""

    def __init__(
        self,
        job_id: str,
        recipe: Recipe,
        inventory: Inventory,
        start_tick: Tick,
        duration: Tick,
        action_id: ActionId,
    ) -> None:
        if not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("job_id cannot be empty.")
        if not isinstance(recipe, Recipe):
            raise TypeError("recipe must be Recipe.")
        if not isinstance(inventory, Inventory):
            raise TypeError("inventory must be Inventory.")
        if not isinstance(start_tick, Tick) or not isinstance(duration, Tick):
            raise TypeError("start_tick and duration must be Tick.")
        if duration.value <= 0:
            raise ValueError("Production duration must be positive.")
        if not isinstance(action_id, ActionId):
            raise TypeError("action_id must be ActionId.")
        self._job_id = job_id
        self._recipe = recipe
        self._inventory = inventory
        self._start_tick = start_tick
        self._duration = duration
        self._end_tick = start_tick + duration
        self._action_id = action_id
        self._state = ProductionJobState.PLANNED
        self._inputs_refunded = False

    @property
    def job_id(self) -> str:
        return self._job_id

    @property
    def recipe(self) -> Recipe:
        return self._recipe

    @property
    def inventory(self) -> Inventory:
        return self._inventory

    @property
    def start_tick(self) -> Tick:
        return self._start_tick

    @property
    def duration(self) -> Tick:
        return self._duration

    @property
    def end_tick(self) -> Tick:
        return self._end_tick

    @property
    def action_id(self) -> ActionId:
        return self._action_id

    @property
    def state(self) -> ProductionJobState:
        return self._state

    @property
    def inputs_refunded(self) -> bool:
        return self._inputs_refunded

    def _mark_running(self) -> None:
        if self._state == ProductionJobState.PLANNED:
            self._state = ProductionJobState.RUNNING
        elif self._state != ProductionJobState.RUNNING:
            raise ValueError("Production job cannot become running from its current state.")

    def _mark_completed(self) -> None:
        if self._state != ProductionJobState.RUNNING:
            raise ValueError("Only a running production job can complete.")
        self._state = ProductionJobState.COMPLETED

    def _mark_cancelled(self) -> None:
        if self._state not in {ProductionJobState.PLANNED, ProductionJobState.RUNNING}:
            raise ValueError("Production job cannot be cancelled in its current state.")
        self._state = ProductionJobState.CANCELLED

    def _mark_failed(self) -> None:
        if self._state in {ProductionJobState.COMPLETED, ProductionJobState.CANCELLED}:
            raise ValueError("Finished production job cannot fail.")
        self._state = ProductionJobState.FAILED

    def _mark_inputs_refunded(self) -> None:
        self._inputs_refunded = True

    def _restore_runtime_state(
        self,
        state: ProductionJobState,
        inputs_refunded: bool,
    ) -> None:
        if not isinstance(state, ProductionJobState):
            raise TypeError("state must be ProductionJobState.")
        if not isinstance(inputs_refunded, bool):
            raise TypeError("inputs_refunded must be boolean.")
        self._state = state
        self._inputs_refunded = inputs_refunded


class ProductionJobManager:
    """Manage production jobs through a canonical SimulationRuntime."""

    WORK_TYPE = "production.job"

    def __init__(self, runtime: SimulationRuntime) -> None:
        if not isinstance(runtime, SimulationRuntime):
            raise TypeError("runtime must be SimulationRuntime.")
        self._runtime = runtime
        self._jobs: dict[str, ProductionJob] = {}
        self._next_job_id = 1
        runtime.dispatcher.register(self)

    @property
    def runtime(self) -> SimulationRuntime:
        return self._runtime

    def get(self, job_id: str) -> ProductionJob | None:
        return self._jobs.get(job_id)

    def jobs(self) -> tuple[ProductionJob, ...]:
        """Return jobs in stable job-id order for runtime inspection."""
        return tuple(self._jobs[job_id] for job_id in sorted(self._jobs))

    def restore_job(
        self,
        job_id: str,
        recipe: Recipe,
        inventory: Inventory,
        start_tick: Tick,
        duration: Tick,
        action_id: ActionId,
        state: ProductionJobState,
        inputs_refunded: bool,
    ) -> ProductionJob:
        """Rebuild one persisted job without consuming inputs again.

        Active jobs are scheduled from the current runtime tick with only their
        remaining duration. This preserves the logical end tick without
        attempting to schedule an action in the past.
        """
        if not isinstance(start_tick, Tick) or not isinstance(duration, Tick):
            raise TypeError("start_tick and duration must be Tick.")
        if job_id in self._jobs:
            raise ValueError(f"Production job ID already exists: {job_id}")
        if not isinstance(state, ProductionJobState):
            raise TypeError("state must be ProductionJobState.")
        expected_action_id = production_action_id(job_id)
        if action_id != expected_action_id:
            raise ValueError(
                f"Production job action ID must be {expected_action_id}: {action_id}"
            )

        active = state in {ProductionJobState.PLANNED, ProductionJobState.RUNNING}
        if active and start_tick + duration < self._runtime.current_tick:
            raise ValueError("Persisted production job ended before restore tick.")
        action = None
        if active:
            remaining = (start_tick + duration).value - self._runtime.current_tick.value
            if remaining <= 0:
                raise ValueError("Active persisted production job has no future duration.")
            action = self._runtime.actions.create(
                Identifier(f"production_job:{job_id}"),
                Tick(remaining),
                context={"production_job_id": job_id, "work_type": self.WORK_TYPE},
                action_id=expected_action_id,
            )
            try:
                self._runtime.actions.schedule(action.action_id, self._runtime.current_tick)
            except Exception:
                try:
                    self._runtime.actions.cancel(action.action_id, "production restore scheduling failed")
                except Exception:
                    pass
                raise

        job = ProductionJob(
            job_id=job_id,
            recipe=recipe,
            inventory=inventory,
            start_tick=start_tick,
            duration=duration,
            action_id=expected_action_id,
        )
        job._restore_runtime_state(state, inputs_refunded)
        self._jobs[job_id] = job
        return job

    def start(
        self,
        recipe: Recipe,
        inventory: Inventory,
        duration: Tick | int,
        job_id: str | None = None,
    ) -> ProductionJob:
        if not isinstance(recipe, Recipe):
            raise TypeError("recipe must be Recipe.")
        if not isinstance(inventory, Inventory):
            raise TypeError("inventory must be Inventory.")
        duration = self._coerce_duration(duration)
        job_id = self._resolve_job_id(job_id)
        if job_id in self._jobs:
            raise ValueError(f"Production job ID already exists: {job_id}")

        inventory_before = inventory.snapshot()
        action_id = production_action_id(job_id)
        consume_resources(inventory, recipe.inputs)
        action = None
        try:
            action = self._runtime.actions.create(
                Identifier(f"production_job:{job_id}"),
                duration,
                context={"production_job_id": job_id, "work_type": self.WORK_TYPE},
                action_id=action_id,
            )
            self._runtime.actions.schedule(action.action_id, self._runtime.current_tick)
        except Exception:
            if action is not None:
                try:
                    self._runtime.actions.cancel(action.action_id, "production scheduling failed")
                except Exception:
                    pass
            inventory._restore_snapshot(inventory_before)
            raise

        job = ProductionJob(
            job_id=job_id,
            recipe=recipe,
            inventory=inventory,
            start_tick=self._runtime.current_tick,
            duration=duration,
            action_id=action.action_id,
        )
        self._jobs[job_id] = job
        return job

    def cancel(self, job_id: str, cancellation: str = "cancelled") -> ProductionJob:
        job = self._require(job_id)
        if job.state not in {ProductionJobState.PLANNED, ProductionJobState.RUNNING}:
            raise ValueError("Production job cannot be cancelled in its current state.")

        before_refund = job.inventory.snapshot()
        self._refund_inputs(job)
        try:
            self._runtime.actions.cancel(job.action_id, cancellation)
        except Exception:
            job.inventory._restore_snapshot(before_refund)
            raise
        job._mark_cancelled()
        return job

    def advance_to(self, target_tick: Tick | int) -> tuple[SimulationEvent, ...]:
        events = self._runtime.advance_to(target_tick)
        self._runtime.dispatcher.dispatch_pending()
        return events

    def advance_by(self, delta: Tick | int) -> tuple[SimulationEvent, ...]:
        delta = delta if isinstance(delta, Tick) else Tick(delta)
        if delta.value < 0:
            raise ValueError("Simulation delta cannot be negative.")
        return self.advance_to(self._runtime.current_tick + delta)

    def consume(self, event: SimulationEvent) -> None:
        if not isinstance(event, SimulationEvent) or event.action_id is None:
            return
        job_id = event.target_id.value.removeprefix("production_job:") if event.target_id else None
        job = self._jobs.get(job_id) if job_id is not None else None
        if job is None or event.action_id != job.action_id:
            return

        if event.event_type == CanonicalEventType.ACTION_STARTED:
            job._mark_running()
        elif event.event_type == CanonicalEventType.ACTION_COMPLETED:
            self._complete(job)
        elif event.event_type == CanonicalEventType.ACTION_CANCELLED:
            if job.state in {ProductionJobState.PLANNED, ProductionJobState.RUNNING}:
                self._refund_inputs(job)
                job._mark_cancelled()
        elif event.event_type == CanonicalEventType.ACTION_FAILED:
            self._refund_inputs(job)
            job._mark_failed()

    def _complete(self, job: ProductionJob) -> None:
        if job.state != ProductionJobState.RUNNING:
            return
        before_outputs = job.inventory.snapshot()
        try:
            for resource_type, quantity in job.recipe.outputs:
                job.inventory.add(resource_type, quantity)
            job._mark_completed()
        except Exception:
            job.inventory._restore_snapshot(before_outputs)
            # Make the job terminal before attempting compensation. If refund
            # itself fails, a repeated completion event must not retry output or
            # refund and the false state "inputs refunded" must not be recorded.
            job._mark_failed()
            self._refund_inputs(job)
            raise

    @staticmethod
    def _refund_inputs(job: ProductionJob) -> None:
        if job.inputs_refunded:
            return
        before = job.inventory.snapshot()
        try:
            for resource_type, quantity in job.recipe.inputs:
                job.inventory.add(resource_type, quantity)
        except Exception:
            job.inventory._restore_snapshot(before)
            raise
        job._mark_inputs_refunded()

    def _resolve_job_id(self, job_id: str | None) -> str:
        if job_id is not None:
            if not isinstance(job_id, str) or not job_id.strip():
                raise ValueError("job_id cannot be empty.")
            return job_id
        while f"production_job_{self._next_job_id:06d}" in self._jobs:
            self._next_job_id += 1
        resolved = f"production_job_{self._next_job_id:06d}"
        self._next_job_id += 1
        return resolved

    @staticmethod
    def _coerce_duration(value: Tick | int) -> Tick:
        duration = value if isinstance(value, Tick) else Tick(value)
        if duration.value <= 0:
            raise ValueError("Production duration must be positive.")
        return duration

    def _require(self, job_id: str) -> ProductionJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Production job not found: {job_id}")
        return job
