from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pufopt.storage.artifacts import (
    create_run_layout,
    deterministic_run_id,
    read_artifact,
    write_artifact,
    write_run_context,
)
from pufopt.storage.io import read_json_file
from pufopt.types import CandidateSpec, FormalClaimSpec, ScoreCard, WorldSpec
from tests.utils import DEFAULT_TEST_SEED, seeded_random


class StorageContractTest(unittest.TestCase):
    def test_run_layout_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            seeds = {"evaluation": DEFAULT_TEST_SEED}
            first = create_run_layout(
                tmpdir,
                suite_id="suite-1",
                candidate_id="candidate-1",
                world_id="world-1",
                seeds=seeds,
            )
            second = create_run_layout(
                tmpdir,
                suite_id="suite-1",
                candidate_id="candidate-1",
                world_id="world-1",
                seeds=seeds,
            )

            self.assertEqual(first.run_id, second.run_id)
            self.assertEqual(first.root, second.root)
            self.assertTrue(first.candidate_dir.is_dir())
            self.assertTrue(first.world_dir.is_dir())
            self.assertTrue(first.attacks_dir.is_dir())

    def test_major_objects_serialize_and_reload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            layout = create_run_layout(
                tmpdir,
                candidate_id="candidate-1",
                world_id="world-1",
                seeds={"evaluation": DEFAULT_TEST_SEED},
            )
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
            score = ScoreCard(
                candidate_id="candidate-1",
                world_id="world-1",
                disposition="survivor",
                utility=0.91,
                hard_constraint_passed=True,
                is_survivor=True,
                proof_status="specified",
                formal_claim_id="claim-1",
            )
            formal = FormalClaimSpec(
                id="claim-1",
                candidate_family="classical_crp",
                security_game="game-1",
                assumptions=["honest verifier"],
                claim="The candidate survives the bounded game.",
                proof_status="specified",
            )

            write_artifact(layout, "candidate/spec.json", candidate)
            write_artifact(layout, "world/spec.json", world)
            write_artifact(layout, "score/score.json", score)
            write_artifact(layout, "formal/claim.json", formal)

            self.assertEqual(
                read_artifact(layout, "candidate/spec.json")["family"],
                "classical_crp",
            )
            self.assertEqual(
                read_artifact(layout, "world/spec.json")["family"],
                "lab_clean",
            )
            self.assertEqual(
                read_artifact(layout, "score/score.json")["formal_claim_id"],
                "claim-1",
            )
            self.assertEqual(
                read_artifact(layout, "formal/claim.json")["security_game"],
                "game-1",
            )

    def test_context_always_records_seeds_and_config_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            layout = create_run_layout(
                tmpdir,
                suite_id="suite-1",
                candidate_id="candidate-1",
                world_id="world-1",
                seeds={"evaluation": DEFAULT_TEST_SEED},
            )
            write_run_context(
                layout,
                seeds={"evaluation": DEFAULT_TEST_SEED},
                config_refs={
                    "suite": "suites/example.yaml",
                    "candidate": "candidates/example.yaml",
                    "world": "configs/worlds/example.yaml",
                },
                metadata={"note": "test"},
            )

            context = read_json_file(layout.context_path)
            self.assertEqual(context["seeds"]["evaluation"], DEFAULT_TEST_SEED)
            self.assertEqual(context["config_refs"]["suite"], "suites/example.yaml")
            self.assertEqual(context["metadata"]["note"], "test")

    def test_atomic_write_leaves_no_temp_files_behind(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            layout = create_run_layout(
                tmpdir,
                candidate_id="candidate-1",
                world_id="world-1",
                seeds={"evaluation": seeded_random().randint(1, 10_000)},
            )
            target = write_artifact(layout, "score/score.json", {"utility": 0.5})

            temp_files = list(Path(target.parent).glob(".*.tmp"))
            self.assertEqual(temp_files, [])
            self.assertTrue(target.is_file())

    def test_run_id_function_matches_layout(self) -> None:
        seeds = {"evaluation": DEFAULT_TEST_SEED}
        expected = deterministic_run_id(
            suite_id="suite-1",
            candidate_id="candidate-1",
            world_id="world-1",
            seeds=seeds,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            layout = create_run_layout(
                tmpdir,
                suite_id="suite-1",
                candidate_id="candidate-1",
                world_id="world-1",
                seeds=seeds,
            )
            self.assertEqual(layout.run_id, expected)


if __name__ == "__main__":
    unittest.main()
