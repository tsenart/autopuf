"""Configuration loaders and provenance helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import yaml

DEFAULT_ATTACK_HEURISTICS_PATH = Path("configs/heuristics/attacks.yaml")
DEFAULT_REGRESSION_EXPECTATIONS_PATH = Path("tests/fixtures/regression_expectations.yaml")


@lru_cache(maxsize=None)
def _load_yaml(path: str) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"config {path!r} must contain a top-level mapping")
    return data


def load_attack_heuristics(
    path: str | Path = DEFAULT_ATTACK_HEURISTICS_PATH,
) -> dict[str, Any]:
    """Load attack-heuristic coefficients and provenance metadata."""
    return _load_yaml(str(Path(path).resolve()))


def load_regression_expectations(
    path: str | Path = DEFAULT_REGRESSION_EXPECTATIONS_PATH,
) -> dict[str, Any]:
    """Load regression expectations and their provenance metadata."""
    return _load_yaml(str(Path(path).resolve()))


def attack_family_config(
    attack_name: str,
    family: str,
    path: str | Path = DEFAULT_ATTACK_HEURISTICS_PATH,
) -> dict[str, Any]:
    """Return one attack/family heuristic block."""
    data = load_attack_heuristics(path)
    attacks = _mapping(data.get("attacks"), "attacks")
    attack = _mapping(attacks.get(attack_name), f"attacks.{attack_name}")
    families = _mapping(attack.get("families"), f"attacks.{attack_name}.families")
    family_config = _mapping(
        families.get(family),
        f"attacks.{attack_name}.families.{family}",
    )
    merged = dict(attack)
    merged.update(family_config)
    merged["families"] = families
    return merged


def attack_provenance(
    attack_name: str,
    family: str,
    path: str | Path = DEFAULT_ATTACK_HEURISTICS_PATH,
) -> dict[str, str]:
    """Return normalized provenance fields for one attack/family block."""
    config = attack_family_config(attack_name, family, path)
    provenance = _mapping(config.get("provenance"), f"{attack_name}.{family}.provenance")
    return {
        "calibration_status": str(provenance.get("calibration_status", "heuristic")),
        "citation_status": str(
            provenance.get("citation_status", "qualitative_literature_alignment_only")
        ),
        "provenance_note": str(provenance.get("note", "")),
        "provenance_ref": (
            f"{Path(path).as_posix()}#attacks.{attack_name}.families.{family}"
        ),
    }


def _mapping(value: object, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be a mapping")
    return value
