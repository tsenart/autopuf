from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pufopt.storage.io import read_json_file, read_yaml_file, write_yaml_atomic


class OpsCliTest(unittest.TestCase):
    def test_ops_help_smoke(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "pufopt.ops", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("next-task", result.stdout)
        self.assertIn("verify-task", result.stdout)
        self.assertIn("formalize-claim", result.stdout)

    def test_next_task_pack_verify_and_promote(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            tasks_root = repo_root / "ops" / "tasks"
            (tasks_root / "T100").mkdir(parents=True)
            (repo_root / "outputs").mkdir()
            write_yaml_atomic(
                tasks_root / "T100" / "task.yaml",
                {
                    "id": "T100",
                    "title": "Test task",
                    "status": "ready",
                    "phase": "Phase X",
                    "objective": "Verify the control plane.",
                    "depends_on": [],
                    "inputs": {
                        "design_docs": ["README.md"],
                        "code_paths": ["outputs/example.txt"],
                        "formal_paths": [],
                    },
                    "allowed_write_paths": ["outputs/example.txt"],
                    "required_outputs": ["outputs/example.txt"],
                    "acceptance_criteria": ["required output exists"],
                    "required_commands": [
                        "mkdir -p outputs && printf 'ok\\n' > outputs/example.txt"
                    ],
                    "artifacts": [
                        "verification.json",
                        "formal_check.json",
                        "red_review.md",
                        "reproduction_report.md",
                    ],
                    "risks": [],
                    "escalation_triggers": [],
                    "formal_claim_id": None,
                    "proof_status_required": False,
                    "formal_contract_required": False,
                    "owner_role": "Builder",
                    "reviewer_role": "Red Reviewer",
                    "promoter_role": "Integrator",
                },
            )

            next_task = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pufopt.ops",
                    "next-task",
                    "--tasks-root",
                    str(tasks_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(next_task.returncode, 0, next_task.stderr)
            self.assertIn("task_id: T100", next_task.stdout)

            pack = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pufopt.ops",
                    "pack-context",
                    "--task",
                    "T100",
                    "--tasks-root",
                    str(tasks_root),
                    "--repo-root",
                    str(repo_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(pack.returncode, 0, pack.stderr)
            self.assertTrue((tasks_root / "T100" / "context.md").is_file())

            verify = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pufopt.ops",
                    "verify-task",
                    "--task",
                    "T100",
                    "--tasks-root",
                    str(tasks_root),
                    "--repo-root",
                    str(repo_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(verify.returncode, 0, verify.stderr)
            verification = read_json_file(tasks_root / "T100" / "verification.json")
            self.assertEqual(verification["status"], "self_tested")
            self.assertTrue((tasks_root / "T100" / "red_review.md").is_file())
            self.assertTrue((tasks_root / "T100" / "reproduction_report.md").is_file())
            manifest = read_yaml_file(tasks_root / "T100" / "task.yaml")
            self.assertEqual(manifest["status"], "reproduced")

            promote = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pufopt.ops",
                    "promote-task",
                    "--task",
                    "T100",
                    "--tasks-root",
                    str(tasks_root),
                    "--repo-root",
                    str(repo_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(promote.returncode, 0, promote.stderr)
            promotion = read_yaml_file(tasks_root / "T100" / "promotion.yaml")
            self.assertEqual(promotion["status"], "promoted")
            manifest = read_yaml_file(tasks_root / "T100" / "task.yaml")
            self.assertEqual(manifest["status"], "promoted")

    def test_formalize_claim_refreshes_run_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluate = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pufopt.cli",
                    "evaluate",
                    "--candidate",
                    "candidates/baseline-classical-crp-001.yaml",
                    "--world",
                    "configs/worlds/lab-clean-v1.yaml",
                    "--artifacts-root",
                    tmpdir,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(evaluate.returncode, 0, evaluate.stderr)
            run_dir = next(Path(tmpdir).iterdir())
            claim_path = run_dir / "formal" / "claim.yaml"
            proof_status_path = run_dir / "formal" / "proof_status.json"
            differential_path = run_dir / "formal" / "differential_check.json"
            claim_path.unlink()
            proof_status_path.unlink()
            differential_path.unlink()

            formalize = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pufopt.ops",
                    "formalize-claim",
                    "--run",
                    str(run_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(formalize.returncode, 0, formalize.stderr)
            self.assertTrue(claim_path.is_file())
            self.assertTrue(proof_status_path.is_file())
            self.assertTrue(differential_path.is_file())


if __name__ == "__main__":
    unittest.main()
