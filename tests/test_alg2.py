import random

import pytest

from rac_sim import (undirected, simulate, Algorithm2, NoDetector, Crash, Offset, Frozen,
                     RandomLie, TamperInbox, FakeDetection)

X5 = [8, 6, 1, 3, 9]


def g5():
    # PLACEHOLDER for the paper's Fig. 5a: K5 minus edge {1,2}. 3-connected, and adversaries
    # 4 and 5 (indices 3, 4) are neighbors with normal common neighbors 1, 2, 3.
    E = [(u, v) for u in range(1, 6) for v in range(u + 1, 6) if (u, v) != (1, 2)]
    return undirected(5, E, one_indexed=True)


def assert_no_false_positives(res, adversaries):
    assert res.flagged_by_normals() <= set(adversaries)


def test_no_attack_no_flags_exact_mean():
    d = Algorithm2()
    res = simulate(g5(), X5, detector=d, steps=200)
    assert d.log == []
    assert res.max_error() < 1e-9


def test_paper_5node_scenario():
    # Paper: node 5 attacks at k=4, node 4 manipulates its own value at k=13 -> average 5
    atk = {4: Offset(at=4, dy=5.0), 3: Offset(at=13, dy=-3.0)}
    d = Algorithm2()
    res = simulate(g5(), X5, atk, d, steps=300)
    assert res.target == pytest.approx(5.0)
    assert res.flagged_by_normals() == {3, 4}
    assert res.first_detection(4) == 5 and res.first_detection(3) == 14   # one step after
    assert res.max_error() < 1e-9


def test_without_detection_same_attack_breaks_average():
    atk = {4: Offset(at=4, dy=5.0), 3: Offset(at=13, dy=-3.0)}
    res = simulate(g5(), X5, atk, NoDetector(), steps=300)
    assert res.max_error() > 0.1


@pytest.mark.parametrize("attack,reason", [
    (Crash(at=3), "silent"),
    (Offset(at=3, dy=4.0), "step4"),
    (Offset(at=3, dy=0.0, dz=0.3), "step4"),     # z-channel only
    (Frozen(at=3), "step4"),
    (RandomLie(at=3, scale=2.0), "step4"),
    (FakeDetection(at=3, victim=0), "step1"),
    (TamperInbox(at=3, src=0, dy=4.0), "step3"),  # lies about what honest node 1 sent
])
def test_each_attack_detected_by_expected_check(attack, reason):
    atk = {4: attack}
    d = Algorithm2()
    res = simulate(g5(), X5, atk, d, steps=300)
    assert res.flagged_by_normals() == {4}
    assert {r for (_, _, j, r) in d.log if j == 4} == {reason}
    assert res.first_detection(4) == 4
    assert res.max_error(target=(8 + 6 + 1 + 3) / 4) < 1e-9


# ---- Lemma 1: colluding neighbors need a normal common neighbor ----------------------
# Nodes 0-3 normal, 4 and 5 malicious and adjacent. 4 lies about what 5 sent it; 5 stays quiet
# about it (otherwise behaves honestly). Only a normal common neighbor of 4 and 5 can catch it.
BASE = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (4, 0), (4, 1), (5, 2), (5, 3), (4, 5)]
X6 = [2, 9, 4, 7, 5, 1]


def test_lemma1_caught_with_common_normal_neighbor():
    g = undirected(6, BASE + [(0, 5)])           # node 0 now neighbors both 4 and 5
    atk = {4: TamperInbox(at=5, src=5, dy=6.0), 5: Offset(at=10**9)}   # 5 never misbehaves
    d = Algorithm2()
    res = simulate(g, X6, atk, d, steps=400)
    assert res.flagged_by_normals() == {4}
    assert {r for *_, r in d.log} == {"step3"}
    # 5 behaved properly throughout, so it belongs to N_0 and counts toward the target
    assert res.max_error(target=(2 + 9 + 4 + 7 + 1) / 5) < 1e-9


def test_lemma1_missed_without_common_normal_neighbor():
    g = undirected(6, BASE)
    atk = {4: TamperInbox(at=5, src=5, dy=6.0), 5: Offset(at=10**9)}
    d = Algorithm2()
    res = simulate(g, X6, atk, d, steps=400)
    assert d.log == []                           # attack is invisible
    # everyone converges to the all-node average plus exactly the injected mass dy
    corrupted = (sum(X6) + 6.0) / 6
    assert res.max_error(target=corrupted) < 1e-9
    assert abs(corrupted - (2 + 9 + 4 + 7) / 4) > 0.1


# ---- randomized: no false positives, every attacker caught, exact average ------------
ATTACKS = [lambda at, r: Offset(at, r.uniform(-6, 6)), lambda at, r: Crash(at),
           lambda at, r: Frozen(at), lambda at, r: RandomLie(at, 3.0, r.randrange(99)),
           lambda at, r: Offset(at, 0.0, r.uniform(0.1, 0.5))]


@pytest.mark.parametrize("seed", range(25))
def test_random_graphs(seed):
    rng = random.Random(seed)
    n = rng.randrange(7, 13)
    while True:
        E = {tuple(sorted(rng.sample(range(n), 2))) for _ in range(n * 2)}
        E |= {(i, i + 1) for i in range(n - 1)}
        g = undirected(n, E)
        bad = rng.sample(range(n), 2)
        if not any(b in g.in_nbrs[c] for b in bad for c in bad) and \
                g.is_strongly_connected([v for v in range(n) if v not in bad]):
            break
    x = [rng.uniform(-10, 10) for _ in range(n)]
    atk = {b: rng.choice(ATTACKS)(rng.randrange(1, 15), rng) for b in bad}
    d = Algorithm2()
    res = simulate(g, x, atk, d, steps=2000)
    assert_no_false_positives(res, atk)
    assert res.flagged_by_normals() == set(bad)
    assert res.max_error() < 1e-6, res.max_error()
