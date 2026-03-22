from __future__ import annotations

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from pufopt.storage.schema import (
    SchemaValidationError,
    load_candidate_spec,
    load_formal_claim_spec,
    validate_candidate_spec,
    validate_formal_claim_spec,
    validate_suite_spec,
    validate_world_spec,
)


class SchemaValidationTest(unittest.TestCase):
    def test_valid_candidate_spec(self) -> None:
        spec = validate_candidate_spec(
            {
                "id": "baseline-optical-auth-001",
                "family": "optical_auth",
                "params": {
                    "feature_extractor": "spectral_histogram_v1",
                    "enrollment_samples": 64,
                },
            }
        )
        self.assertEqual(spec.id, "baseline-optical-auth-001")
        self.assertEqual(spec.family, "optical_auth")

    def test_invalid_candidate_family_raises_actionable_error(self) -> None:
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_candidate_spec(
                {
                    "id": "candidate-1",
                    "family": "",
                    "params": {},
                }
            )
        self.assertIn("candidate.family must not be empty", str(ctx.exception))

    def test_invalid_world_params_raise_actionable_error(self) -> None:
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_world_spec(
                {
                    "id": "world-1",
                    "params": ["not", "a", "mapping"],
                }
            )
        self.assertIn("world.params must be a mapping", str(ctx.exception))

    def test_valid_search_suite_spec(self) -> None:
        spec = validate_suite_spec(
            {
                "id": "v1-auth-search",
                "search": {
                    "algorithm": "evolutionary",
                    "max_iterations": 200,
                    "seeds": [
                        "candidates/baseline-optical-auth-001.yaml",
                        "candidates/baseline-classical-crp-001.yaml",
                    ],
                },
                "worlds": [
                    "configs/worlds/phone-reader-indoor-v1.yaml",
                    "configs/worlds/lab-clean-v1.yaml",
                ],
                "attacks": ["modeling", "replay"],
                "scoring": {"file": "configs/scoring/default.yaml"},
            }
        )
        self.assertEqual(spec.search.algorithm, "evolutionary")
        self.assertEqual(spec.attacks[0].name, "modeling")
        self.assertEqual(spec.scoring_config, "configs/scoring/default.yaml")

    def test_invalid_suite_missing_attacks_raises(self) -> None:
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_suite_spec(
                {
                    "id": "bad-suite",
                    "search": {"algorithm": "evolutionary"},
                    "worlds": ["configs/worlds/lab-clean-v1.yaml"],
                }
            )
        self.assertIn("suite.attacks is required", str(ctx.exception))

    def test_invalid_suite_candidate_without_world_raises(self) -> None:
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_suite_spec(
                {
                    "id": "bad-run",
                    "candidate": "candidates/example.yaml",
                    "attacks": ["modeling"],
                }
            )
        self.assertIn("suite.world is required", str(ctx.exception))

    def test_invalid_formal_claim_proof_status_raises(self) -> None:
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_formal_claim_spec(
                {
                    "id": "claim-1",
                    "candidate_family": "optical_auth",
                    "security_game": "game-1",
                    "assumptions": ["honest verifier"],
                    "claim": "Something is true.",
                    "proof_status": "totally_proved",
                }
            )
        self.assertIn("formal_claim.proof_status must be one of", str(ctx.exception))

    def test_load_candidate_spec_from_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            candidate_path = Path(tmpdir) / "candidate.yaml"
            candidate_path.write_text(
                textwrap.dedent(
                    """
                    id: candidate-1
                    family: classical_crp
                    params:
                      threshold: 0.1
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            spec = load_candidate_spec(candidate_path)
            self.assertEqual(spec.family, "classical_crp")

    def test_load_formal_claim_spec_from_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            claim_path = Path(tmpdir) / "claim.json"
            claim_path.write_text(
                json.dumps(
                    {
                        "id": "claim-1",
                        "candidate_family": "optical_auth",
                        "security_game": "game-1",
                        "assumptions": ["honest verifier"],
                        "claim": "Something is true.",
                        "proof_status": "specified",
                    }
                ),
                encoding="utf-8",
            )

            spec = load_formal_claim_spec(claim_path)
            self.assertEqual(spec.proof_status, "specified")


if __name__ == "__main__":
    unittest.main()
