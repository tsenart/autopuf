from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from pufopt.candidates.factory import build_candidate, load_candidate_definition
from pufopt.candidates.registry import (
    BuiltCandidateRecord,
    CandidateRegistry,
    UnknownCandidateFamilyError,
)


class CandidateRegistryTest(unittest.TestCase):
    def test_valid_candidate_yaml_loads_and_builds(self) -> None:
        registry = CandidateRegistry()
        registry.register(
            "stub_candidate",
            lambda spec: BuiltCandidateRecord(
                id=spec.id,
                family=spec.family,
                params=dict(spec.params),
            ),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            candidate_path = Path(tmpdir) / "candidate.yaml"
            candidate_path.write_text(
                textwrap.dedent(
                    """
                    id: candidate-1
                    family: stub_candidate
                    params:
                      threshold: 0.1
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            definition = load_candidate_definition(candidate_path, registry=registry)
            built = build_candidate(candidate_path, registry=registry)

            self.assertEqual(definition.spec.id, "candidate-1")
            self.assertEqual(built.family, "stub_candidate")
            self.assertEqual(built.params["threshold"], 0.1)

    def test_unknown_family_fails_clearly(self) -> None:
        registry = CandidateRegistry()

        with tempfile.TemporaryDirectory() as tmpdir:
            candidate_path = Path(tmpdir) / "candidate.yaml"
            candidate_path.write_text(
                textwrap.dedent(
                    """
                    id: candidate-1
                    family: unknown_family
                    params: {}
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(UnknownCandidateFamilyError) as ctx:
                load_candidate_definition(candidate_path, registry=registry)
            self.assertIn("unknown candidate family", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
