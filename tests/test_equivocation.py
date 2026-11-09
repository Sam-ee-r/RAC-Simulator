"""Per-recipient messaging + Byzantine equivocation experiments (outside the paper's broadcast threat model)."""
import sys, os
import numpy as np
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "experiments"))
from rac_sim import paper, simulate, Algorithm3, Offset, Equivocate
from equiv_lib import run, classify

G = paper.fig5b()
X = [9, 7, 1, 3, 4, 6]
ATT = 5                      # node 6
OUTS = list(G.out_nbrs[ATT])


def test_equivocate_to_all_equals_broadcast_offset():
    a = simulate(G, X, {ATT: Offset(3, 4.0, 0.0)}, Algorithm3(f=1), steps=120)
    b = simulate(G, X, {ATT: Equivocate(3, {v: 4.0 for v in OUTS})}, Algorithm3(f=1), steps=120)
    assert np.allclose(a.r, b.r, equal_nan=True)


def test_non_victim_receives_untouched_message():
    res, d = run(G, X, ATT, (OUTS[0],), steps=40)
    assert res is not None  # sanity: runs; detailed content checked below
    atk = Equivocate(3, {OUTS[0]: 4.0})
    from rac_sim import Phi
    m = Phi(A=frozenset(), own_next=(1.0, 1.0), seen={})
    assert atk.transform_to(m, 3, OUTS[0]).own_next == (5.0, 1.0)
    assert atk.transform_to(m, 3, OUTS[1]) is m
    assert atk.transform_to(m, 4, OUTS[0]) is m


def test_broadcast_to_all_out_neighbours_is_handled():
    res, d = run(G, X, ATT, tuple(OUTS))
    assert classify(res, d, ATT) == "CORRECT"


@pytest.mark.parametrize("victim", OUTS)
def test_single_victim_equivocation_causes_false_flag(victim):
    res, d = run(G, X, ATT, (victim,))
    assert classify(res, d, ATT) == "FALSE_FLAG"


@pytest.mark.parametrize("grace", [0, 3, 10])
def test_false_flag_not_an_artifact_of_grace(grace):
    res, d = run(G, X, ATT, (OUTS[0],), grace=grace)
    assert classify(res, d, ATT) == "FALSE_FLAG"


def test_without_claim_checks_failure_is_silent_wrong_average():
    res, d = run(G, X, ATT, (OUTS[0],), claims=False)
    assert classify(res, d, ATT) == "WRONG_AVG"
