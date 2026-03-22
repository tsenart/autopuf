from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from pufopt.worlds.registry import (
    UnknownWorldFamilyError,
    WorldRegistry,
    load_world_definition,
    sample_world,
)


class WorldRegistryTest(unittest.TestCase):
    def test_valid_world_yaml_loads_and_samples_deterministically(self) -> None:
        registry = WorldRegistry()
        registry.register(
            "stub_world",
            lambda spec, seed: type(
                "StubWorldInstance",
                (),
                {
                    "id": spec.id,
                    "params": {
                        **spec.params,
                        "sample_seed": seed,
                        "sample_value": seed * 2,
                    },
                },
            )(),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            world_path = Path(tmpdir) / "world.yaml"
            world_path.write_text(
                textwrap.dedent(
                    """
                    id: world-1
                    family: stub_world
                    params:
                      sensor_noise_sigma: 0.01
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            definition = load_world_definition(world_path, registry=registry)
            first = sample_world(world_path, 17, registry=registry)
            second = definition.sample(17)

            self.assertEqual(definition.spec.id, "world-1")
            self.assertEqual(first.params["sample_seed"], second.params["sample_seed"])
            self.assertEqual(first.params["sample_value"], second.params["sample_value"])

    def test_unknown_world_family_fails_clearly(self) -> None:
        registry = WorldRegistry()

        with tempfile.TemporaryDirectory() as tmpdir:
            world_path = Path(tmpdir) / "world.yaml"
            world_path.write_text(
                textwrap.dedent(
                    """
                    id: world-1
                    family: missing_world
                    params: {}
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(UnknownWorldFamilyError) as ctx:
                load_world_definition(world_path, registry=registry)
            self.assertIn("unknown world family", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
