"""World family registry."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pufopt.storage.schema import load_world_spec
from pufopt.types import Params, World, WorldInstance, WorldSpec

WorldSampler = Callable[[WorldSpec, int], WorldInstance]


class UnknownWorldFamilyError(LookupError):
    """Raised when a world family has not been registered."""


@dataclass(frozen=True, slots=True)
class WorldInstanceRecord(WorldInstance):
    """Simple concrete world instance."""

    id: str
    params: Params


@dataclass(frozen=True, slots=True)
class WorldDefinition(World):
    """Sampleable world wrapper around a validated spec."""

    spec: WorldSpec
    _sampler: WorldSampler

    @property
    def id(self) -> str:
        return self.spec.id

    @property
    def params(self) -> Params:
        return dict(self.spec.params)

    def sample(self, seed: int) -> WorldInstance:
        return self._sampler(self.spec, seed)


class WorldRegistry:
    """Registry of world samplers."""

    def __init__(self) -> None:
        self._samplers: dict[str, WorldSampler] = {}

    def register(self, family: str, sampler: WorldSampler) -> None:
        normalized = family.strip()
        if not normalized:
            raise ValueError("world family name must not be empty")
        self._samplers[normalized] = sampler

    def get(self, family: str | None) -> WorldSampler:
        if family is None:
            raise UnknownWorldFamilyError(
                "world spec does not declare a family; a registered world family is required"
            )
        try:
            return self._samplers[family]
        except KeyError as exc:
            known = ", ".join(sorted(self._samplers)) or "<none>"
            raise UnknownWorldFamilyError(
                f"unknown world family {family!r}; registered families: {known}"
            ) from exc

    def create(self, spec: WorldSpec) -> WorldDefinition:
        return WorldDefinition(spec=spec, _sampler=self.get(spec.family))

    def families(self) -> tuple[str, ...]:
        return tuple(sorted(self._samplers))


default_world_registry = WorldRegistry()


def register_world_family(
    family: str,
    *,
    registry: WorldRegistry | None = None,
) -> Callable[[WorldSampler], WorldSampler]:
    """Decorator for registering world samplers."""

    registry_ref = registry or default_world_registry

    def decorator(sampler: WorldSampler) -> WorldSampler:
        registry_ref.register(family, sampler)
        return sampler

    return decorator


def load_world_definition(
    path: str | Path,
    *,
    registry: WorldRegistry | None = None,
) -> WorldDefinition:
    """Load a world definition from disk and resolve its family."""
    spec = load_world_spec(path)
    registry_ref = registry or default_world_registry
    return registry_ref.create(spec)


def sample_world(
    path: str | Path,
    seed: int,
    *,
    registry: WorldRegistry | None = None,
) -> WorldInstance:
    """Load and sample a world from disk."""
    return load_world_definition(path, registry=registry).sample(seed)


def seeded_param_sampler(spec: WorldSpec, seed: int) -> WorldInstanceRecord:
    """Default deterministic sampler that annotates params with the seed."""
    rng = random.Random(seed)
    params = dict(spec.params)
    params["sample_seed"] = seed
    params["sample_nonce"] = rng.randint(0, 1_000_000)
    return WorldInstanceRecord(id=spec.id, params=params)

