"""Candidate spec loading and build helpers."""

from __future__ import annotations

from pathlib import Path

from pufopt.candidates.registry import (
    CandidateDefinition,
    CandidateRegistry,
    default_candidate_registry,
)
from pufopt.storage.schema import load_candidate_spec
from pufopt.types import BuiltCandidate, CandidateSpec


def load_candidate_definition(
    path: str | Path,
    *,
    registry: CandidateRegistry | None = None,
) -> CandidateDefinition:
    """Load a candidate definition from disk and resolve its family."""
    spec = load_candidate_spec(path)
    return build_candidate_definition(spec, registry=registry)


def build_candidate_definition(
    spec: CandidateSpec,
    *,
    registry: CandidateRegistry | None = None,
) -> CandidateDefinition:
    """Resolve a validated candidate spec into a buildable candidate."""
    registry_ref = registry or default_candidate_registry
    return registry_ref.create(spec)


def build_candidate(
    path: str | Path,
    *,
    registry: CandidateRegistry | None = None,
) -> BuiltCandidate:
    """Load and build a candidate from disk."""
    return load_candidate_definition(path, registry=registry).build()

