"""Shared types and protocols for autopuf."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol, TypeAlias, runtime_checkable

Scalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = Scalar | list["JSONValue"] | dict[str, "JSONValue"]
Params: TypeAlias = dict[str, JSONValue]
Metrics: TypeAlias = dict[str, Scalar]
ProofStatus: TypeAlias = Literal[
    "empirical_only",
    "specified",
    "partially_proved",
    "proved",
    "counterexample_found",
]
ResultDisposition: TypeAlias = Literal[
    "valid",
    "invalid",
    "survivor",
    "dominated",
    "rejected",
    "untrusted",
    "reproduced",
]

PROOF_STATUS_VALUES: tuple[ProofStatus, ...] = (
    "empirical_only",
    "specified",
    "partially_proved",
    "proved",
    "counterexample_found",
)
RESULT_DISPOSITION_VALUES: tuple[ResultDisposition, ...] = (
    "valid",
    "invalid",
    "survivor",
    "dominated",
    "rejected",
    "untrusted",
    "reproduced",
)


@dataclass(frozen=True, slots=True)
class CandidateSpec:
    """Declarative candidate definition loaded from YAML or JSON."""

    id: str
    family: str
    params: Params
    metadata: Params = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorldSpec:
    """Declarative world definition loaded from YAML or JSON."""

    id: str
    params: Params
    family: str | None = None
    metadata: Params = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AttackSpec:
    """Declarative attack configuration."""

    name: str
    params: Params = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SearchSpec:
    """Search configuration for optimization suites."""

    algorithm: str
    max_iterations: int | None = None
    seeds: list[str] = field(default_factory=list)
    params: Params = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ResearchRunSpec:
    """Normalized research run or optimization suite configuration."""

    id: str
    attacks: list[AttackSpec]
    status: str = "ready"
    mode: str = "research"
    candidate: str | None = None
    world: str | None = None
    suite: str | None = None
    worlds: list[str] = field(default_factory=list)
    search: SearchSpec | None = None
    scoring_config: str | None = None
    budgets: Params = field(default_factory=dict)
    strong_result_policy: Params = field(default_factory=dict)
    surprising_result_policy: Params = field(default_factory=dict)
    proof_policy: Params = field(default_factory=dict)
    constraints_frozen: bool = False
    objective_frozen: bool = False
    requires_reproduction: bool = True
    requires_red_review: bool = True
    artifacts_root: str | None = None


@dataclass(frozen=True, slots=True)
class AttackResult:
    """Output of a single attack family."""

    name: str
    success: float | None
    metrics: Metrics = field(default_factory=dict)
    traces: list[str] = field(default_factory=list)
    params: Params = field(default_factory=dict)
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Combined evaluation output for one candidate and world."""

    candidate_id: str
    world_id: str
    honest_metrics: Metrics
    attacks: list[AttackResult]
    seeds: dict[str, int] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class ScoreCard:
    """Constraint and utility output for a candidate evaluation."""

    candidate_id: str
    world_id: str
    disposition: ResultDisposition
    utility: float | None = None
    hard_constraint_passed: bool = False
    is_survivor: bool = False
    strong_result: bool = False
    surprising_result: bool = False
    reject_reasons: list[str] = field(default_factory=list)
    metrics: Metrics = field(default_factory=dict)
    proof_status: ProofStatus | None = None
    formal_claim_id: str | None = None


@dataclass(frozen=True, slots=True)
class FrontierEntry:
    """One entry on the current non-dominated frontier."""

    candidate_id: str
    family: str
    utility: float
    metrics: Metrics = field(default_factory=dict)
    formal_claim_id: str | None = None
    proof_status: ProofStatus | None = None


@dataclass(frozen=True, slots=True)
class PlanDecision:
    """Decision emitted by the planner."""

    action: str
    reason: str
    candidate_id: str | None = None
    world_id: str | None = None
    metadata: Params = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FormalClaimSpec:
    """Formal claim metadata attached to promoted results."""

    id: str
    candidate_family: str
    security_game: str
    assumptions: list[str]
    claim: str
    proof_status: ProofStatus
    lean_modules: list[str] = field(default_factory=list)
    bridge_checks: Params = field(default_factory=dict)
    related_runs: list[str] = field(default_factory=list)
    notes: str | None = None


@runtime_checkable
class BuiltCandidate(Protocol):
    """Runtime representation of a candidate ready for evaluation."""

    id: str
    family: str
    params: Params


@runtime_checkable
class Candidate(Protocol):
    """Buildable candidate contract."""

    id: str
    family: str
    params: Params

    def build(self) -> BuiltCandidate: ...


@runtime_checkable
class WorldInstance(Protocol):
    """Concrete world sampled from a world spec."""

    id: str
    params: Params


@runtime_checkable
class World(Protocol):
    """World specification contract."""

    id: str
    params: Params

    def sample(self, seed: int) -> WorldInstance: ...


@runtime_checkable
class Attack(Protocol):
    """Attack execution contract."""

    name: str

    def run(
        self,
        candidate: BuiltCandidate,
        world: WorldInstance,
        budget: Params,
    ) -> AttackResult: ...


@runtime_checkable
class Evaluator(Protocol):
    """Evaluator contract."""

    def evaluate(
        self,
        candidate: Candidate,
        world: World,
        attacks: list[Attack],
    ) -> EvaluationResult: ...
