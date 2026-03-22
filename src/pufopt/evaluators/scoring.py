"""Utility scoring for surviving candidates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from pufopt.types import Metrics, ScoreCard


@dataclass(frozen=True, slots=True)
class WeightConfig:
    security: float
    robustness: float
    efficiency: float
    operability: float


@dataclass(frozen=True, slots=True)
class ResultPolicy:
    survivor_required: bool
    frontier_update: bool
    score_threshold: float | None
    improvement_over_baseline: float | None
    surprising_margin: float | None


@dataclass(frozen=True, slots=True)
class ScoringConfig:
    weights: WeightConfig
    strong_result_policy: ResultPolicy


DEFAULT_SCORING_CONFIG_PATH = Path("configs/scoring/default.yaml")


def load_scoring_config(path: str | Path = DEFAULT_SCORING_CONFIG_PATH) -> ScoringConfig:
    """Load the utility-weight and result-policy portions of the config."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    weights = data.get("weights", {})
    strong = data.get("strong_result_policy", {})
    surprising = data.get("surprising_result_policy", {})

    return ScoringConfig(
        weights=WeightConfig(
            security=float(weights["security"]),
            robustness=float(weights["robustness"]),
            efficiency=float(weights["efficiency"]),
            operability=float(weights["operability"]),
        ),
        strong_result_policy=ResultPolicy(
            survivor_required=bool(strong.get("survivor_required", True)),
            frontier_update=bool(strong.get("frontier_update", False)),
            score_threshold=_optional_float(strong.get("score_threshold")),
            improvement_over_baseline=_optional_float(
                strong.get("improvement_over_baseline")
            ),
            surprising_margin=_optional_float(
                surprising.get("improvement_over_baseline")
            ),
        ),
    )


def score_candidate(
    scorecard: ScoreCard,
    config: ScoringConfig,
    *,
    frontier_updated: bool = False,
    baseline_utility: float | None = None,
) -> ScoreCard:
    """Attach utility and classification flags to a surviving score card."""
    if not scorecard.hard_constraint_passed:
        return scorecard

    metrics = scorecard.metrics
    utility = _compute_utility(metrics, config.weights)
    strong_result = _is_strong_result(
        utility,
        scorecard.is_survivor,
        config.strong_result_policy,
        frontier_updated=frontier_updated,
        baseline_utility=baseline_utility,
    )
    surprising_result = _is_surprising_result(
        utility,
        config.strong_result_policy,
        baseline_utility=baseline_utility,
    )

    return ScoreCard(
        candidate_id=scorecard.candidate_id,
        world_id=scorecard.world_id,
        disposition="survivor",
        utility=utility,
        hard_constraint_passed=True,
        is_survivor=True,
        strong_result=strong_result,
        surprising_result=surprising_result,
        reject_reasons=[],
        metrics=scorecard.metrics,
        proof_status=scorecard.proof_status,
        formal_claim_id=scorecard.formal_claim_id,
    )


def _compute_utility(metrics: Metrics, weights: WeightConfig) -> float:
    security_risk = max(
        _metric(metrics, "far"),
        _metric(metrics, "frr"),
        _optional_metric(metrics, "modeling_attack_success"),
        _optional_metric(metrics, "replay_attack_success"),
        _optional_metric(
            metrics,
            "counterfeit_attack_success",
            aliases=("nearest_match_attack_success",),
        ),
        _optional_metric(metrics, "crp_exhaustion_attack_success"),
        _optional_metric(metrics, "drift_abuse_attack_success"),
    )
    security_score = max(0.0, 1.0 - security_risk)
    robustness_score = _mean(
        _metric(metrics, "robustness_under_drift"),
        min(1.0, _metric(metrics, "min_entropy_estimate") / 8.0),
    )
    efficiency_score = _mean(
        1.0 - min(1.0, _metric(metrics, "latency_ms") / 50.0),
        1.0 - min(1.0, _metric(metrics, "readout_cost") / 2.0),
        1.0 - min(1.0, _metric(metrics, "enrollment_cost") / 50.0),
    )
    operability_score = _mean(
        min(1.0, _metric(metrics, "crp_lifetime") / 512.0),
        _metric(metrics, "confidence"),
    )

    total_weight = (
        weights.security + weights.robustness + weights.efficiency + weights.operability
    )
    weighted = (
        weights.security * security_score
        + weights.robustness * robustness_score
        + weights.efficiency * efficiency_score
        + weights.operability * operability_score
    )
    return round(weighted / total_weight, 6)


def _is_strong_result(
    utility: float,
    is_survivor: bool,
    policy: ResultPolicy,
    *,
    frontier_updated: bool,
    baseline_utility: float | None,
) -> bool:
    if policy.survivor_required and not is_survivor:
        return False
    if policy.frontier_update and frontier_updated:
        return True
    if policy.score_threshold is not None and utility >= policy.score_threshold:
        return True
    if (
        policy.improvement_over_baseline is not None
        and baseline_utility is not None
        and utility - baseline_utility >= policy.improvement_over_baseline
    ):
        return True
    return False


def _is_surprising_result(
    utility: float,
    policy: ResultPolicy,
    *,
    baseline_utility: float | None,
) -> bool:
    if policy.surprising_margin is None or baseline_utility is None:
        return False
    return utility - baseline_utility >= policy.surprising_margin


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _metric(metrics: Mapping[str, object], key: str) -> float:
    value = metrics.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"metric {key!r} must be numeric")
    return float(value)


def _optional_metric(
    metrics: Mapping[str, object],
    key: str,
    *,
    aliases: tuple[str, ...] = (),
) -> float:
    for name in (key, *aliases):
        value = metrics.get(name)
        if value is None:
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"metric {name!r} must be numeric")
        return float(value)
    return 0.0


def _mean(*values: float) -> float:
    return sum(values) / len(values)
