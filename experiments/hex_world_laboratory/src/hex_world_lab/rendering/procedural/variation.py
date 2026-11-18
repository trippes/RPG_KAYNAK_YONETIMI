"""Stable seed normalization and isolated random generators."""
import hashlib
import random


Seed = int | str


def normalize_seed(seed: Seed) -> int:
    """Convert an integer or string seed to a stable non-negative integer."""
    if isinstance(seed, bool) or not isinstance(seed, (int, str)):
        raise TypeError("seed must be an integer or string")
    if isinstance(seed, int):
        return seed
    if not seed:
        raise ValueError("string seed must not be empty")
    digest = hashlib.blake2b(seed.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big", signed=False)


def create_rng(seed: Seed) -> random.Random:
    """Create an independent RNG; global random state is never accessed."""
    return random.Random(normalize_seed(seed))
