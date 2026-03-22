from __future__ import annotations

import unittest

from pufopt.candidates.factory import build_candidate
from pufopt.worlds.registry import sample_world


class BaselineFamiliesTest(unittest.TestCase):
    def test_classical_crp_candidate_builds(self) -> None:
        built = build_candidate("candidates/baseline-classical-crp-001.yaml")
        self.assertEqual(built.family, "classical_crp")
        self.assertEqual(built.params["challenge_space_size"], 128)
        self.assertEqual(len(built.params["challenge_labels"]), 128)

    def test_optical_auth_candidate_builds(self) -> None:
        built = build_candidate("candidates/baseline-optical-auth-001.yaml")
        self.assertEqual(built.family, "optical_auth")
        self.assertEqual(built.params["enrollment_samples"], 64)
        self.assertEqual(len(built.params["feature_labels"]), 96)

    def test_lab_clean_world_samples_deterministically(self) -> None:
        first = sample_world("configs/worlds/lab-clean-v1.yaml", 99)
        second = sample_world("configs/worlds/lab-clean-v1.yaml", 99)
        self.assertEqual(first.params, second.params)
        self.assertLess(float(first.params["observed_sensor_noise_sigma"]), 0.006)

    def test_phone_reader_world_samples_deterministically(self) -> None:
        first = sample_world("configs/worlds/phone-reader-indoor-v1.yaml", 77)
        second = sample_world("configs/worlds/phone-reader-indoor-v1.yaml", 77)
        self.assertEqual(first.params, second.params)
        self.assertIn("observed_illumination_jitter", first.params)
        self.assertIn("observed_angle_variation_deg", first.params)


if __name__ == "__main__":
    unittest.main()
