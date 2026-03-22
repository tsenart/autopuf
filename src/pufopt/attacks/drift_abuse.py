"""Drift abuse attack heuristics."""

from __future__ import annotations

from pufopt.config import attack_family_config, attack_provenance
from pufopt.attacks.base import AttackBudget, clamp_success, numeric_param, register_attack_family
from pufopt.types import AttackResult, BuiltCandidate, WorldInstance


@register_attack_family("drift_abuse")
def run_drift_abuse_attack(
    candidate: BuiltCandidate,
    world: WorldInstance,
    budget: AttackBudget,
) -> AttackResult:
    """Exploit allowed environmental drift to induce errors."""
    family_config = attack_family_config("drift_abuse", candidate.family)
    provenance = attack_provenance("drift_abuse", candidate.family)
    search_factor = min(
        1.0,
        budget.search_steps / float(family_config["search_step_reference"]),
    )
    noise = numeric_param(
        world.params, "observed_sensor_noise_sigma", numeric_param(world.params, "sensor_noise_sigma", 0.02)
    )
    illumination = numeric_param(
        world.params,
        "observed_illumination_jitter",
        numeric_param(world.params, "illumination_jitter", 0.05),
    )
    angle = numeric_param(
        world.params,
        "observed_angle_variation_deg",
        numeric_param(world.params, "angle_variation_deg", 0.0),
    )

    if candidate.family == "classical_crp":
        success = clamp_success(
            float(family_config["base"])
            + float(family_config["search_factor_weight"]) * search_factor
            + float(family_config["noise_weight"]) * noise
        )
    elif candidate.family == "optical_auth":
        success = clamp_success(
            float(family_config["base"])
            + float(family_config["search_factor_weight"]) * search_factor
            + float(family_config["noise_weight"]) * noise
            + float(family_config["illumination_weight"]) * illumination
            + angle / float(family_config["angle_divisor"])
        )
    else:
        raise ValueError(f"unsupported candidate family for drift abuse attack: {candidate.family}")

    return AttackResult(
        name="drift_abuse",
        success=success,
        metrics={
            "attack_success": success,
            "induced_false_accept_or_reject": success,
            "calibration_status": provenance["calibration_status"],
            "citation_status": provenance["citation_status"],
            "provenance_ref": provenance["provenance_ref"],
        },
        traces=[f"drift_abuse_success={success:.6f}"],
        params=budget.as_params(),
        notes=(
            f"calibration_status={provenance['calibration_status']}; "
            f"provenance_ref={provenance['provenance_ref']}"
        ),
    )
