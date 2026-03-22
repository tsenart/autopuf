"""Schema loading and validation helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, TypeVar

import yaml

from pufopt.types import (
    AttackSpec,
    CandidateSpec,
    FormalClaimSpec,
    PROOF_STATUS_VALUES,
    Params,
    ResearchRunSpec,
    SearchSpec,
    WorldSpec,
)

T = TypeVar("T")


class SchemaValidationError(ValueError):
    """Raised when a machine-readable artifact does not satisfy the schema."""

    def __init__(self, issues: Iterable[str]):
        self.issues = list(issues)
        message = "Schema validation failed:\n- " + "\n- ".join(self.issues)
        super().__init__(message)


def load_candidate_spec(path: str | Path) -> CandidateSpec:
    """Load and validate a candidate spec from YAML or JSON."""
    return validate_candidate_spec(load_data_file(path))


def load_world_spec(path: str | Path) -> WorldSpec:
    """Load and validate a world spec from YAML or JSON."""
    return validate_world_spec(load_data_file(path))


def load_suite_spec(path: str | Path) -> ResearchRunSpec:
    """Load and validate a research run or optimization suite spec."""
    return validate_suite_spec(load_data_file(path))


def load_formal_claim_spec(path: str | Path) -> FormalClaimSpec:
    """Load and validate a formal claim spec from YAML or JSON."""
    return validate_formal_claim_spec(load_data_file(path))


def load_data_file(path: str | Path) -> Any:
    """Load a YAML or JSON file into Python data."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    text = file_path.read_text(encoding="utf-8")
    if file_path.suffix.lower() == ".json":
        return json.loads(text)
    if file_path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    raise SchemaValidationError(
        [f"path '{file_path}' must use .json, .yaml, or .yml extension"]
    )


def validate_candidate_spec(raw: Any) -> CandidateSpec:
    """Validate candidate data and return a normalized spec."""
    data = _mapping(raw, "candidate")
    return CandidateSpec(
        id=_non_empty_string(data, "candidate.id"),
        family=_non_empty_string(data, "candidate.family"),
        params=_params(data.get("params"), "candidate.params"),
        metadata=_optional_params(data.get("metadata"), "candidate.metadata"),
    )


def validate_world_spec(raw: Any) -> WorldSpec:
    """Validate world data and return a normalized spec."""
    data = _mapping(raw, "world")
    family = data.get("family")
    if family is not None and not isinstance(family, str):
        raise SchemaValidationError(
            [f"world.family must be a string when provided, got {type(family).__name__}"]
        )

    normalized_family = family.strip() if isinstance(family, str) else None
    if isinstance(family, str) and not normalized_family:
        raise SchemaValidationError(["world.family must not be empty when provided"])

    return WorldSpec(
        id=_non_empty_string(data, "world.id"),
        family=normalized_family,
        params=_params(data.get("params"), "world.params"),
        metadata=_optional_params(data.get("metadata"), "world.metadata"),
    )


def validate_suite_spec(raw: Any) -> ResearchRunSpec:
    """Validate suite or research run data and return a normalized spec."""
    data = _mapping(raw, "suite")

    search_data = data.get("search")
    search = _validate_search_spec(search_data) if search_data is not None else None

    worlds = _string_list(data.get("worlds", []), "suite.worlds")
    attacks = _validate_attacks(data.get("attacks"), "suite.attacks")
    scoring_config = _optional_string(data.get("scoring_config"), "suite.scoring_config")

    scoring = data.get("scoring")
    if scoring is not None:
        scoring_mapping = _mapping(scoring, "suite.scoring")
        if scoring_config is not None:
            raise SchemaValidationError(
                [
                    "suite may set either suite.scoring_config or suite.scoring.file, not both"
                ]
            )
        scoring_config = _non_empty_string(scoring_mapping, "suite.scoring.file", "file")

    spec = ResearchRunSpec(
        id=_non_empty_string(data, "suite.id"),
        attacks=attacks,
        status=_optional_string(data.get("status"), "suite.status") or "ready",
        mode=_optional_string(data.get("mode"), "suite.mode") or "research",
        candidate=_optional_string(data.get("candidate"), "suite.candidate"),
        world=_optional_string(data.get("world"), "suite.world"),
        suite=_optional_string(data.get("suite"), "suite.suite"),
        worlds=worlds,
        search=search,
        scoring_config=scoring_config,
        budgets=_optional_params(data.get("budgets"), "suite.budgets"),
        strong_result_policy=_optional_params(
            data.get("strong_result_policy"), "suite.strong_result_policy"
        ),
        surprising_result_policy=_optional_params(
            data.get("surprising_result_policy"), "suite.surprising_result_policy"
        ),
        proof_policy=_optional_params(data.get("proof_policy"), "suite.proof_policy"),
        constraints_frozen=_optional_bool(
            data.get("constraints_frozen"), "suite.constraints_frozen", default=False
        ),
        objective_frozen=_optional_bool(
            data.get("objective_frozen"), "suite.objective_frozen", default=False
        ),
        requires_reproduction=_optional_bool(
            data.get("requires_reproduction"),
            "suite.requires_reproduction",
            default=True,
        ),
        requires_red_review=_optional_bool(
            data.get("requires_red_review"), "suite.requires_red_review", default=True
        ),
        artifacts_root=_optional_string(data.get("artifacts_root"), "suite.artifacts_root"),
    )

    if spec.search is None and spec.candidate is None and spec.suite is None:
        raise SchemaValidationError(
            [
                "suite must define either search configuration, a candidate path, or a nested suite path"
            ]
        )
    if spec.search is not None and not spec.worlds:
        raise SchemaValidationError(
            ["suite.worlds must contain at least one world path when suite.search is set"]
        )
    if spec.candidate is not None and spec.world is None:
        raise SchemaValidationError(
            ["suite.world is required when suite.candidate is provided"]
        )

    return spec


def validate_formal_claim_spec(raw: Any) -> FormalClaimSpec:
    """Validate formal claim data and return a normalized spec."""
    data = _mapping(raw, "formal_claim")
    proof_status = _non_empty_string(data, "formal_claim.proof_status")
    if proof_status not in PROOF_STATUS_VALUES:
        allowed = ", ".join(PROOF_STATUS_VALUES)
        raise SchemaValidationError(
            [
                f"formal_claim.proof_status must be one of {allowed}; got {proof_status!r}"
            ]
        )

    return FormalClaimSpec(
        id=_non_empty_string(data, "formal_claim.id"),
        candidate_family=_non_empty_string(
            data, "formal_claim.candidate_family"
        ),
        security_game=_non_empty_string(data, "formal_claim.security_game"),
        assumptions=_string_list(data.get("assumptions"), "formal_claim.assumptions"),
        claim=_non_empty_string(data, "formal_claim.claim"),
        proof_status=proof_status,
        lean_modules=_string_list(
            data.get("lean_modules", []), "formal_claim.lean_modules"
        ),
        bridge_checks=_optional_params(
            data.get("bridge_checks"), "formal_claim.bridge_checks"
        ),
        related_runs=_string_list(
            data.get("related_runs", []), "formal_claim.related_runs"
        ),
        notes=_optional_string(data.get("notes"), "formal_claim.notes"),
    )


def _validate_search_spec(raw: Any) -> SearchSpec:
    data = _mapping(raw, "suite.search")
    algorithm = _non_empty_string(data, "suite.search.algorithm")
    max_iterations = data.get("max_iterations")
    if max_iterations is not None:
        max_iterations = _positive_int(max_iterations, "suite.search.max_iterations")
    seeds = _string_list(data.get("seeds", []), "suite.search.seeds")

    remaining = {
        key: value
        for key, value in data.items()
        if key not in {"algorithm", "max_iterations", "seeds"}
    }
    return SearchSpec(
        algorithm=algorithm,
        max_iterations=max_iterations,
        seeds=seeds,
        params=_optional_params(remaining, "suite.search.params"),
    )


def _validate_attacks(raw: Any, path: str) -> list[AttackSpec]:
    if raw is None:
        raise SchemaValidationError([f"{path} is required"])
    if not isinstance(raw, list):
        raise SchemaValidationError([f"{path} must be a list, got {type(raw).__name__}"])

    attacks: list[AttackSpec] = []
    issues: list[str] = []
    for index, entry in enumerate(raw):
        item_path = f"{path}[{index}]"
        if isinstance(entry, str):
            name = entry.strip()
            if not name:
                issues.append(f"{item_path} must not be empty")
                continue
            attacks.append(AttackSpec(name=name))
            continue
        if isinstance(entry, Mapping):
            try:
                attack_data = _mapping(entry, item_path)
                attacks.append(
                    AttackSpec(
                        name=_non_empty_string(attack_data, f"{item_path}.name"),
                        params=_optional_params(
                            attack_data.get("params"), f"{item_path}.params"
                        ),
                    )
                )
            except SchemaValidationError as exc:
                issues.extend(exc.issues)
            continue
        issues.append(
            f"{item_path} must be either a string or mapping, got {type(entry).__name__}"
        )

    if issues:
        raise SchemaValidationError(issues)
    if not attacks:
        raise SchemaValidationError([f"{path} must contain at least one attack"])
    return attacks


def _mapping(raw: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise SchemaValidationError([f"{path} must be a mapping, got {type(raw).__name__}"])
    return raw


def _non_empty_string(
    data: Mapping[str, Any], path: str, key: str | None = None
) -> str:
    lookup_key = key or path.rsplit(".", 1)[-1]
    if lookup_key not in data:
        raise SchemaValidationError([f"{path} is required"])
    value = data[lookup_key]
    if not isinstance(value, str):
        raise SchemaValidationError([f"{path} must be a string, got {type(value).__name__}"])
    normalized = value.strip()
    if not normalized:
        raise SchemaValidationError([f"{path} must not be empty"])
    return normalized


def _optional_string(value: Any, path: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SchemaValidationError([f"{path} must be a string, got {type(value).__name__}"])
    normalized = value.strip()
    if not normalized:
        raise SchemaValidationError([f"{path} must not be empty when provided"])
    return normalized


def _string_list(value: Any, path: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise SchemaValidationError([f"{path} must be a list, got {type(value).__name__}"])
    items: list[str] = []
    issues: list[str] = []
    for index, entry in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(entry, str):
            issues.append(f"{item_path} must be a string, got {type(entry).__name__}")
            continue
        normalized = entry.strip()
        if not normalized:
            issues.append(f"{item_path} must not be empty")
            continue
        items.append(normalized)
    if issues:
        raise SchemaValidationError(issues)
    return items


def _optional_bool(value: Any, path: str, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise SchemaValidationError(
            [f"{path} must be a boolean, got {type(value).__name__}"]
        )
    return value


def _positive_int(value: Any, path: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SchemaValidationError([f"{path} must be an integer, got {type(value).__name__}"])
    if value <= 0:
        raise SchemaValidationError([f"{path} must be greater than zero"])
    return value


def _optional_params(value: Any, path: str) -> Params:
    if value is None:
        return {}
    return _params(value, path)


def _params(value: Any, path: str) -> Params:
    data = _mapping(value, path)
    return {
        str(key): _normalize_json_value(entry, f"{path}.{key}")
        for key, entry in data.items()
    }


def _normalize_json_value(value: Any, path: str) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_normalize_json_value(entry, f"{path}[{index}]") for index, entry in enumerate(value)]
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_json_value(entry, f"{path}.{key}")
            for key, entry in value.items()
        }
    raise SchemaValidationError(
        [f"{path} must contain JSON-compatible data, got {type(value).__name__}"]
    )
