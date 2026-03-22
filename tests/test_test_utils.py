from __future__ import annotations

import unittest

from tests.utils import DEFAULT_TEST_SEED, seeded_random


class TestUtilsContractTest(unittest.TestCase):
    def test_seeded_random_is_deterministic(self) -> None:
        first = seeded_random(DEFAULT_TEST_SEED)
        second = seeded_random(DEFAULT_TEST_SEED)

        self.assertEqual(first.random(), second.random())
        self.assertEqual(first.randint(1, 1000), second.randint(1, 1000))


if __name__ == "__main__":
    unittest.main()
