from __future__ import annotations

import unittest

from pufopt.types import (
    AttackSpec,
    CandidateSpec,
    FormalClaimSpec,
    FrontierEntry,
    PlanDecision,
    PROOF_STATUS_VALUES,
    ScoreCard,
    SearchSpec,
    WorldSpec,
)


class TypesContractTest(unittest.TestCase):
    def test_core_specs_are_constructible(self) -> None:
        candidate = CandidateSpec(
            id="candidate-1",
            family="classical_crp",
            params={"threshold": 0.1},
        )
        world = WorldSpec(
            id="world-1",
            family="lab_clean",
            params={"sensor_noise_sigma": 0.01},
        )
        attack = AttackSpec(name="modeling", params={"budget": 100})
        search = SearchSpec(
            algorithm="evolutionary",
            max_iterations=10,
            seeds=["candidates/a.yaml"],
        )
        score = ScoreCard(
            candidate_id=candidate.id,
            world_id=world.id,
            disposition="survivor",
            utility=0.8,
            hard_constraint_passed=True,
            is_survivor=True,
        )
        frontier = FrontierEntry(
            candidate_id=candidate.id,
            family=candidate.family,
            utility=0.8,
        )
        plan = PlanDecision(action="explore", reason="seed the search")
        formal = FormalClaimSpec(
            id="claim-1",
            candidate_family=candidate.family,
            security_game="example_game",
            assumptions=["honest verifier"],
            claim="Example claim.",
            proof_status="specified",
        )

        self.assertEqual(candidate.family, "classical_crp")
        self.assertEqual(world.family, "lab_clean")
        self.assertEqual(attack.name, "modeling")
        self.assertEqual(search.max_iterations, 10)
        self.assertTrue(score.is_survivor)
        self.assertEqual(frontier.family, "classical_crp")
        self.assertEqual(plan.action, "explore")
        self.assertEqual(formal.proof_status, "specified")

    def test_proof_status_values_match_contract(self) -> None:
        self.assertEqual(
            PROOF_STATUS_VALUES,
            (
                "empirical_only",
                "specified",
                "partially_proved",
                "proved",
                "counterexample_found",
            ),
        )


if __name__ == "__main__":
    unittest.main()
