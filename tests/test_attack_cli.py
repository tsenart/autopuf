from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class AttackCliTest(unittest.TestCase):
    def test_attack_command_writes_attack_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    ".venv/bin/python",
                    "-m",
                    "pufopt.cli",
                    "attack",
                    "--candidate",
                    "candidates/baseline-classical-crp-001.yaml",
                    "--world",
                    "configs/worlds/lab-clean-v1.yaml",
                    "--attack",
                    "modeling",
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
            self.assertIn("Attack run written to", result.stdout)

            run_dirs = [path for path in Path(tmpdir).iterdir() if path.is_dir()]
            self.assertEqual(len(run_dirs), 1)
            run_dir = run_dirs[0]
            artifact_path = run_dir / "attacks" / "modeling.json"
            self.assertTrue(artifact_path.is_file())
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["name"], "modeling")
            self.assertIn("attack_success", payload["metrics"])


if __name__ == "__main__":
    unittest.main()
