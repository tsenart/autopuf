"""Frontier maintenance for optimization runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import inf

from pufopt.types import FrontierEntry, ScoreCard


@dataclass(frozen=True, slots=True)
class FrontierUpdate:
    """Summary of one frontier update attempt."""

    candidate_id: str
    family: str
    status: str
    frontier_updated: bool
    removed_candidate_ids: list[str] = field(default_factory=list)
    frontier_size: int = 0
    dominated_size: int = 0
    rejected_size: int = 0


@dataclass(slots=True)
class FrontierState:
    """Deterministic frontier state for one optimization run."""

    frontier: list[FrontierEntry] = field(default_factory=list)
    dominated: list[FrontierEntry] = field(default_factory=list)
    rejected: list[dict[str, object]] = field(default_factory=list)

    def update(self, scorecard: ScoreCard, *, family: str) -> FrontierUpdate:
        """Update the frontier with one candidate result."""
        self._drop_existing(scorecard.candidate_id)

        if (
            not scorecard.hard_constraint_passed
            or not scorecard.is_survivor
            or scorecard.utility is None
        ):
            self.rejected.append(
                {
                    "candidate_id": scorecard.candidate_id,
                    "world_id": scorecard.world_id,
                    "family": family,
                    "reject_reasons": list(scorecard.reject_reasons),
                }
            )
            self._sort_rejected()
            return FrontierUpdate(
                candidate_id=scorecard.candidate_id,
                family=family,
                status="rejected",
                frontier_updated=False,
                frontier_size=len(self.frontier),
                dominated_size=len(self.dominated),
                rejected_size=len(self.rejected),
            )

        entry = FrontierEntry(
            candidate_id=scorecard.candidate_id,
            family=family,
            utility=scorecard.utility,
            metrics=dict(scorecard.metrics),
            formal_claim_id=scorecard.formal_claim_id,
            proof_status=scorecard.proof_status,
        )

        dominators = [other for other in self.frontier if _dominates(other, entry)]
        if dominators:
            self.dominated.append(entry)
            self._sort_entries()
            return FrontierUpdate(
                candidate_id=entry.candidate_id,
                family=family,
                status="dominated",
                frontier_updated=False,
                frontier_size=len(self.frontier),
                dominated_size=len(self.dominated),
                rejected_size=len(self.rejected),
            )

        removed = [other for other in self.frontier if _dominates(entry, other)]
        if removed:
            removed_ids = {item.candidate_id for item in removed}
            self.frontier = [
                other for other in self.frontier if other.candidate_id not in removed_ids
            ]
            self.dominated.extend(removed)
        else:
            removed_ids = set()

        self.frontier.append(entry)
        self._sort_entries()
        return FrontierUpdate(
            candidate_id=entry.candidate_id,
            family=family,
            status="frontier",
            frontier_updated=True,
            removed_candidate_ids=sorted(removed_ids),
            frontier_size=len(self.frontier),
            dominated_size=len(self.dominated),
            rejected_size=len(self.rejected),
        )

    def snapshot(
        self,
        *,
        run_id: str | None = None,
        update: FrontierUpdate | None = None,
    ) -> dict[str, object]:
        """Serialize the frontier state for artifacts and reporting."""
        payload: dict[str, object] = {
            "run_id": run_id,
            "frontier": [asdict(entry) for entry in self.frontier],
            "dominated": [asdict(entry) for entry in self.dominated],
            "rejected": list(self.rejected),
            "counts": {
                "frontier": len(self.frontier),
                "dominated": len(self.dominated),
                "rejected": len(self.rejected),
            },
        }
        if update is not None:
            payload["last_update"] = asdict(update)
        return payload

    def best(self) -> FrontierEntry | None:
        """Return the current best frontier entry by deterministic ordering."""
        return self.frontier[0] if self.frontier else None

    def _drop_existing(self, candidate_id: str) -> None:
        self.frontier = [
            entry for entry in self.frontier if entry.candidate_id != candidate_id
        ]
        self.dominated = [
            entry for entry in self.dominated if entry.candidate_id != candidate_id
        ]
        self.rejected = [
            entry for entry in self.rejected if entry["candidate_id"] != candidate_id
        ]

    def _sort_entries(self) -> None:
        self.frontier.sort(key=_entry_sort_key)
        self.dominated.sort(key=_entry_sort_key)

    def _sort_rejected(self) -> None:
        self.rejected.sort(
            key=lambda item: (
                str(item["family"]),
                str(item["candidate_id"]),
                str(item["world_id"]),
            )
        )


def _dominates(left: FrontierEntry, right: FrontierEntry) -> bool:
    left_checks = (
        left.utility >= right.utility,
        _min_metric(left, "far") <= _min_metric(right, "far"),
        _min_metric(left, "frr") <= _min_metric(right, "frr"),
        _min_metric(left, "latency_ms") <= _min_metric(right, "latency_ms"),
        _min_metric(left, "readout_cost") <= _min_metric(right, "readout_cost"),
        _max_metric(left, "robustness_under_drift")
        >= _max_metric(right, "robustness_under_drift"),
        _max_metric(left, "crp_lifetime") >= _max_metric(right, "crp_lifetime"),
    )
    if not all(left_checks):
        return False

    strict_checks = (
        left.utility > right.utility,
        _min_metric(left, "far") < _min_metric(right, "far"),
        _min_metric(left, "frr") < _min_metric(right, "frr"),
        _min_metric(left, "latency_ms") < _min_metric(right, "latency_ms"),
        _min_metric(left, "readout_cost") < _min_metric(right, "readout_cost"),
        _max_metric(left, "robustness_under_drift")
        > _max_metric(right, "robustness_under_drift"),
        _max_metric(left, "crp_lifetime") > _max_metric(right, "crp_lifetime"),
    )
    return any(strict_checks)


def _entry_sort_key(entry: FrontierEntry) -> tuple[float, str, str]:
    return (-entry.utility, entry.family, entry.candidate_id)


def _min_metric(entry: FrontierEntry, key: str) -> float:
    value = entry.metrics.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return inf
    return float(value)


def _max_metric(entry: FrontierEntry, key: str) -> float:
    value = entry.metrics.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return 0.0
    return float(value)
