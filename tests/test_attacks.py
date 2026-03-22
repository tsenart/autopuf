from __future__ import annotations

import unittest

from pufopt.attacks import default_attack_registry, normalize_attack_budget, run_attack
from pufopt.candidates.factory import build_candidate
from pufopt.worlds.registry import sample_world


class AttacksTest(unittest.TestCase):
    def test_required_attack_families_are_registered(self) -> None:
        families = set(default_attack_registry.families())

        self.assertTrue(
            {
                "modeling",
                "replay",
                "nearest_match",
                "crp_exhaustion",
                "drift_abuse",
            }.issubset(families)
        )

    def test_modeling_attack_runs_on_classical_baseline(self) -> None:
        candidate = build_candidate("candidates/baseline-classical-crp-001.yaml")
        world = sample_world("configs/worlds/lab-clean-v1.yaml", 13)

        result = run_attack("modeling", candidate, world)

        self.assertEqual(result.name, "modeling")
        self.assertIsNotNone(result.success)
        self.assertGreaterEqual(float(result.success), 0.0)
        self.assertLess(float(result.success), 1.0)
        self.assertIn("best_model", result.metrics)
        self.assertEqual(result.metrics["calibration_status"], "heuristic")
        self.assertIn("provenance_ref", result.metrics)

    def test_nearest_match_attack_runs_on_optical_baseline(self) -> None:
        candidate = build_candidate("candidates/baseline-optical-auth-001.yaml")
        world = sample_world("configs/worlds/phone-reader-indoor-v1.yaml", 21)

        result = run_attack("nearest_match", candidate, world)

        self.assertEqual(result.name, "nearest_match")
        self.assertIsNotNone(result.success)
        self.assertGreaterEqual(float(result.success), 0.0)
        self.assertLess(float(result.success), 1.0)
        self.assertEqual(result.metrics["calibration_status"], "heuristic")
        self.assertIn("provenance_ref", result.metrics)

    def test_attack_budget_requires_positive_integers(self) -> None:
        with self.assertRaises(ValueError):
            normalize_attack_budget({"queries": 0})


if __name__ == "__main__":
    unittest.main()
