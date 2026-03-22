"""Optimization-suite loading helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pufopt.storage.schema import load_candidate_spec, load_data_file, load_suite_spec
from pufopt.types import CandidateSpec, ResearchRunSpec


@dataclass(frozen=True, slots=True)
class LoadedSuite:
    """Materialized optimization suite."""

    path: Path
    raw_data: dict[str, object]
    spec: ResearchRunSpec
    seed_paths: list[str]
    seed_candidates: list[CandidateSpec]
    world_paths: list[str]
    scoring_config_path: str
    artifacts_root: str


def load_optimization_suite(path: str | Path) -> LoadedSuite:
    """Load a suite with resolved seed candidates and world paths."""
    suite_path = Path(path)
    spec = load_suite_spec(suite_path)
    raw_data = load_data_file(suite_path)

    if spec.search is None:
        raise ValueError("optimization suite must declare suite.search")

    seed_paths = list(spec.search.seeds)
    if not seed_paths and spec.candidate is not None:
        seed_paths = [spec.candidate]
    if not seed_paths:
        raise ValueError("optimization suite must declare at least one seed candidate")

    world_paths = list(spec.worlds)
    if not world_paths and spec.world is not None:
        world_paths = [spec.world]
    if not world_paths:
        raise ValueError("optimization suite must declare at least one world")

    seed_candidates = [load_candidate_spec(seed_path) for seed_path in seed_paths]
    scoring_config_path = spec.scoring_config or "configs/scoring/default.yaml"
    artifacts_root = spec.artifacts_root or "artifacts/runs"

    if not isinstance(raw_data, dict):
        raise ValueError("suite root must be a mapping")

    return LoadedSuite(
        path=suite_path,
        raw_data=dict(raw_data),
        spec=spec,
        seed_paths=seed_paths,
        seed_candidates=seed_candidates,
        world_paths=world_paths,
        scoring_config_path=scoring_config_path,
        artifacts_root=artifacts_root,
    )
