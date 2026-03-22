from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pufopt.candidates.factory import build_candidate
from pufopt.evaluators.constraints import apply_constraints, load_constraint_config
from pufopt.evaluators.honest import evaluate_honest
from pufopt.evaluators.scoring import load_scoring_config, score_candidate
from pufopt.formal.bridge import finalize_formal_artifacts, run_bounded_differential_check
from pufopt.formal.proof_status import ensure_result_has_proof_status
from pufopt.worlds.registry import sample_world


class FormalBridgeTest(unittest.TestCase):
    def test_classical_crp_differential_check_passes(self) -> None:
        candidate = build_candidate("candidates/baseline-classical-crp-001.yaml")
        world = sample_world("configs/worlds/lab-clean-v1.yaml", 123)
        honest_metrics = evaluate_honest(candidate, world)
        score = score_candidate(
            apply_constraints(
                candidate.id,
                world.id,
                honest_metrics,
                load_constraint_config(),
            ),
            load_scoring_config(),
        )
        score = ensure_result_has_proof_status(score)

        differential = run_bounded_differential_check(candidate, score, run_id="run-test")

        self.assertTrue(differential.supported)
        self.assertTrue(differential.passed)
        self.assertEqual(differential.reference["family"], "classical_crp")
        self.assertEqual(str(differential.reference["expected_lifetime"]), "128")

    def test_finalize_formal_artifacts_writes_claim_and_status(self) -> None:
        candidate = build_candidate("candidates/baseline-classical-crp-001.yaml")
        world = sample_world("configs/worlds/lab-clean-v1.yaml", 123)
        honest_metrics = evaluate_honest(candidate, world)
        score = score_candidate(
            apply_constraints(
                candidate.id,
                world.id,
                honest_metrics,
                load_constraint_config(),
            ),
            load_scoring_config(),
        )
        score = ensure_result_has_proof_status(score)

        with tempfile.TemporaryDirectory() as tmpdir:
            updated = finalize_formal_artifacts(
                tmpdir,
                run_id="run-test",
                candidate=candidate,
                world=world,
                scorecard=score,
            )

            self.assertEqual(updated.proof_status, "specified")
            self.assertIsNotNone(updated.formal_claim_id)
            self.assertTrue((Path(tmpdir) / "formal" / "claim.yaml").is_file())
            self.assertTrue((Path(tmpdir) / "formal" / "proof_status.json").is_file())
            self.assertTrue(
                (Path(tmpdir) / "formal" / "differential_check.json").is_file()
            )

    def test_unsupported_family_writes_differential_without_claim(self) -> None:
        candidate = build_candidate("candidates/baseline-optical-auth-001.yaml")
        world = sample_world("configs/worlds/phone-reader-indoor-v1.yaml", 123)
        honest_metrics = evaluate_honest(candidate, world)
        score = score_candidate(
            apply_constraints(
                candidate.id,
                world.id,
                honest_metrics,
                load_constraint_config(),
            ),
            load_scoring_config(),
        )
        score = ensure_result_has_proof_status(score)

        with tempfile.TemporaryDirectory() as tmpdir:
            updated = finalize_formal_artifacts(
                tmpdir,
                run_id="run-test",
                candidate=candidate,
                world=world,
                scorecard=score,
            )

            self.assertIsNone(updated.formal_claim_id)
            self.assertTrue(
                (Path(tmpdir) / "formal" / "differential_check.json").is_file()
            )
            self.assertFalse((Path(tmpdir) / "formal" / "claim.yaml").exists())


if __name__ == "__main__":
    unittest.main()
