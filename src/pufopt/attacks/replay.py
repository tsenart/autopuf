"""Replay attack heuristics."""

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


@register_attack_family("replay")
def run_replay_attack(
    candidate: BuiltCandidate,
    world: WorldInstance,
    budget: AttackBudget,
) -> AttackResult:
    """Run a replay-style attack under observation and query budgets."""
    family_config = attack_family_config("replay", candidate.family)
    provenance = attack_provenance("replay", candidate.family)
    observation_factor = min(
        1.0,
        budget.observations / float(family_config["observation_reference"]),
    )
    noise = numeric_param(
        world.params, "observed_sensor_noise_sigma", numeric_param(world.params, "sensor_noise_sigma", 0.02)
    )

    if candidate.family == "classical_crp":
        replay_window = max(1.0, numeric_param(candidate.params, "replay_window", 1.0))
        success = clamp_success(
            float(family_config["base"])
            + float(family_config["window_inverse_weight"]) * (1.0 / replay_window)
            + float(family_config["observation_factor_weight"]) * observation_factor
            + float(family_config["noise_weight"]) * noise
        )
    elif candidate.family == "optical_auth":
        session_policy = string_param(candidate.params, "session_policy", "one_time_use")
        policy_bonus = float(
            family_config["session_policy_bonus"].get(
                session_policy,
                family_config["session_policy_bonus"]["bounded_reuse"],
            )
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
            + policy_bonus
            + trust_bonus
            + float(family_config["observation_factor_weight"]) * observation_factor
            + float(family_config["noise_weight"]) * noise
            + float(family_config["illumination_weight"]) * illumination
        )
    else:
        raise ValueError(f"unsupported candidate family for replay attack: {candidate.family}")

    return AttackResult(
        name="replay",
        success=success,
        metrics={
            "attack_success": success,
            "observations_used": min(budget.observations, budget.queries),
            "calibration_status": provenance["calibration_status"],
            "citation_status": provenance["citation_status"],
            "provenance_ref": provenance["provenance_ref"],
        },
        traces=[f"replay_success={success:.6f}", f"observations={budget.observations}"],
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
