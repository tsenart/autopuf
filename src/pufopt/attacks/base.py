"""Attack registry, budgets, and execution helpers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from pufopt.types import AttackResult, BuiltCandidate, Params, WorldInstance

AttackRunner = Callable[[BuiltCandidate, WorldInstance, "AttackBudget"], AttackResult]


@dataclass(frozen=True, slots=True)
class AttackBudget:
    """Serializable attack budget."""

    queries: int = 1_000
    observations: int = 256
    search_steps: int = 128

    def as_params(self) -> Params:
        return {
            "queries": self.queries,
            "observations": self.observations,
            "search_steps": self.search_steps,
        }


class UnknownAttackError(LookupError):
    """Raised when an attack family is not registered."""


class AttackRegistry:
    """Registry of attack runners."""

    def __init__(self) -> None:
        self._runners: dict[str, AttackRunner] = {}

    def register(self, name: str, runner: AttackRunner) -> None:
        normalized = name.strip()
        if not normalized:
            raise ValueError("attack name must not be empty")
        self._runners[normalized] = runner

    def get(self, name: str) -> AttackRunner:
        try:
            return self._runners[name]
        except KeyError as exc:
            known = ", ".join(sorted(self._runners)) or "<none>"
            raise UnknownAttackError(
                f"unknown attack family {name!r}; registered families: {known}"
            ) from exc

    def run(
        self,
        name: str,
        candidate: BuiltCandidate,
        world: WorldInstance,
        budget: AttackBudget,
    ) -> AttackResult:
        return self.get(name)(candidate, world, budget)

    def families(self) -> tuple[str, ...]:
        return tuple(sorted(self._runners))


default_attack_registry = AttackRegistry()


def register_attack_family(
    name: str,
    *,
    registry: AttackRegistry | None = None,
) -> Callable[[AttackRunner], AttackRunner]:
    """Decorator for registering attack runners."""

    registry_ref = registry or default_attack_registry

    def decorator(runner: AttackRunner) -> AttackRunner:
        registry_ref.register(name, runner)
        return runner

    return decorator


def normalize_attack_budget(
    raw: Mapping[str, object] | None = None,
) -> AttackBudget:
    """Normalize a mapping into an attack budget."""
    if raw is None:
        return AttackBudget()

    return AttackBudget(
        queries=_positive_int(raw.get("queries", 1_000), "queries"),
        observations=_positive_int(raw.get("observations", 256), "observations"),
        search_steps=_positive_int(raw.get("search_steps", 128), "search_steps"),
    )


def run_attack(
    name: str,
    candidate: BuiltCandidate,
    world: WorldInstance,
    budget: Mapping[str, object] | AttackBudget | None = None,
    *,
    registry: AttackRegistry | None = None,
) -> AttackResult:
    """Run one attack family with a normalized budget."""
    registry_ref = registry or default_attack_registry
    resolved_budget = budget if isinstance(budget, AttackBudget) else normalize_attack_budget(budget)
    return registry_ref.run(name, candidate, world, resolved_budget)


def clamp_success(value: float) -> float:
    """Clamp a success metric into the [0, 1) interval."""
    return min(0.999999, max(0.0, value))


def numeric_param(params: Mapping[str, object], key: str, default: float) -> float:
    """Read a numeric param with a numeric default."""
    value = params.get(key, default)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def string_param(params: Mapping[str, object], key: str, default: str) -> str:
    """Read a string param with a string default."""
    value = params.get(key, default)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _positive_int(value: object, key: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    if value <= 0:
        raise ValueError(f"{key} must be greater than zero")
    return value

