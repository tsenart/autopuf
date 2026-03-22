from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pufopt.candidates.factory import build_candidate
from pufopt.evaluators.honest import HonestEvaluationError, evaluate_honest, write_metrics_artifact
from pufopt.worlds.registry import WorldInstanceRecord, sample_world


class HonestEvaluatorTest(unittest.TestCase):
    def test_classical_crp_metrics_are_computed(self) -> None:
        candidate = build_candidate("candidates/baseline-classical-crp-001.yaml")
        world = sample_world("configs/worlds/lab-clean-v1.yaml", 13)

        metrics = evaluate_honest(candidate, world)

        self.assertIn("far", metrics)
        self.assertIn("frr", metrics)
        self.assertIn("eer", metrics)
        self.assertIn("latency_ms", metrics)
        self.assertIn("crp_lifetime", metrics)

    def test_optical_auth_metrics_are_computed(self) -> None:
        candidate = build_candidate("candidates/baseline-optical-auth-001.yaml")
        world = sample_world("configs/worlds/phone-reader-indoor-v1.yaml", 21)

        metrics = evaluate_honest(candidate, world)

        self.assertGreater(float(metrics["readout_cost"]), 0.0)
        self.assertGreater(float(metrics["enrollment_cost"]), 0.0)
        self.assertIn("robustness_under_drift", metrics)

    def test_metrics_artifact_is_written(self) -> None:
        candidate = build_candidate("candidates/baseline-classical-crp-001.yaml")
        world = sample_world("configs/worlds/lab-clean-v1.yaml", 17)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "metrics.json")
            result_path = write_metrics_artifact(path, candidate, world)
            self.assertTrue(Path(result_path).is_file())

    def test_unsupported_family_fails_clearly(self) -> None:
        class UnsupportedCandidate:
            id = "candidate-unsupported"
            family = "unsupported_family"
            params = {}

        world = WorldInstanceRecord(id="world-1", params={"sensor_noise_sigma": 0.01})

        with self.assertRaises(HonestEvaluationError) as ctx:
            evaluate_honest(UnsupportedCandidate(), world)
        self.assertIn("unsupported candidate family", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
