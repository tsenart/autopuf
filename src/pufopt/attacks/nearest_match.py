"""Nearest-match counterfeit attack heuristics."""

from __future__ import annotations

from pufopt.config import attack_family_config, attack_provenance
from pufopt.attacks.base import (
    AttackBudget,
    clamp_success,
    numeric_param,
    register_attack_family,
    string_param,
)
from pufopt.types import AttackResult, BuiltCandidate, WorldInstance


@register_attack_family("nearest_match")
def run_nearest_match_attack(
    candidate: BuiltCandidate,
    world: WorldInstance,
    budget: AttackBudget,
) -> AttackResult:
    """Run a heuristic nearest-match counterfeit attack."""
    family_config = attack_family_config("nearest_match", candidate.family)
    provenance = attack_provenance("nearest_match", candidate.family)
    search_factor = min(
        1.0,
        budget.search_steps / float(family_config["search_step_reference"]),
    )
    noise = numeric_param(
        world.params, "observed_sensor_noise_sigma", numeric_param(world.params, "sensor_noise_sigma", 0.02)
    )

    if candidate.family == "classical_crp":
        threshold = numeric_param(candidate.params, "threshold", 0.1)
        challenge_factor = min(
            1.0,
            float(family_config["challenge_space_reference"])
            / max(1.0, numeric_param(candidate.params, "challenge_space_size", 128.0)),
        )
        success = clamp_success(
            float(family_config["base"])
            + float(family_config["threshold_weight"]) * threshold
            + float(family_config["challenge_factor_weight"]) * challenge_factor
            + float(family_config["search_factor_weight"]) * search_factor
            + float(family_config["noise_weight"]) * noise
        )
    elif candidate.family == "optical_auth":
        feature_factor = min(
            1.0,
            float(family_config["feature_dimension_reference"])
            / max(1.0, numeric_param(candidate.params, "feature_dimension", 64.0)),
        )
        verifier_model = string_param(world.params, "verifier_model", "honest")
        template_leakage = max(
            0.0,
            min(1.0, numeric_param(world.params, "template_leakage", 0.0)),
        )
        trust_bonus = _verifier_bonus(
            verifier_model,
            family_config["verifier_bonus"],
        ) + float(family_config["template_leakage_weight"]) * template_leakage
        illumination = numeric_param(
            world.params,
            "observed_illumination_jitter",
            numeric_param(world.params, "illumination_jitter", 0.12),
        )
        success = clamp_success(
            float(family_config["base"])
            + float(family_config["feature_factor_weight"]) * feature_factor
            + trust_bonus
            + float(family_config["search_factor_weight"]) * search_factor
            + float(family_config["noise_weight"]) * noise
            + float(family_config["illumination_weight"]) * illumination
        )
    else:
        raise ValueError(f"unsupported candidate family for nearest-match attack: {candidate.family}")

    return AttackResult(
        name="nearest_match",
        success=success,
        metrics={
            "attack_success": success,
            "search_steps": budget.search_steps,
            "calibration_status": provenance["calibration_status"],
            "citation_status": provenance["citation_status"],
            "provenance_ref": provenance["provenance_ref"],
        },
        traces=[f"nearest_match_success={success:.6f}"],
        params=budget.as_params(),
        notes=(
            f"calibration_status={provenance['calibration_status']}; "
            f"provenance_ref={provenance['provenance_ref']}"
        ),
    )


def _verifier_bonus(verifier_model: str, mapping: dict[str, object]) -> float:
    value = mapping.get(verifier_model, mapping.get("default", 0.0))
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError("verifier bonus config must be numeric")
    return float(value)
