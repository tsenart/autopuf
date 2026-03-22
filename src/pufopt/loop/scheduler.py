"""Scheduling decisions for optimization runs."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from pufopt.loop.frontier import FrontierState
from pufopt.types import CandidateSpec, PlanDecision


@dataclass(frozen=True, slots=True)
class SchedulerConfig:
    """Configurable scheduling mode."""

    mode: str = "balanced"
    falsification_interval: int = 3


@dataclass(slots=True)
class SchedulerState:
    """Mutable scheduler state across iterations."""

    world_cursor: int = 0
    queue: deque[CandidateSpec] = field(default_factory=deque)


def initialize_scheduler_state(seeds: list[CandidateSpec]) -> SchedulerState:
    """Create scheduler state from seed candidates."""
    return SchedulerState(queue=deque(seeds))


def pick_candidate(
    state: SchedulerState,
    frontier: FrontierState,
    candidate_index: dict[str, CandidateSpec],
    *,
    iteration: int,
    config: SchedulerConfig,
) -> tuple[CandidateSpec, PlanDecision]:
    """Pick the next candidate using a simple explore/exploit policy."""
    if not state.queue and not frontier.frontier:
        raise ValueError("scheduler has no queued or frontier candidates to evaluate")

    should_falsify = (
        frontier.frontier
        and config.mode in {"balanced", "exploit"}
        and config.falsification_interval > 0
        and iteration > 0
        and iteration % config.falsification_interval == 0
    )
    if should_falsify:
        best = frontier.best()
        if best is not None and best.candidate_id in candidate_index:
            candidate = candidate_index[best.candidate_id]
            return candidate, PlanDecision(
                action="falsify_frontier_candidate",
                reason="periodic re-evaluation of current frontier leader",
                candidate_id=candidate.id,
                metadata={"scheduler_mode": config.mode},
            )

    if config.mode == "exploit" and frontier.frontier:
        best = frontier.best()
        if best is not None and best.candidate_id in candidate_index:
            candidate = candidate_index[best.candidate_id]
            return candidate, PlanDecision(
                action="exploit_frontier_candidate",
                reason="exploit mode prefers the current best survivor",
                candidate_id=candidate.id,
                metadata={"scheduler_mode": config.mode},
            )

    if not state.queue:
        best = frontier.best()
        if best is None or best.candidate_id not in candidate_index:
            raise ValueError("scheduler cannot recover a candidate from the frontier")
        candidate = candidate_index[best.candidate_id]
        return candidate, PlanDecision(
            action="reuse_frontier_candidate",
            reason="queue is empty, reusing the best known survivor",
            candidate_id=candidate.id,
            metadata={"scheduler_mode": config.mode},
        )

    candidate = state.queue.popleft()
    return candidate, PlanDecision(
        action="evaluate_queue_candidate",
        reason="queue-driven exploration step",
        candidate_id=candidate.id,
        metadata={"scheduler_mode": config.mode, "queue_remaining": len(state.queue)},
    )


def pick_world(
    state: SchedulerState,
    worlds: list[str],
    *,
    candidate: CandidateSpec,
) -> tuple[str, PlanDecision]:
    """Pick the next world path in deterministic round-robin order."""
    if not worlds:
        raise ValueError("at least one world path is required")
    world_path = worlds[state.world_cursor % len(worlds)]
    state.world_cursor += 1
    world_name = Path(world_path).name
    return world_path, PlanDecision(
        action="select_world",
        reason="round-robin world selection for coverage",
        candidate_id=candidate.id,
        world_id=world_name,
        metadata={"world_index": state.world_cursor - 1},
    )


def enqueue_mutations(state: SchedulerState, mutations: list[CandidateSpec]) -> None:
    """Append mutations to the scheduler queue in deterministic order."""
    for mutation in sorted(mutations, key=lambda item: item.id):
        state.queue.append(mutation)
