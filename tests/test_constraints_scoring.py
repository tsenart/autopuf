from __future__ import annotations

import unittest

from pufopt.evaluators.constraints import ConstraintConfig, apply_constraints
from pufopt.evaluators.scoring import ResultPolicy, ScoringConfig, WeightConfig, score_candidate


class ConstraintsAndScoringTest(unittest.TestCase):
    def test_constraints_reject_out_of_bounds_metrics(self) -> None:
        config = ConstraintConfig(
            max_far=0.1,
            max_frr=0.2,
            max_latency_ms=10.0,
            min_crp_lifetime=32,
            max_readout_cost=1.0,
            min_confidence=0.7,
        )
        metrics = {
            "far": 0.2,
            "frr": 0.05,
            "latency_ms": 5.0,
            "crp_lifetime": 128,
            "readout_cost": 0.2,
            "confidence": 0.9,
        }

        scorecard = apply_constraints("candidate-1", "world-1", metrics, config)

        self.assertEqual(scorecard.disposition, "rejected")
        self.assertFalse(scorecard.hard_constraint_passed)
        self.assertTrue(scorecard.reject_reasons)

    def test_scoring_applies_only_to_survivors_and_uses_policy(self) -> None:
        scorecard = apply_constraints(
            "candidate-1",
            "world-1",
            {
                "far": 0.02,
                "frr": 0.03,
                "eer": 0.025,
                "latency_ms": 7.0,
                "readout_cost": 0.2,
                "enrollment_cost": 1.0,
                "crp_lifetime": 128,
                "min_entropy_estimate": 4.0,
                "robustness_under_drift": 0.92,
                "confidence": 0.88,
            },
            ConstraintConfig(
                max_far=0.1,
                max_frr=0.2,
                max_latency_ms=25.0,
                min_crp_lifetime=32,
                max_readout_cost=1.0,
                min_confidence=0.7,
            ),
        )
        scored = score_candidate(
            scorecard,
            ScoringConfig(
                weights=WeightConfig(
                    security=0.4,
                    robustness=0.25,
                    efficiency=0.2,
                    operability=0.15,
                ),
                strong_result_policy=ResultPolicy(
                    survivor_required=True,
                    frontier_update=False,
                    score_threshold=0.5,
                    improvement_over_baseline=None,
                    surprising_margin=0.1,
                ),
            ),
        )

        self.assertEqual(scored.disposition, "survivor")
        self.assertIsNotNone(scored.utility)
        self.assertTrue(scored.strong_result)

    def test_scoring_penalizes_adversarial_success(self) -> None:
        config = ScoringConfig(
            weights=WeightConfig(
                security=0.4,
                robustness=0.25,
                efficiency=0.2,
                operability=0.15,
            ),
            strong_result_policy=ResultPolicy(
                survivor_required=True,
                frontier_update=False,
                score_threshold=0.6,
                improvement_over_baseline=None,
                surprising_margin=0.1,
            ),
        )
        baseline_metrics = {
            "far": 0.02,
            "frr": 0.03,
            "eer": 0.025,
            "latency_ms": 7.0,
            "readout_cost": 0.2,
            "enrollment_cost": 1.0,
            "crp_lifetime": 128,
            "min_entropy_estimate": 4.0,
            "robustness_under_drift": 0.92,
            "confidence": 0.88,
        }
        attacked_metrics = dict(baseline_metrics)
        attacked_metrics.update(
            {
                "modeling_attack_success": 0.95,
                "replay_attack_success": 0.7,
                "counterfeit_attack_success": 0.8,
                "crp_exhaustion_attack_success": 0.4,
                "drift_abuse_attack_success": 0.3,
            }
        )

        baseline_score = score_candidate(
            apply_constraints(
                "candidate-1",
                "world-1",
                baseline_metrics,
                ConstraintConfig(
                    max_far=0.1,
                    max_frr=0.2,
                    max_latency_ms=25.0,
                    min_crp_lifetime=32,
                    max_readout_cost=1.0,
                    min_confidence=0.7,
                ),
            ),
            config,
        )
        attacked_score = score_candidate(
            apply_constraints(
                "candidate-1",
                "world-1",
                attacked_metrics,
                ConstraintConfig(
                    max_far=0.1,
                    max_frr=0.2,
                    max_latency_ms=25.0,
                    min_crp_lifetime=32,
                    max_readout_cost=1.0,
                    min_confidence=0.7,
                ),
            ),
            config,
        )

        assert baseline_score.utility is not None
        assert attacked_score.utility is not None
        self.assertGreater(baseline_score.utility, attacked_score.utility)
        self.assertTrue(baseline_score.strong_result)
        self.assertFalse(attacked_score.strong_result)


if __name__ == "__main__":
    unittest.main()
