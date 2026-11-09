import random

import numpy as np
import pytest

from rac_sim import (Digraph, circulant, simulate, NoDetector, OracleDetector,
                     Crash, Offset, Frozen, RandomLie)

X6 = [9, 7, 1, 3, 4, 6]   # paper's 6-node initial values; node 6 (index 5) is the adversary


def g6():
    # PLACEHOLDER topology (circulant, in/out-degree 2). Replace with the edge list of the
    # paper's Fig. 5b via Digraph.from_one_indexed(...) once copied from the PDF.
    return circulant(6, (1, 2))


def test_no_attack_converges_to_exact_mean():
    res = simulate(g6(), X6, steps=300)
    assert res.target == pytest.approx(5.0)
    assert res.max_error() < 1e-9


@pytest.mark.parametrize("attack", [
    Crash(at=2), Offset(at=2, dy=5.0), Offset(at=2, dy=-4.0, dz=0.5),
    Frozen(at=2), RandomLie(at=2, scale=3.0),
])
def test_oracle_detection_plus_recovery_gives_average_of_normal_nodes(attack):
    attacks = {5: attack}
    res = simulate(g6(), X6, adversaries=attacks, detector=OracleDetector(attacks), steps=400)
    assert res.target == pytest.approx(4.8)           # (9+7+1+3+4)/5, as in the paper
    assert res.max_error() < 1e-6


def test_without_detection_the_attack_corrupts_the_average():
    attacks = {5: Offset(at=2, dy=5.0)}
    res = simulate(g6(), X6, adversaries=attacks, detector=NoDetector(), steps=400)
    assert res.max_error() > 0.1


def test_late_attack_still_recovered():
    attacks = {5: Offset(at=25, dy=8.0)}
    res = simulate(g6(), X6, adversaries=attacks, detector=OracleDetector(attacks), steps=500)
    assert res.max_error() < 1e-6


def test_two_adversaries_non_neighboring():
    g = circulant(10, (1, 2, 3))
    x = list(range(10))
    attacks = {2: Offset(at=3, dy=4.0), 7: Crash(at=5)}
    res = simulate(g, x, adversaries=attacks, detector=OracleDetector(attacks), steps=600)
    assert res.max_error() < 1e-6


@pytest.mark.parametrize("seed", range(10))
def test_random_strongly_connected_graphs(seed):
    rng = random.Random(seed)
    n = 8
    while True:
        edges = [(i, (i + 1) % n) for i in range(n)]          # Hamiltonian cycle
        edges += [(rng.randrange(n), rng.randrange(n)) for _ in range(14)]
        g = Digraph(n, edges)
        bad = rng.randrange(n)
        rest = [v for v in range(n) if v != bad]
        if g.is_strongly_connected(rest):
            break
    x = [rng.uniform(-10, 10) for _ in range(n)]
    attacks = {bad: Offset(at=rng.randrange(1, 8), dy=rng.uniform(-6, 6))}
    res = simulate(g, x, adversaries=attacks, detector=OracleDetector(attacks), steps=1500)
    assert res.max_error() < 1e-5, res.max_error()
