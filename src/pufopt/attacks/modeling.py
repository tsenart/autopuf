"""Modeling attack heuristics."""

from __future__ import annotations

from pufopt.config import attack_family_config, attack_provenance
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
    root_config = attack_family_config("modeling", candidate.family)
    provenance = attack_provenance("modeling", candidate.family)
    budget_factor = min(1.0, budget.queries / float(root_config["budget_query_reference"]))

    if candidate.family == "classical_crp":
        family_config = root_config
        challenge_factor = min(
            1.0,
            float(family_config["challenge_space_reference"])
            / max(1.0, numeric_param(candidate.params, "challenge_space_size", 128.0)),
        )
        response_factor = min(
            1.0,
            float(family_config["response_width_reference"])
            / max(1.0, numeric_param(candidate.params, "response_bit_width", 1.0)),
        )
        models = family_config["models"]
        model_scores = {
            "linear_probe": clamp_success(
                float(models["linear_probe"]["base"])
                + float(models["linear_probe"]["challenge_factor"]) * challenge_factor
                + float(models["linear_probe"]["budget_factor"]) * budget_factor
                + float(models["linear_probe"]["response_factor"]) * response_factor
                + float(models["linear_probe"]["observed_noise"]) * observed_noise
            ),
            "tree_probe": clamp_success(
                float(models["tree_probe"]["base"])
                + float(models["tree_probe"]["challenge_factor"]) * challenge_factor
                + float(models["tree_probe"]["budget_factor"]) * budget_factor
                + float(models["tree_probe"]["response_factor"]) * response_factor
                + float(models["tree_probe"]["observed_noise"]) * observed_noise
            ),
            "kernel_probe": clamp_success(
                float(models["kernel_probe"]["base"])
                + float(models["kernel_probe"]["challenge_factor"]) * challenge_factor
                + float(models["kernel_probe"]["budget_factor"]) * budget_factor
                + float(models["kernel_probe"]["response_factor"]) * response_factor
                + float(models["kernel_probe"]["observed_noise"]) * observed_noise
            ),
        }
    elif candidate.family == "optical_auth":
        family_config = root_config
        feature_factor = min(
            1.0,
            float(family_config["feature_dimension_reference"])
            / max(1.0, numeric_param(candidate.params, "feature_dimension", 64.0)),
        )
        enrollment_factor = min(
            1.0,
            float(family_config["enrollment_reference"])
            / max(1.0, numeric_param(candidate.params, "enrollment_samples", 32.0)),
        )
        illumination = numeric_param(
            world.params,
            "observed_illumination_jitter",
            numeric_param(world.params, "illumination_jitter", 0.12),
        )
        models = family_config["models"]
        model_scores = {
            "linear_probe": clamp_success(
                float(models["linear_probe"]["base"])
                + float(models["linear_probe"]["feature_factor"]) * feature_factor
                + float(models["linear_probe"]["enrollment_factor"]) * enrollment_factor
                + float(models["linear_probe"]["budget_factor"]) * budget_factor
                + float(models["linear_probe"]["observed_noise"]) * observed_noise
                + float(models["linear_probe"]["illumination"]) * illumination
            ),
            "tree_probe": clamp_success(
                float(models["tree_probe"]["base"])
                + float(models["tree_probe"]["feature_factor"]) * feature_factor
                + float(models["tree_probe"]["enrollment_factor"]) * enrollment_factor
                + float(models["tree_probe"]["budget_factor"]) * budget_factor
                + float(models["tree_probe"]["observed_noise"]) * observed_noise
                + float(models["tree_probe"]["illumination"]) * illumination
            ),
            "kernel_probe": clamp_success(
                float(models["kernel_probe"]["base"])
                + float(models["kernel_probe"]["feature_factor"]) * feature_factor
                + float(models["kernel_probe"]["enrollment_factor"]) * enrollment_factor
                + float(models["kernel_probe"]["budget_factor"]) * budget_factor
                + float(models["kernel_probe"]["observed_noise"]) * observed_noise
                + float(models["kernel_probe"]["illumination"]) * illumination
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
            "calibration_status": provenance["calibration_status"],
            "citation_status": provenance["citation_status"],
            "provenance_ref": provenance["provenance_ref"],
        },
        traces=[f"{model}: {score:.6f}" for model, score in model_scores.items()],
        params=budget.as_params(),
        notes=(
            f"best_model={best_model}; "
            f"calibration_status={provenance['calibration_status']}; "
            f"provenance_ref={provenance['provenance_ref']}"
        ),
    )
