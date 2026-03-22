"""CRP exhaustion attack heuristics."""

from __future__ import annotations

from pufopt.config import attack_family_config, attack_provenance
from pufopt.attacks.base import AttackBudget, clamp_success, numeric_param, register_attack_family
from pufopt.types import AttackResult, BuiltCandidate, WorldInstance


@register_attack_family("crp_exhaustion")
def run_crp_exhaustion_attack(
    candidate: BuiltCandidate,
    world: WorldInstance,
    budget: AttackBudget,
) -> AttackResult:
    """Model safe-session collapse under bounded query pressure."""
    family_config = attack_family_config("crp_exhaustion", candidate.family)
    provenance = attack_provenance("crp_exhaustion", candidate.family)
    query_factor = min(1.0, budget.queries / float(family_config["query_reference"]))

    if candidate.family == "classical_crp":
        challenge_space_size = max(
            1.0, numeric_param(candidate.params, "challenge_space_size", 128.0)
        )
        replay_window = max(1.0, numeric_param(candidate.params, "replay_window", 1.0))
        lifetime = max(1.0, challenge_space_size / replay_window)
        success = clamp_success(
            float(family_config["base"])
            + float(family_config["query_factor_weight"]) * query_factor
            + float(family_config["lifetime_weight"])
            * min(1.0, float(family_config["lifetime_reference"]) / lifetime)
        )
        reduced_lifetime = max(1, int(lifetime - min(lifetime - 1, budget.queries // int(replay_window))))
    elif candidate.family == "optical_auth":
        enrollment_samples = max(
            1.0, numeric_param(candidate.params, "enrollment_samples", 32.0)
        )
        lifetime = max(1.0, enrollment_samples * 4.0)
        success = clamp_success(
            float(family_config["base"])
            + float(family_config["query_factor_weight"]) * query_factor
            + float(family_config["lifetime_weight"])
            * min(1.0, float(family_config["lifetime_reference"]) / lifetime)
        )
        reduced_lifetime = max(
            1,
            int(
                lifetime
                - min(
                    lifetime - 1,
                    budget.queries // int(family_config["queries_per_session"]),
                )
            ),
        )
    else:
        raise ValueError(f"unsupported candidate family for CRP exhaustion attack: {candidate.family}")

    return AttackResult(
        name="crp_exhaustion",
        success=success,
        metrics={
            "attack_success": success,
            "reduced_crp_lifetime": reduced_lifetime,
            "calibration_status": provenance["calibration_status"],
            "citation_status": provenance["citation_status"],
            "provenance_ref": provenance["provenance_ref"],
        },
        traces=[f"reduced_crp_lifetime={reduced_lifetime}", f"success={success:.6f}"],
        params=budget.as_params(),
        notes=(
            f"calibration_status={provenance['calibration_status']}; "
            f"provenance_ref={provenance['provenance_ref']}"
        ),
    )
