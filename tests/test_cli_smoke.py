from __future__ import annotations

import subprocess
import sys
import unittest

from pufopt.cli import build_parser


class CliSmokeTest(unittest.TestCase):
    def test_cli_help_smoke(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "pufopt.cli", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("optimize", result.stdout)
        self.assertIn("evaluate", result.stdout)
        self.assertIn("attack", result.stdout)

    def test_subcommand_parsing(self) -> None:
        parser = build_parser()

        optimize = parser.parse_args(["optimize", "--suite", "suites/demo.yaml"])
        evaluate = parser.parse_args(
            ["evaluate", "--candidate", "candidates/demo.yaml", "--world", "worlds/demo.yaml"]
        )
        attack = parser.parse_args(
            [
                "attack",
                "--candidate",
                "candidates/demo.yaml",
                "--world",
                "worlds/demo.yaml",
                "--attack",
                "modeling",
            ]
        )
        frontier = parser.parse_args(["frontier", "--run", "artifacts/runs/demo"])
        report = parser.parse_args(["report", "--run", "artifacts/runs/demo"])

        self.assertEqual(optimize.command, "optimize")
        self.assertEqual(optimize.suite, "suites/demo.yaml")
        self.assertEqual(evaluate.command, "evaluate")
        self.assertEqual(evaluate.candidate, "candidates/demo.yaml")
        self.assertEqual(attack.attack_name, "modeling")
        self.assertEqual(frontier.command, "frontier")
        self.assertEqual(report.command, "report")


if __name__ == "__main__":
    unittest.main()
