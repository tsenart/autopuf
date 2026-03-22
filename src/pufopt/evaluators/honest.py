"""Honest candidate evaluation."""

from __future__ import annotations

from typing import Mapping

from pufopt.storage.io import write_json_atomic
from pufopt.types import BuiltCandidate, Metrics, WorldInstance


class HonestEvaluationError(ValueError):
    """Raised when honest metrics cannot be computed."""


def evaluate_honest(candidate: BuiltCandidate, world: WorldInstance) -> Metrics:
    """Compute deterministic honest metrics for a candidate in a world."""
    if candidate.family == "classical_crp":
        return _evaluate_classical_crp(candidate.params, world.params)
    if candidate.family == "optical_auth":
        return _evaluate_optical_auth(candidate.params, world.params)
    raise HonestEvaluationError(f"unsupported candidate family {candidate.family!r}")


def write_metrics_artifact(
    output_path: str,
    candidate: BuiltCandidate,
    world: WorldInstance,
) -> str:
    """Evaluate honestly and write the resulting metrics as JSON."""
    metrics = evaluate_honest(candidate, world)
    payload = {
        "candidate_id": candidate.id,
        "world_id": world.id,
        "metrics": metrics,
    }
    write_json_atomic(output_path, payload)
    return output_path


def _evaluate_classical_crp(
    candidate_params: Mapping[str, object],
    world_params: Mapping[str, object],
) -> Metrics:
    challenge_space_size = _require_positive_int(
        candidate_params, "challenge_space_size", "classical_crp"
    )
    response_bit_width = _require_positive_int(
        candidate_params, "response_bit_width", "classical_crp"
    )
    replay_window = _require_positive_int(
        candidate_params, "replay_window", "classical_crp"
    )
    threshold = _require_float(candidate_params, "threshold", "classical_crp")
    observed_noise = _read_world_float(
        world_params, "observed_sensor_noise_sigma", fallback_key="sensor_noise_sigma"
    )

    far = _clamp(0.005 + observed_noise * 0.45 + threshold * 0.03)
    frr = _clamp(0.006 + observed_noise * 0.65 + 0.002 / replay_window)
    latency_ms = round(2.0 + challenge_space_size / 64.0, 4)
    readout_cost = round(0.02 + challenge_space_size / 20_000.0, 6)
    enrollment_cost = round(challenge_space_size * 0.0015, 6)
    crp_lifetime = max(1, challenge_space_size // replay_window)
    min_entropy_estimate = round(max(0.1, response_bit_width * 0.92 - observed_noise), 6)
    robustness_under_drift = round(max(0.0, 1.0 - observed_noise * 6.0), 6)
    confidence = round(min(0.99, 0.8 + challenge_space_size / 2000.0), 6)

    return _finalize_metrics(
        far=far,
        frr=frr,
        latency_ms=latency_ms,
        readout_cost=readout_cost,
        enrollment_cost=enrollment_cost,
        crp_lifetime=crp_lifetime,
        min_entropy_estimate=min_entropy_estimate,
        robustness_under_drift=robustness_under_drift,
        confidence=confidence,
    )


def _evaluate_optical_auth(
    candidate_params: Mapping[str, object],
    world_params: Mapping[str, object],
) -> Metrics:
    enrollment_samples = _require_positive_int(
        candidate_params, "enrollment_samples", "optical_auth"
    )
    feature_dimension = _require_positive_int(
        candidate_params, "feature_dimension", "optical_auth"
    )
    observed_noise = _read_world_float(
        world_params, "observed_sensor_noise_sigma", fallback_key="sensor_noise_sigma"
    )
    observed_illumination = _read_world_float(
        world_params,
        "observed_illumination_jitter",
        fallback_key="illumination_jitter",
    )
    observed_angle = _read_world_float(
        world_params,
        "observed_angle_variation_deg",
        fallback_key="angle_variation_deg",
        default=0.0,
    )

    far = _clamp(0.01 + observed_noise * 0.35 + observed_illumination * 0.12)
    frr = _clamp(
        0.012
        + observed_noise * 0.55
        + observed_illumination * 0.18
        + observed_angle / 180.0
    )
    latency_ms = round(8.0 + feature_dimension / 12.0, 4)
    readout_cost = round(0.08 + feature_dimension / 5_000.0, 6)
    enrollment_cost = round(enrollment_samples * feature_dimension / 300.0, 6)
    crp_lifetime = max(1, enrollment_samples * 4)
    min_entropy_estimate = round(
        max(0.1, feature_dimension / 20.0 - observed_noise - observed_illumination),
        6,
    )
    robustness_under_drift = round(
        max(0.0, 1.0 - observed_noise * 4.0 - observed_illumination * 1.8 - observed_angle / 90.0),
        6,
    )
    confidence = round(min(0.99, 0.72 + enrollment_samples / 250.0), 6)

    return _finalize_metrics(
        far=far,
        frr=frr,
        latency_ms=latency_ms,
        readout_cost=readout_cost,
        enrollment_cost=enrollment_cost,
        crp_lifetime=crp_lifetime,
        min_entropy_estimate=min_entropy_estimate,
        robustness_under_drift=robustness_under_drift,
        confidence=confidence,
    )


def _finalize_metrics(
    *,
    far: float,
    frr: float,
    latency_ms: float,
    readout_cost: float,
    enrollment_cost: float,
    crp_lifetime: int,
    min_entropy_estimate: float,
    robustness_under_drift: float,
    confidence: float,
) -> Metrics:
    eer = round((far + frr) / 2.0, 6)
    return {
        "far": round(far, 6),
        "frr": round(frr, 6),
        "eer": eer,
        "latency_ms": latency_ms,
        "readout_cost": readout_cost,
        "enrollment_cost": enrollment_cost,
        "crp_lifetime": crp_lifetime,
        "min_entropy_estimate": min_entropy_estimate,
        "robustness_under_drift": robustness_under_drift,
        "confidence": confidence,
    }


def _require_positive_int(
    params: Mapping[str, object],
    key: str,
    family: str,
) -> int:
    value = params.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise HonestEvaluationError(f"{family}.{key} must be an integer")
    if value <= 0:
        raise HonestEvaluationError(f"{family}.{key} must be greater than zero")
    return value


def _require_float(params: Mapping[str, object], key: str, family: str) -> float:
    value = params.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise HonestEvaluationError(f"{family}.{key} must be numeric")
    return float(value)


def _read_world_float(
    params: Mapping[str, object],
    preferred_key: str,
    *,
    fallback_key: str,
    default: float | None = None,
) -> float:
    for key in (preferred_key, fallback_key):
        if key in params:
            value = params[key]
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise HonestEvaluationError(f"world.{key} must be numeric")
            return float(value)
    if default is not None:
        return default
    raise HonestEvaluationError(
        f"world is missing both {preferred_key!r} and {fallback_key!r}"
    )


def _clamp(value: float) -> float:
    return min(0.999999, max(0.0, value))

