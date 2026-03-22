from __future__ import annotations

import tempfile
import unittest

from pufopt.loop.search import optimize_suite


TEMPLATE_SUITES = [
    "suites/template-smoke-evaluate.yaml",
    "suites/template-attack-analysis.yaml",
    "suites/template-short-optimization.yaml",
    "suites/template-regression-run.yaml",
]


class SuiteTemplatesTest(unittest.TestCase):
    def test_all_suite_templates_run_without_editing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            for suite_path in TEMPLATE_SUITES:
                run_root = optimize_suite(suite_path, artifacts_root=tmpdir)
                self.assertTrue((run_root / "summary.md").is_file(), suite_path)
                self.assertTrue((run_root / "frontier" / "update.json").is_file(), suite_path)


if __name__ == "__main__":
    unittest.main()
