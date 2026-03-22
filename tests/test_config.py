from __future__ import annotations

import unittest

from pufopt.config import load_attack_heuristics, load_regression_expectations


class ConfigTest(unittest.TestCase):
    def test_attack_heuristics_are_externalized_with_provenance(self) -> None:
        data = load_attack_heuristics()

        self.assertEqual(data["calibration_status"], "heuristic")
        self.assertIn("attacks", data)
        self.assertIn("modeling", data["attacks"])
        self.assertIn("provenance", data["attacks"]["modeling"]["families"]["classical_crp"])

    def test_regression_expectations_are_externalized_with_provenance(self) -> None:
        data = load_regression_expectations()

        self.assertEqual(data["calibration_status"], "heuristic")
        self.assertIn("fixtures", data)
        self.assertIn("regression-modeling-vulnerable-crp-001", data["fixtures"])
        self.assertIn(
            "provenance",
            data["fixtures"]["regression-trust-limited-remote-auth-001"],
        )


if __name__ == "__main__":
    unittest.main()
