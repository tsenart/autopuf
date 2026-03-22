from __future__ import annotations

import unittest

from pufopt.candidates.factory import build_candidate_definition
from pufopt.candidates.mutations import mutate_candidate_spec
from pufopt.storage.schema import load_candidate_spec


class MutationTest(unittest.TestCase):
    def test_classical_mutations_build_and_stay_in_domain(self) -> None:
        spec = load_candidate_spec("candidates/baseline-classical-crp-001.yaml")

        mutations = mutate_candidate_spec(
            spec,
            metrics={
                "modeling_attack_success": 0.8,
                "replay_attack_success": 0.5,
                "crp_exhaustion_attack_success": 0.4,
            },
        )

        self.assertTrue(mutations)
        for mutation in mutations:
            built = build_candidate_definition(mutation).build()
            self.assertIn(
                built.params["challenge_space_size"],
                {64, 128, 256, 512},
            )
            self.assertIn(built.params["response_bit_width"], {1, 2, 4})
            self.assertIn(built.params["replay_window"], {1, 2, 4, 8})

    def test_optical_mutations_build_and_stay_in_domain(self) -> None:
        spec = load_candidate_spec("candidates/baseline-optical-auth-001.yaml")

        mutations = mutate_candidate_spec(
            spec,
            metrics={
                "modeling_attack_success": 0.4,
                "counterfeit_attack_success": 0.35,
                "replay_attack_success": 0.5,
                "crp_exhaustion_attack_success": 0.3,
            },
        )

        self.assertTrue(mutations)
        for mutation in mutations:
            built = build_candidate_definition(mutation).build()
            self.assertIn(
                built.params["enrollment_samples"],
                {16, 32, 64, 128},
            )
            self.assertIn(
                built.params["feature_dimension"],
                {32, 64, 96, 128},
            )
            self.assertIn(
                built.params["session_policy"],
                {"one_time_use", "bounded_reuse"},
            )


if __name__ == "__main__":
    unittest.main()
