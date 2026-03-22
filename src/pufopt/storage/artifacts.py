"""Run artifact layout and replay helpers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from pufopt.storage.io import ensure_directory, read_json_file, write_json_atomic


@dataclass(frozen=True, slots=True)
class RunLayout:
    """Filesystem layout for one run directory."""

    root: Path
    run_id: str

    @property
    def candidate_dir(self) -> Path:
        return self.root / "candidate"

    @property
    def world_dir(self) -> Path:
        return self.root / "world"

    @property
    def honest_dir(self) -> Path:
        return self.root / "honest"

    @property
    def attacks_dir(self) -> Path:
        return self.root / "attacks"

    @property
    def formal_dir(self) -> Path:
        return self.root / "formal"

    @property
    def score_dir(self) -> Path:
        return self.root / "score"

    @property
    def frontier_dir(self) -> Path:
        return self.root / "frontier"

    @property
    def planner_dir(self) -> Path:
        return self.root / "planner"

    @property
    def context_path(self) -> Path:
        return self.root / "context.json"


def deterministic_run_id(
    *,
    suite_id: str | None = None,
    candidate_id: str | None = None,
    world_id: str | None = None,
    seeds: Mapping[str, int] | None = None,
) -> str:
    """Compute a stable run identifier from the core replay inputs."""
    parts = [
        suite_id or "",
        candidate_id or "",
        world_id or "",
        _seed_fingerprint(seeds or {}),
    ]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


def create_run_layout(
    artifacts_root: str | Path,
    *,
    suite_id: str | None = None,
    candidate_id: str | None = None,
    world_id: str | None = None,
    seeds: Mapping[str, int] | None = None,
) -> RunLayout:
    """Create the canonical directory tree for a run."""
    run_id = deterministic_run_id(
        suite_id=suite_id,
        candidate_id=candidate_id,
        world_id=world_id,
        seeds=seeds,
    )
    root = ensure_directory(Path(artifacts_root) / run_id)
    layout = RunLayout(root=root, run_id=run_id)
    for directory in (
        layout.candidate_dir,
        layout.world_dir,
        layout.honest_dir,
        layout.attacks_dir,
        layout.formal_dir,
        layout.score_dir,
        layout.frontier_dir,
        layout.planner_dir,
    ):
        ensure_directory(directory)
    return layout


def write_run_context(
    layout: RunLayout,
    *,
    seeds: Mapping[str, int],
    config_refs: Mapping[str, str | None],
    metadata: Mapping[str, Any] | None = None,
) -> Path:
    """Write the replay-critical seeds and config references for a run."""
    payload = {
        "run_id": layout.run_id,
        "seeds": dict(seeds),
        "config_refs": dict(config_refs),
        "metadata": dict(metadata or {}),
    }
    return write_json_atomic(layout.context_path, payload)


def write_artifact(
    layout: RunLayout,
    relative_path: str | Path,
    payload: Any,
) -> Path:
    """Write a JSON artifact relative to the run root."""
    return write_json_atomic(layout.root / Path(relative_path), payload)


def read_artifact(layout: RunLayout, relative_path: str | Path) -> Any:
    """Read a JSON artifact relative to the run root."""
    return read_json_file(layout.root / Path(relative_path))


def _seed_fingerprint(seeds: Mapping[str, int]) -> str:
    items = [f"{key}={value}" for key, value in sorted(seeds.items())]
    return ",".join(items)

