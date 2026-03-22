from __future__ import annotations

import random

DEFAULT_TEST_SEED = 1729


def seeded_random(seed: int = DEFAULT_TEST_SEED) -> random.Random:
    """Return a deterministic random generator for tests."""
    return random.Random(seed)

