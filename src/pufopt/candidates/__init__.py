"""Candidate family registration and construction."""

from pufopt.candidates import baselines as _baselines
from pufopt.candidates.factory import (
    build_candidate,
    build_candidate_definition,
    load_candidate_definition,
)
from pufopt.candidates.registry import (
    BuiltCandidateRecord,
    CandidateDefinition,
    CandidateRegistry,
    UnknownCandidateFamilyError,
    default_candidate_registry,
    register_candidate_family,
)

__all__ = [
    "BuiltCandidateRecord",
    "CandidateDefinition",
    "CandidateRegistry",
    "UnknownCandidateFamilyError",
    "build_candidate",
    "build_candidate_definition",
    "default_candidate_registry",
    "load_candidate_definition",
    "register_candidate_family",
]
