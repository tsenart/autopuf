"""Adversarial evaluation orchestration."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from pufopt.attacks import normalize_attack_budget, run_attack
from pufopt.types import AttackResult, BuiltCandidate, EvaluationResult, Metrics, WorldInstance

REQUIRED_V1_ATTACKS: tuple[str, ...] = (
    "modeling",
    "replay",
    "nearest_match",
    "crp_exhaustion",
    "drift_abuse",
)
CANONICAL_ATTACK_METRICS: dict[str, tuple[str, ...]] = {
    "modeling": ("modeling_attack_success",),
    "replay": ("replay_attack_success",),
    "nearest_match": ("nearest_match_attack_success", "counterfeit_attack_success"),
    "crp_exhaustion": ("crp_exhaustion_attack_success",),
    "drift_abuse": ("drift_abuse_attack_success",),
}


def run_attacks(
    candidate: BuiltCandidate,
    world: WorldInstance,
    attack_names: Iterable[str] = REQUIRED_V1_ATTACKS,
    budget: Mapping[str, object] | None = None,
) -> list[AttackResult]:
    """Run the requested attack families."""
    resolved_budget = normalize_attack_budget(budget)
    return [
        run_attack(name, candidate, world, resolved_budget)
        for name in attack_names
    ]


def merge_attack_metrics(
    honest_metrics: Metrics,
    attacks: Iterable[AttackResult],
) -> Metrics:
    """Augment honest metrics with canonical attack-success fields."""
    merged = dict(honest_metrics)
    for attack in attacks:
        for metric_name in CANONICAL_ATTACK_METRICS.get(
            attack.name,
            (f"{attack.name}_attack_success",),
        ):
            merged[metric_name] = attack.success or 0.0
    return merged


def evaluate_with_attacks(
    candidate: BuiltCandidate,
    world: WorldInstance,
    honest_metrics: Metrics,
    attack_names: Iterable[str] = REQUIRED_V1_ATTACKS,
    budget: Mapping[str, object] | None = None,
    *,
    seed: int | None = None,
) -> EvaluationResult:
    """Run all requested attacks and package the combined result."""
    attacks = run_attacks(candidate, world, attack_names=attack_names, budget=budget)
    merged_metrics = merge_attack_metrics(honest_metrics, attacks)
    return EvaluationResult(
        candidate_id=candidate.id,
        world_id=world.id,
        honest_metrics=merged_metrics,
        attacks=attacks,
        seeds={"evaluation": seed} if seed is not None else {},
        artifacts={},
    )
