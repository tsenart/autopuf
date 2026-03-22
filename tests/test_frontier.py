from __future__ import annotations

import unittest

from pufopt.loop.frontier import FrontierState
from pufopt.types import ScoreCard


def _survivor(candidate_id: str, utility: float, *, far: float, latency_ms: float) -> ScoreCard:
    return ScoreCard(
        candidate_id=candidate_id,
        world_id="world-1",
        disposition="survivor",
        utility=utility,
        hard_constraint_passed=True,
        is_survivor=True,
        metrics={
            "far": far,
            "frr": far,
            "latency_ms": latency_ms,
            "readout_cost": 0.1,
            "robustness_under_drift": 0.9,
            "crp_lifetime": 128,
        },
    )


class FrontierStateTest(unittest.TestCase):
    def test_frontier_excludes_rejected_candidates(self) -> None:
        frontier = FrontierState()
        update = frontier.update(
            ScoreCard(
                candidate_id="candidate-rejected",
                world_id="world-1",
                disposition="rejected",
                hard_constraint_passed=False,
                is_survivor=False,
                reject_reasons=["far too high"],
                metrics={"far": 0.5},
            ),
            family="classical_crp",
        )

        self.assertEqual(update.status, "rejected")
        self.assertEqual(len(frontier.frontier), 0)
        self.assertEqual(len(frontier.rejected), 1)

    def test_dominated_candidates_are_tracked_separately(self) -> None:
        frontier = FrontierState()
        frontier.update(
            _survivor("candidate-strong", 0.9, far=0.02, latency_ms=5.0),
            family="classical_crp",
        )
        update = frontier.update(
            _survivor("candidate-weak", 0.7, far=0.05, latency_ms=8.0),
            family="classical_crp",
        )

        self.assertEqual(update.status, "dominated")
        self.assertEqual(len(frontier.frontier), 1)
        self.assertEqual(len(frontier.dominated), 1)

    def test_repeated_updates_are_deterministic(self) -> None:
        scorecards = [
            _survivor("candidate-b", 0.78, far=0.03, latency_ms=6.0),
            _survivor("candidate-a", 0.81, far=0.02, latency_ms=5.0),
        ]
        first = FrontierState()
        second = FrontierState()

        for scorecard in scorecards:
            first.update(scorecard, family="classical_crp")
            second.update(scorecard, family="classical_crp")

        self.assertEqual(first.snapshot(), second.snapshot())


if __name__ == "__main__":
    unittest.main()
