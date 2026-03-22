"""Baseline candidate family implementations."""

from __future__ import annotations

from pufopt.candidates.registry import BuiltCandidateRecord, register_candidate_family
from pufopt.types import CandidateSpec


@register_candidate_family("classical_crp")
def build_classical_crp(spec: CandidateSpec) -> BuiltCandidateRecord:
    challenge_space_size = _positive_int(
        spec.params.get("challenge_space_size", 128), "challenge_space_size"
    )
    response_bit_width = _positive_int(
        spec.params.get("response_bit_width", 1), "response_bit_width"
    )
    replay_window = _positive_int(spec.params.get("replay_window", 1), "replay_window")

    params = dict(spec.params)
    params.setdefault("threshold", 0.1)
    params["challenge_space_size"] = challenge_space_size
    params["response_bit_width"] = response_bit_width
    params["replay_window"] = replay_window
    params["challenge_labels"] = [
        f"challenge-{index}" for index in range(challenge_space_size)
    ]
    return BuiltCandidateRecord(id=spec.id, family=spec.family, params=params)


@register_candidate_family("optical_auth")
def build_optical_auth(spec: CandidateSpec) -> BuiltCandidateRecord:
    enrollment_samples = _positive_int(
        spec.params.get("enrollment_samples", 32), "enrollment_samples"
    )
    feature_dimension = _positive_int(
        spec.params.get("feature_dimension", 64), "feature_dimension"
    )

    params = dict(spec.params)
    params.setdefault("feature_extractor", "spectral_histogram_v1")
    params.setdefault("threshold_policy", "global_margin")
    params.setdefault("sensor_mode", "standard_camera")
    params.setdefault("session_policy", "one_time_use")
    params["enrollment_samples"] = enrollment_samples
    params["feature_dimension"] = feature_dimension
    params["feature_labels"] = [
        f"feature-{index}" for index in range(feature_dimension)
    ]
    return BuiltCandidateRecord(id=spec.id, family=spec.family, params=params)


def _positive_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value

