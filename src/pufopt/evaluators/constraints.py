"""Constraint evaluation for honest and adversarial metrics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from pufopt.types import Metrics, ScoreCard


@dataclass(frozen=True, slots=True)
class ConstraintConfig:
    max_far: float
    max_frr: float
    max_latency_ms: float
    min_crp_lifetime: int
    max_readout_cost: float
    min_confidence: float


DEFAULT_SCORING_CONFIG_PATH = Path("configs/scoring/default.yaml")


def load_constraint_config(path: str | Path = DEFAULT_SCORING_CONFIG_PATH) -> ConstraintConfig:
    """Load the hard-constraint section from the scoring config."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    constraints = data.get("constraints", {})
    return ConstraintConfig(
        max_far=float(constraints["max_far"]),
        max_frr=float(constraints["max_frr"]),
        max_latency_ms=float(constraints["max_latency_ms"]),
        min_crp_lifetime=int(constraints["min_crp_lifetime"]),
        max_readout_cost=float(constraints["max_readout_cost"]),
        min_confidence=float(constraints["min_confidence"]),
    )


def apply_constraints(
    candidate_id: str,
    world_id: str,
    metrics: Metrics,
    config: ConstraintConfig,
) -> ScoreCard:
    """Apply hard constraints and return a score card with explicit reasons."""
    reasons: list[str] = []

    if _metric(metrics, "far") > config.max_far:
        reasons.append(f"far exceeds max_far ({metrics['far']} > {config.max_far})")
    if _metric(metrics, "frr") > config.max_frr:
        reasons.append(f"frr exceeds max_frr ({metrics['frr']} > {config.max_frr})")
    if _metric(metrics, "latency_ms") > config.max_latency_ms:
        reasons.append(
            f"latency_ms exceeds max_latency_ms ({metrics['latency_ms']} > {config.max_latency_ms})"
        )
    if int(_metric(metrics, "crp_lifetime")) < config.min_crp_lifetime:
        reasons.append(
            f"crp_lifetime below min_crp_lifetime ({metrics['crp_lifetime']} < {config.min_crp_lifetime})"
        )
    if _metric(metrics, "readout_cost") > config.max_readout_cost:
        reasons.append(
            f"readout_cost exceeds max_readout_cost ({metrics['readout_cost']} > {config.max_readout_cost})"
        )
    if _metric(metrics, "confidence") < config.min_confidence:
        reasons.append(
            f"confidence below min_confidence ({metrics['confidence']} < {config.min_confidence})"
        )

    if reasons:
        return ScoreCard(
            candidate_id=candidate_id,
            world_id=world_id,
            disposition="rejected",
            hard_constraint_passed=False,
            is_survivor=False,
            reject_reasons=reasons,
            metrics=metrics,
        )

    return ScoreCard(
        candidate_id=candidate_id,
        world_id=world_id,
        disposition="valid",
        hard_constraint_passed=True,
        is_survivor=True,
        reject_reasons=[],
        metrics=metrics,
    )


def _metric(metrics: Mapping[str, object], key: str) -> float:
    value = metrics.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"metric {key!r} must be numeric")
    return float(value)

