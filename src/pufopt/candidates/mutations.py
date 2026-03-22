"""Deterministic local mutations over candidate specs."""

from __future__ import annotations

import hashlib
import json

from pufopt.types import CandidateSpec, Metrics

CLASSICAL_CHALLENGE_SPACE = (64, 128, 256, 512)
CLASSICAL_RESPONSE_WIDTH = (1, 2, 4)
CLASSICAL_REPLAY_WINDOW = (1, 2, 4, 8)
OPTICAL_ENROLLMENT_SAMPLES = (16, 32, 64, 128)
OPTICAL_FEATURE_DIMENSION = (32, 64, 96, 128)
OPTICAL_SESSION_POLICIES = ("one_time_use", "bounded_reuse")


def mutate_candidate_spec(
    spec: CandidateSpec,
    *,
    metrics: Metrics | None = None,
    max_variants: int = 3,
) -> list[CandidateSpec]:
    """Generate deterministic, schema-valid local mutations for a candidate."""
    if max_variants <= 0:
        return []

    if spec.family == "classical_crp":
        variants = _mutate_classical_crp(spec, metrics or {})
    elif spec.family == "optical_auth":
        variants = _mutate_optical_auth(spec, metrics or {})
    else:
        raise ValueError(f"unsupported candidate family for mutation: {spec.family}")

    deduped: list[CandidateSpec] = []
    seen: set[str] = set()
    for candidate in variants:
        fingerprint = _fingerprint(candidate.family, candidate.params)
        if fingerprint in seen:
            continue
        if candidate.params == spec.params:
            continue
        seen.add(fingerprint)
        deduped.append(candidate)
        if len(deduped) >= max_variants:
            break
    return deduped


def _mutate_classical_crp(spec: CandidateSpec, metrics: Metrics) -> list[CandidateSpec]:
    params = dict(spec.params)
    threshold = _float_param(params, "threshold", 0.1)
    challenge_space = _int_param(params, "challenge_space_size", 128)
    response_width = _int_param(params, "response_bit_width", 1)
    replay_window = _int_param(params, "replay_window", 1)

    modeling = _metric(metrics, "modeling_attack_success")
    replay = _metric(metrics, "replay_attack_success")
    exhaustion = _metric(metrics, "crp_exhaustion_attack_success")

    candidates = [
        _variant(
            spec,
            {
                **params,
                "challenge_space_size": _step_int(
                    challenge_space,
                    CLASSICAL_CHALLENGE_SPACE,
                    1 if modeling >= 0.35 or exhaustion >= 0.35 else -1,
                ),
            },
            reason="challenge_space_adjustment",
        ),
        _variant(
            spec,
            {
                **params,
                "response_bit_width": _step_int(
                    response_width,
                    CLASSICAL_RESPONSE_WIDTH,
                    1 if modeling >= 0.4 else -1,
                ),
            },
            reason="response_width_adjustment",
        ),
        _variant(
            spec,
            {
                **params,
                "replay_window": _step_int(
                    replay_window,
                    CLASSICAL_REPLAY_WINDOW,
                    1 if replay >= 0.3 else -1,
                ),
            },
            reason="replay_window_adjustment",
        ),
        _variant(
            spec,
            {
                **params,
                "threshold": round(
                    min(0.25, max(0.03, threshold + (0.02 if modeling >= 0.4 else -0.01))),
                    4,
                ),
            },
            reason="threshold_adjustment",
        ),
    ]
    return sorted(candidates, key=lambda candidate: candidate.id)


def _mutate_optical_auth(spec: CandidateSpec, metrics: Metrics) -> list[CandidateSpec]:
    params = dict(spec.params)
    enrollment_samples = _int_param(params, "enrollment_samples", 32)
    feature_dimension = _int_param(params, "feature_dimension", 64)
    session_policy = _string_param(params, "session_policy", "one_time_use")

    modeling = _metric(metrics, "modeling_attack_success")
    counterfeit = max(
        _metric(metrics, "counterfeit_attack_success"),
        _metric(metrics, "nearest_match_attack_success"),
    )
    replay = _metric(metrics, "replay_attack_success")
    exhaustion = _metric(metrics, "crp_exhaustion_attack_success")

    candidates = [
        _variant(
            spec,
            {
                **params,
                "feature_dimension": _step_int(
                    feature_dimension,
                    OPTICAL_FEATURE_DIMENSION,
                    1 if max(modeling, counterfeit) >= 0.3 else -1,
                ),
            },
            reason="feature_dimension_adjustment",
        ),
        _variant(
            spec,
            {
                **params,
                "enrollment_samples": _step_int(
                    enrollment_samples,
                    OPTICAL_ENROLLMENT_SAMPLES,
                    1 if exhaustion >= 0.25 else -1,
                ),
            },
            reason="enrollment_adjustment",
        ),
        _variant(
            spec,
            {
                **params,
                "session_policy": _next_string(
                    session_policy,
                    OPTICAL_SESSION_POLICIES,
                    0 if replay >= 0.2 else 1,
                ),
            },
            reason="session_policy_adjustment",
        ),
    ]
    return sorted(candidates, key=lambda candidate: candidate.id)


def _variant(spec: CandidateSpec, params: dict[str, object], *, reason: str) -> CandidateSpec:
    metadata = dict(spec.metadata)
    metadata["parent_id"] = spec.id
    metadata["mutation_reason"] = reason
    return CandidateSpec(
        id=_candidate_id(spec.family, params),
        family=spec.family,
        params=params,
        metadata=metadata,
    )


def _candidate_id(family: str, params: dict[str, object]) -> str:
    return f"{family}-{_fingerprint(family, params)}"


def _fingerprint(family: str, params: dict[str, object]) -> str:
    payload = json.dumps({"family": family, "params": params}, sort_keys=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:10]


def _step_int(current: int, domain: tuple[int, ...], delta: int) -> int:
    if current not in domain:
        current = min(domain, key=lambda candidate: abs(candidate - current))
    index = domain.index(current)
    return domain[max(0, min(len(domain) - 1, index + delta))]


def _next_string(current: str, domain: tuple[str, ...], preferred_index: int) -> str:
    if current not in domain:
        return domain[max(0, min(len(domain) - 1, preferred_index))]
    if len(domain) == 1:
        return domain[0]
    current_index = domain.index(current)
    if current_index == preferred_index:
        return domain[(current_index + 1) % len(domain)]
    return domain[preferred_index]


def _metric(metrics: Metrics, key: str) -> float:
    value = metrics.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return 0.0
    return float(value)


def _int_param(params: dict[str, object], key: str, default: int) -> int:
    value = params.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    return value


def _float_param(params: dict[str, object], key: str, default: float) -> float:
    value = params.get(key, default)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _string_param(params: dict[str, object], key: str, default: str) -> str:
    value = params.get(key, default)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value
