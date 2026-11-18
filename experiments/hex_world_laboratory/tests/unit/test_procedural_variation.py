import random

import pytest
from hex_world_lab.rendering.procedural.variation import create_rng, normalize_seed


def test_integer_and_string_seeds_are_stable():
    assert normalize_seed(42) == 42
    assert normalize_seed("oak-tree-17") == normalize_seed("oak-tree-17")
    assert normalize_seed("oak-tree-17") != normalize_seed("oak-tree-18")


def test_rng_repeats_sequence_for_same_seed_and_differs_for_other_seed():
    first = [create_rng("fern").random() for _ in range(3)]
    second_rng = create_rng("fern")
    second = [second_rng.random() for _ in range(3)]
    third = [create_rng("moss").random() for _ in range(3)]
    assert first == second
    assert first[0] != third[0]


def test_rng_does_not_change_module_global_random_state():
    random.seed(913)
    before = random.getstate()
    rng = create_rng("isolated")
    rng.random()
    rng.randint(1, 100)
    assert random.getstate() == before


@pytest.mark.parametrize("seed", [True, 1.5, None, b"bytes"])
def test_seed_rejects_unsupported_types(seed):
    with pytest.raises(TypeError):
        normalize_seed(seed)


def test_seed_rejects_empty_string():
    with pytest.raises(ValueError):
        normalize_seed("")
