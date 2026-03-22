"""Drift abuse attack heuristics."""

from __future__ import annotations

from pufopt.attacks.base import AttackBudget, clamp_success, numeric_param, register_attack_family
from pufopt.types import AttackResult, BuiltCandidate, WorldInstance


@register_attack_family("drift_abuse")
def run_drift_abuse_attack(
    candidate: BuiltCandidate,
    world: WorldInstance,
    budget: AttackBudget,
) -> AttackResult:
    """Exploit allowed environmental drift to induce errors."""
    search_factor = min(1.0, budget.search_steps / 128.0)
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
        success = clamp_success(0.05 + 0.16 * search_factor + 1.8 * noise)
    elif candidate.family == "optical_auth":
        success = clamp_success(
            0.07 + 0.18 * search_factor + 1.4 * noise + 0.5 * illumination + angle / 120.0
        )
    else:
        raise ValueError(f"unsupported candidate family for drift abuse attack: {candidate.family}")

    return AttackResult(
        name="drift_abuse",
        success=success,
        metrics={
            "attack_success": success,
            "induced_false_accept_or_reject": success,
        },
        traces=[f"drift_abuse_success={success:.6f}"],
        params=budget.as_params(),
    )

