"""Modeling attack heuristics."""

from __future__ import annotations

from pufopt.attacks.base import (
    AttackBudget,
    clamp_success,
    numeric_param,
    register_attack_family,
)
from pufopt.types import AttackResult, BuiltCandidate, WorldInstance


@register_attack_family("modeling")
def run_modeling_attack(
    candidate: BuiltCandidate,
    world: WorldInstance,
    budget: AttackBudget,
) -> AttackResult:
    """Run a heuristic modeling attack across several simple model families."""
    observed_noise = numeric_param(
        world.params, "observed_sensor_noise_sigma", numeric_param(world.params, "sensor_noise_sigma", 0.02)
    )
    budget_factor = min(1.0, budget.queries / 1_000.0)

    if candidate.family == "classical_crp":
        challenge_factor = min(
            1.0,
            128.0 / max(1.0, numeric_param(candidate.params, "challenge_space_size", 128.0)),
        )
        response_factor = min(
            1.0,
            1.0 / max(1.0, numeric_param(candidate.params, "response_bit_width", 1.0)),
        )
        model_scores = {
            "linear_probe": clamp_success(
                0.12 + 0.28 * challenge_factor + 0.18 * budget_factor + 0.05 * response_factor - 1.8 * observed_noise
            ),
            "tree_probe": clamp_success(
                0.18 + 0.36 * challenge_factor + 0.22 * budget_factor + 0.06 * response_factor - 1.4 * observed_noise
            ),
            "kernel_probe": clamp_success(
                0.16 + 0.32 * challenge_factor + 0.25 * budget_factor + 0.08 * response_factor - 1.2 * observed_noise
            ),
        }
    elif candidate.family == "optical_auth":
        feature_factor = min(
            1.0,
            64.0 / max(1.0, numeric_param(candidate.params, "feature_dimension", 64.0)),
        )
        enrollment_factor = min(
            1.0,
            32.0 / max(1.0, numeric_param(candidate.params, "enrollment_samples", 32.0)),
        )
        illumination = numeric_param(
            world.params,
            "observed_illumination_jitter",
            numeric_param(world.params, "illumination_jitter", 0.12),
        )
        model_scores = {
            "linear_probe": clamp_success(
                0.08 + 0.20 * feature_factor + 0.16 * enrollment_factor + 0.14 * budget_factor - 1.4 * observed_noise - 0.4 * illumination
            ),
            "tree_probe": clamp_success(
                0.10 + 0.24 * feature_factor + 0.18 * enrollment_factor + 0.18 * budget_factor - 1.2 * observed_noise - 0.35 * illumination
            ),
            "kernel_probe": clamp_success(
                0.11 + 0.28 * feature_factor + 0.14 * enrollment_factor + 0.2 * budget_factor - 1.0 * observed_noise - 0.3 * illumination
            ),
        }
    else:
        raise ValueError(f"unsupported candidate family for modeling attack: {candidate.family}")

    best_model = max(model_scores, key=model_scores.get)
    best_success = model_scores[best_model]
    return AttackResult(
        name="modeling",
        success=best_success,
        metrics={
            "attack_success": best_success,
            "best_model": best_model,
            "budget_queries": budget.queries,
            "budget_observations": budget.observations,
        },
        traces=[f"{model}: {score:.6f}" for model, score in model_scores.items()],
        params=budget.as_params(),
        notes=f"best_model={best_model}",
    )

