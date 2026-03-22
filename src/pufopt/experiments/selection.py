"""Next-experiment suggestion helpers."""

from __future__ import annotations

from typing import Any, Mapping


def suggest_next_action(snapshot: Mapping[str, Any]) -> dict[str, object]:
    """Suggest the next highest-value action from a frontier snapshot."""
    frontier = snapshot.get("frontier", [])
    if not isinstance(frontier, list) or not frontier:
        return {
            "action": "seed_more_candidates",
            "reason": "no surviving candidates yet; explore broader seed coverage",
        }

    best = frontier[0]
    if not isinstance(best, Mapping):
        return {
            "action": "inspect_frontier",
            "reason": "frontier data is malformed; repair artifacts before continuing",
        }

    metrics = best.get("metrics", {})
    if isinstance(metrics, Mapping):
        drift = _float_metric(metrics, "drift_abuse_attack_success")
        modeling = _float_metric(metrics, "modeling_attack_success")
        exhaustion = _float_metric(metrics, "crp_exhaustion_attack_success")
        if drift >= max(modeling, exhaustion) and drift >= 0.2:
            return {
                "action": "stress_drift_survivor",
                "reason": "best survivor still shows drift sensitivity worth falsifying",
                "candidate_id": best.get("candidate_id"),
            }
        if modeling >= 0.2:
            return {
                "action": "increase_modeling_pressure",
                "reason": "best survivor remains learnable under the current budget",
                "candidate_id": best.get("candidate_id"),
            }
        if exhaustion >= 0.2:
            return {
                "action": "extend_lifetime_tradeoff_search",
                "reason": "best survivor is limited by CRP exhaustion risk",
                "candidate_id": best.get("candidate_id"),
            }

    return {
        "action": "promote_frontier_candidate",
        "reason": "frontier leader survived current attack budgets; formalize or expand worlds",
        "candidate_id": best.get("candidate_id"),
    }


def _float_metric(metrics: Mapping[str, object], key: str) -> float:
    value = metrics.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return 0.0
    return float(value)
