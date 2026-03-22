from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from pufopt.config import load_regression_expectations
from pufopt.loop.search import optimize_suite


class RegressionSuitesTest(unittest.TestCase):
    def test_regression_fixtures_hit_expected_boundaries(self) -> None:
        expectations = load_regression_expectations()["fixtures"]

        with tempfile.TemporaryDirectory() as tmpdir:
            for fixture_id, fixture in expectations.items():
                run_root = optimize_suite(fixture["suite"], artifacts_root=tmpdir)
                evaluation = _read_json(run_root / "iterations" / "000" / "evaluation.json")

                for metric_name, expectation in fixture["expectations"].items():
                    actual = _resolve_metric(evaluation, metric_name)
                    _assert_expectation(self, fixture_id, metric_name, actual, expectation)

    def test_combined_regression_suite_runs_and_writes_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = optimize_suite(
                "suites/regression-known-boundaries.yaml",
                artifacts_root=tmpdir,
            )
            summary = (run_root / "summary.md").read_text(encoding="utf-8")
            frontier = _read_json(run_root / "frontier" / "update.json")

            self.assertIn("# Optimization Summary", summary)
            self.assertIn("next_action", summary)
            self.assertGreaterEqual(int(frontier["counts"]["frontier"]), 1)
            self.assertEqual(int(frontier["iterations_completed"]), 3)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_metric(evaluation: dict[str, Any], metric_name: str) -> float:
    honest_metrics = evaluation.get("honest_metrics", {})
    if metric_name in honest_metrics:
        return float(honest_metrics[metric_name])

    for attack in evaluation.get("attacks", []):
        metrics = attack.get("metrics", {})
        if metric_name in metrics:
            return float(metrics[metric_name])
    raise AssertionError(f"metric {metric_name!r} not found in evaluation artifact")


def _assert_expectation(
    case: unittest.TestCase,
    fixture_id: str,
    metric_name: str,
    actual: float,
    expectation: dict[str, Any],
) -> None:
    operator = expectation["op"]
    expected = float(expectation["value"])
    message = f"{fixture_id}: expected {metric_name} {operator} {expected}, got {actual}"
    if operator == ">=":
        case.assertGreaterEqual(actual, expected, message)
        return
    if operator == "<=":
        case.assertLessEqual(actual, expected, message)
        return
    raise AssertionError(f"unsupported operator {operator!r}")


if __name__ == "__main__":
    unittest.main()
