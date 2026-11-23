"""Step 1a read literally (no grace, no can_verify, judged after this step's vote)."""
import sys, os
import numpy as np
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "experiments"))
from rac_sim import paper, simulate, Algorithm3
from equiv_lib import run, classify

LIT = dict(claim_mode="literal")


@pytest.mark.parametrize("fn,steps", [(paper.exp_alg3_fig5b, 60), (paper.exp_alg3_fig4b, 80), (paper.exp_alg3_fig8, 60)])
def test_literal_reading_still_reproduces_paper_broadcast_attacks(fn, steps):
    g, x, adv, expected = fn()
    d = Algorithm3(f=1, **LIT)
    res = simulate(g, x, adv, d, steps=steps)
    assert not {(i, j) for k, i, j, w in d.log if i in res.normal and j in res.normal}
    assert np.allclose(res.r[-1, res.normal], expected, atol=1e-6)


@pytest.mark.parametrize("victim", [0, 1, 2, 3])
def test_equivocation_to_one_neighbour_still_falsely_flags_under_literal_1a(victim):
    g = paper.fig5b()
    res, d = run(g, [9, 7, 1, 3, 4, 6], 5, (victim,), steps=120, **LIT)
    assert classify(res, d, 5) == "FALSE_FLAG"
    honest = sorted((k, w) for k, i, j, w in d.log if i in res.normal and j in res.normal)
    assert honest[0][1] == "1a-literal"       # the first false flag is Step 1a; later ones can follow by vote
