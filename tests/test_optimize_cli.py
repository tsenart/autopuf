from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


class OptimizeCliTest(unittest.TestCase):
    def test_optimize_frontier_and_report_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            optimize = subprocess.run(
                [
                    ".venv/bin/python",
                    "-m",
                    "pufopt.cli",
                    "optimize",
                    "--suite",
                    "suites/v1-auth-search.yaml",
                    "--artifacts-root",
                    tmpdir,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(optimize.returncode, 0, optimize.stderr)
            self.assertIn("Optimization run written to", optimize.stdout)

            run_dirs = [path for path in Path(tmpdir).iterdir() if path.is_dir()]
            self.assertEqual(len(run_dirs), 1)
            run_dir = run_dirs[0]
            self.assertTrue((run_dir / "suite.yaml").is_file())
            self.assertTrue((run_dir / "frontier" / "update.json").is_file())
            self.assertTrue((run_dir / "planner" / "decision.json").is_file())
            self.assertTrue((run_dir / "score" / "score.json").is_file())
            self.assertTrue((run_dir / "summary.md").is_file())
            self.assertTrue((run_dir / "formal" / "proof_status.json").is_file())
            self.assertTrue((run_dir / "formal" / "differential_check.json").is_file())

            frontier = subprocess.run(
                [
                    ".venv/bin/python",
                    "-m",
                    "pufopt.cli",
                    "frontier",
                    "--run",
                    str(run_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(frontier.returncode, 0, frontier.stderr)
            self.assertIn("# Frontier", frontier.stdout)

            report = subprocess.run(
                [
                    ".venv/bin/python",
                    "-m",
                    "pufopt.cli",
                    "report",
                    "--run",
                    str(run_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(report.returncode, 0, report.stderr)
            self.assertIn("# Optimization Summary", report.stdout)


if __name__ == "__main__":
    unittest.main()
