"""Replay attack heuristics."""

from __future__ import annotations

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
    observation_factor = min(1.0, budget.observations / 128.0)
    noise = numeric_param(
        world.params, "observed_sensor_noise_sigma", numeric_param(world.params, "sensor_noise_sigma", 0.02)
    )

    if candidate.family == "classical_crp":
        replay_window = max(1.0, numeric_param(candidate.params, "replay_window", 1.0))
        success = clamp_success(
            0.18 + 0.48 * (1.0 / replay_window) + 0.18 * observation_factor - 1.2 * noise
        )
    elif candidate.family == "optical_auth":
        session_policy = string_param(candidate.params, "session_policy", "one_time_use")
        policy_bonus = 0.08 if session_policy == "one_time_use" else 0.28
        illumination = numeric_param(
            world.params,
            "observed_illumination_jitter",
            numeric_param(world.params, "illumination_jitter", 0.12),
        )
        success = clamp_success(
            0.05 + policy_bonus + 0.12 * observation_factor - 0.8 * noise - 0.2 * illumination
        )
    else:
        raise ValueError(f"unsupported candidate family for replay attack: {candidate.family}")

    return AttackResult(
        name="replay",
        success=success,
        metrics={
            "attack_success": success,
            "observations_used": min(budget.observations, budget.queries),
        },
        traces=[f"replay_success={success:.6f}", f"observations={budget.observations}"],
        params=budget.as_params(),
    )

