from __future__ import annotations

import unittest

from pufopt.candidates.factory import build_candidate
from pufopt.evaluators.adversarial import REQUIRED_V1_ATTACKS, evaluate_with_attacks
from pufopt.evaluators.honest import evaluate_honest
from pufopt.worlds.registry import sample_world


class AdversarialEvaluatorTest(unittest.TestCase):
    def test_evaluate_with_attacks_merges_canonical_metrics(self) -> None:
        candidate = build_candidate("candidates/baseline-classical-crp-001.yaml")
        world = sample_world("configs/worlds/lab-clean-v1.yaml", 123)
        honest_metrics = evaluate_honest(candidate, world)

        result = evaluate_with_attacks(candidate, world, honest_metrics, seed=123)

        self.assertEqual(result.candidate_id, candidate.id)
        self.assertEqual(result.world_id, world.id)
        self.assertEqual(result.seeds["evaluation"], 123)
        self.assertEqual({attack.name for attack in result.attacks}, set(REQUIRED_V1_ATTACKS))
        self.assertIn("far", result.honest_metrics)
        self.assertIn("modeling_attack_success", result.honest_metrics)
        self.assertIn("replay_attack_success", result.honest_metrics)
        self.assertIn("nearest_match_attack_success", result.honest_metrics)
        self.assertIn("counterfeit_attack_success", result.honest_metrics)
        self.assertIn("crp_exhaustion_attack_success", result.honest_metrics)
        self.assertIn("drift_abuse_attack_success", result.honest_metrics)


if __name__ == "__main__":
    unittest.main()
