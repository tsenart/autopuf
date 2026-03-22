from __future__ import annotations

import importlib


MODULES = [
    "pufopt",
    "pufopt.config",
    "pufopt.types",
    "pufopt.formal.bridge",
    "pufopt.formal.proof_status",
    "pufopt.loop.search",
    "pufopt.loop.scheduler",
    "pufopt.loop.frontier",
    "pufopt.candidates.registry",
    "pufopt.candidates.factory",
    "pufopt.candidates.mutations",
    "pufopt.worlds.registry",
    "pufopt.worlds.noise",
    "pufopt.worlds.drift",
    "pufopt.evaluators.honest",
    "pufopt.evaluators.adversarial",
    "pufopt.evaluators.scoring",
    "pufopt.evaluators.constraints",
    "pufopt.attacks.base",
    "pufopt.attacks.modeling",
    "pufopt.attacks.replay",
    "pufopt.attacks.nearest_match",
    "pufopt.attacks.crp_exhaustion",
    "pufopt.attacks.drift_abuse",
    "pufopt.experiments.suites",
    "pufopt.experiments.selection",
    "pufopt.experiments.reports",
    "pufopt.storage.io",
    "pufopt.storage.schema",
    "pufopt.storage.artifacts",
]


def main() -> None:
    for name in MODULES:
        importlib.import_module(name)
    print(f"imported {len(MODULES)} modules")


if __name__ == "__main__":
    main()
