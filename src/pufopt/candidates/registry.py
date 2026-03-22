"""Candidate family registry."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pufopt.types import BuiltCandidate, Candidate, CandidateSpec

CandidateBuilder = Callable[[CandidateSpec], BuiltCandidate]


class UnknownCandidateFamilyError(LookupError):
    """Raised when a candidate family has not been registered."""


@dataclass(frozen=True, slots=True)
class BuiltCandidateRecord:
    """Simple built candidate representation."""

    id: str
    family: str
    params: dict[str, object]


@dataclass(frozen=True, slots=True)
class CandidateDefinition(Candidate):
    """Buildable candidate wrapper around a validated spec."""

    spec: CandidateSpec
    _builder: CandidateBuilder

    @property
    def id(self) -> str:
        return self.spec.id

    @property
    def family(self) -> str:
        return self.spec.family

    @property
    def params(self) -> dict[str, object]:
        return dict(self.spec.params)

    def build(self) -> BuiltCandidate:
        return self._builder(self.spec)


class CandidateRegistry:
    """Registry of candidate family builders."""

    def __init__(self) -> None:
        self._builders: dict[str, CandidateBuilder] = {}

    def register(self, family: str, builder: CandidateBuilder) -> None:
        normalized = family.strip()
        if not normalized:
            raise ValueError("candidate family name must not be empty")
        self._builders[normalized] = builder

    def get(self, family: str) -> CandidateBuilder:
        try:
            return self._builders[family]
        except KeyError as exc:
            known = ", ".join(sorted(self._builders)) or "<none>"
            raise UnknownCandidateFamilyError(
                f"unknown candidate family {family!r}; registered families: {known}"
            ) from exc

    def create(self, spec: CandidateSpec) -> CandidateDefinition:
        return CandidateDefinition(spec=spec, _builder=self.get(spec.family))

    def families(self) -> tuple[str, ...]:
        return tuple(sorted(self._builders))


default_candidate_registry = CandidateRegistry()


def register_candidate_family(
    family: str,
    *,
    registry: CandidateRegistry | None = None,
) -> Callable[[CandidateBuilder], CandidateBuilder]:
    """Decorator for registering candidate builders."""

    registry_ref = registry or default_candidate_registry

    def decorator(builder: CandidateBuilder) -> CandidateBuilder:
        registry_ref.register(family, builder)
        return builder

    return decorator

