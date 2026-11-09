import json
import pathlib
import random

import pytest

from rac_sim import (Digraph, simulate, Algorithm3, NoDetector, Crash, Offset, Frozen,
                     RandomLie, TamperInbox, FakeDetection, Conceal, satisfies_assumption4,
                     assumption4_violations)

DATA = pathlib.Path(__file__).parent / "data" / "flocal_collusion_graphs.json"


def gen_graph(rng, n, p, f=1):
    """Random strongly connected digraph satisfying Assumption 4, not complete, with real
    two-hop structure (so voting is actually exercised)."""
    while True:
        E = [(u, v) for u in range(n) for v in range(n) if u != v and rng.random() < p]
        g = Digraph(n, E)
        if g.is_strongly_connected() and satisfies_assumption4(g, f) \
                and len(g.edges) < n * (n - 1) and any(g.two_hop_in(i) for i in range(n)):
            return g


def normal_log(d, adversaries):
    return [e for e in d.log if e[1] not in adversaries]


CASES = [(seed, {7: .7, 8: .65, 10: .6}[n], n)
         for seed, n in zip(range(12), [7, 8, 10] * 4)]


def setup(seed, p, n):
    rng = random.Random(seed)
    g = gen_graph(rng, n, p)
    x = [rng.uniform(-10, 10) for _ in range(n)]
    return rng, g, x


# ---- Assumption 4 checker -------------------------------------------------------------
def test_assumption4_complete_graph_ok_and_ring_fails():
    n = 6
    K = Digraph(n, [(u, v) for u in range(n) for v in range(n) if u != v])
    assert satisfies_assumption4(K, 1)
    ring = Digraph(n, [(i, (i + 1) % n) for i in range(n)])
    assert assumption4_violations(ring, 1)


# ---- correctness on random Assumption-4 digraphs --------------------------------------
@pytest.mark.parametrize("seed,p,n", CASES)
def test_no_attack_no_flags(seed, p, n):
    _, g, x = setup(seed, p, n)
    d = Algorithm3(f=1)
    res = simulate(g, x, detector=d, steps=300)
    assert d.log == []
    assert res.max_error() < 1e-9


ATTACKS = {
    "crash": lambda rng, g, b: Crash(3),
    "offset_y": lambda rng, g, b: Offset(3, 4.0),
    "offset_z": lambda rng, g, b: Offset(3, 0.0, 0.3),
    "frozen": lambda rng, g, b: Frozen(3),
    "random": lambda rng, g, b: RandomLie(3, 2.0, seed=1),
    "fake_detection": lambda rng, g, b: FakeDetection(3, rng.choice(g.in_nbrs[b])),
    "tamper_inbox": lambda rng, g, b: TamperInbox(3, rng.choice(g.in_nbrs[b]), 4.0),
}


@pytest.mark.parametrize("name", ATTACKS)
@pytest.mark.parametrize("seed,p,n", CASES[:6])
def test_single_attacker_caught_no_false_positives(seed, p, n, name):
    rng, g, x = setup(seed, p, n)
    b = rng.randrange(n)
    atk = {b: ATTACKS[name](rng, g, b)}
    d = Algorithm3(f=1)
    res = simulate(g, x, atk, d, steps=600)
    assert {j for *_, j, _ in normal_log(d, atk)} == {b}       # only the attacker flagged
    assert res.max_error() < 1e-6


def test_grace_period_is_needed():
    """Decision 3 ('for the second time' = one-step grace). Without it, honest nodes that learn
    about a malicious out-neighbor one step late get flagged."""
    fp = 0
    for seed, p, n in CASES[:8]:
        rng, g, x = setup(seed, p, n)
        b = rng.randrange(n)
        d = Algorithm3(f=1, grace=0)
        res = simulate(g, x, {b: Offset(3, 4.0)}, d, steps=200)
        fp += bool(res.flagged_by_normals() - {b})
    assert fp >= 4


# ---- collusion: one attacker injects, its out-neighbor hides it (1a / faulty reporter) --
def collusion_cases():
    return [(c["n"], c["edges"], c["m"], c["c"]) for c in json.loads(DATA.read_text())]


@pytest.mark.parametrize("n,E,m,c", collusion_cases())
def test_concealing_colluder_caught(n, E, m, c):
    g = Digraph(n, E)
    assert satisfies_assumption4(g, 1)
    bad = {m, c}
    assert all(len(set(g.in_nbrs[v]) & bad) <= 1 for v in range(n) if v not in bad)  # 1-local
    x = [((7 * v) % 11) - 3.0 for v in range(n)]
    atk = {m: Offset(3, 4.0), c: Conceal({m})}

    d = Algorithm3(f=1)
    res = simulate(g, x, atk, d, steps=800)
    assert res.flagged_by_normals() == bad
    assert "1a" in {r for _, i, j, r in normal_log(d, atk) if j == c}
    assert res.max_error() < 1e-6

    undefended = simulate(g, x, atk, NoDetector(), steps=800)
    assert undefended.max_error() > 0.5
