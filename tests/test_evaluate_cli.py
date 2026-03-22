from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class EvaluateCliTest(unittest.TestCase):
    def test_evaluate_command_writes_run_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    ".venv/bin/python",
                    "-m",
                    "pufopt.cli",
                    "evaluate",
                    "--candidate",
                    "candidates/baseline-classical-crp-001.yaml",
                    "--world",
                    "configs/worlds/lab-clean-v1.yaml",
                    "--artifacts-root",
                    tmpdir,
                    "--seed",
                    "123",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Run written to", result.stdout)

            run_dirs = [path for path in Path(tmpdir).iterdir() if path.is_dir()]
            self.assertEqual(len(run_dirs), 1)
            run_dir = run_dirs[0]
            self.assertTrue((run_dir / "candidate" / "candidate.yaml").is_file())
            self.assertTrue((run_dir / "world" / "world.yaml").is_file())
            self.assertTrue((run_dir / "honest" / "metrics.json").is_file())
            self.assertTrue((run_dir / "score" / "evaluation.json").is_file())
            self.assertTrue((run_dir / "score" / "score.json").is_file())
            self.assertTrue((run_dir / "context.json").is_file())
            self.assertTrue((run_dir / "summary.md").is_file())
            self.assertTrue((run_dir / "attacks" / "modeling.json").is_file())
            self.assertTrue((run_dir / "attacks" / "replay.json").is_file())
            self.assertTrue((run_dir / "attacks" / "nearest_match.json").is_file())
            self.assertTrue((run_dir / "attacks" / "crp_exhaustion.json").is_file())
            self.assertTrue((run_dir / "attacks" / "drift_abuse.json").is_file())

            evaluation = json.loads(
                (run_dir / "score" / "evaluation.json").read_text(encoding="utf-8")
            )
            self.assertIn("counterfeit_attack_success", evaluation["honest_metrics"])


if __name__ == "__main__":
    unittest.main()
