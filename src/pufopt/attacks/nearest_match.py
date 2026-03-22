"""Nearest-match counterfeit attack heuristics."""

from __future__ import annotations

from pufopt.attacks.base import AttackBudget, clamp_success, numeric_param, register_attack_family
from pufopt.types import AttackResult, BuiltCandidate, WorldInstance


@register_attack_family("nearest_match")
def run_nearest_match_attack(
    candidate: BuiltCandidate,
    world: WorldInstance,
    budget: AttackBudget,
) -> AttackResult:
    """Run a heuristic nearest-match counterfeit attack."""
    search_factor = min(1.0, budget.search_steps / 128.0)
    noise = numeric_param(
        world.params, "observed_sensor_noise_sigma", numeric_param(world.params, "sensor_noise_sigma", 0.02)
    )

    if candidate.family == "classical_crp":
        threshold = numeric_param(candidate.params, "threshold", 0.1)
        challenge_factor = min(
            1.0,
            64.0 / max(1.0, numeric_param(candidate.params, "challenge_space_size", 128.0)),
        )
        success = clamp_success(
            0.10 + 0.3 * threshold + 0.22 * challenge_factor + 0.18 * search_factor - 1.0 * noise
        )
    elif candidate.family == "optical_auth":
        feature_factor = min(
            1.0,
            64.0 / max(1.0, numeric_param(candidate.params, "feature_dimension", 64.0)),
        )
        illumination = numeric_param(
            world.params,
            "observed_illumination_jitter",
            numeric_param(world.params, "illumination_jitter", 0.12),
        )
        success = clamp_success(
            0.08 + 0.28 * feature_factor + 0.22 * search_factor - 0.8 * noise - 0.25 * illumination
        )
    else:
        raise ValueError(f"unsupported candidate family for nearest-match attack: {candidate.family}")

    return AttackResult(
        name="nearest_match",
        success=success,
        metrics={
            "attack_success": success,
            "search_steps": budget.search_steps,
        },
        traces=[f"nearest_match_success={success:.6f}"],
        params=budget.as_params(),
    )

