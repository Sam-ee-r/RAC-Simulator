"""Reproduction of every numerical example in Section VI of the paper, on the graphs read off
its figures (rac_sim/paper.py)."""
import pytest

from rac_sim import simulate, Algorithm2, Algorithm3, satisfies_assumption4
from rac_sim import paper


def run(exp, det, steps):
    g, x, atk, expected = exp
    d = det()
    res = simulate(g, x, atk, d, steps=steps)
    normal_flags = [e for e in d.log if e[1] in res.normal]
    return res, d, normal_flags, atk, expected


@pytest.mark.parametrize("g", [paper.fig5b(), paper.fig4b(), paper.fig11()])
def test_paper_graphs_satisfy_assumption4(g):
    assert satisfies_assumption4(g, 1)            # as the paper states for these graphs


def test_less_edges_graph_violates_assumption4():
    assert not satisfies_assumption4(paper.fig5b(((1, 4), (2, 5), (3, 6))), 1)


def test_fig10_alg2_5node():
    res, d, flags, atk, exp = run(paper.exp_alg2_fig5a(), Algorithm2, 300)
    assert res.r[12, [0, 1, 2, 3]] == pytest.approx(4.5, abs=1e-3)   # "at k=13 ... almost 4.5"
    assert res.flagged_by_normals() == {3, 4}
    assert res.max_error(target=exp) < 1e-9


def test_fig6b_alg3_6node():
    res, d, flags, atk, exp = run(paper.exp_alg3_fig5b(), lambda: Algorithm3(f=1), 300)
    assert {(k, i) for k, i, j, _ in flags if j == 5 and k == 4} == {(4, 0), (4, 1), (4, 2), (4, 3)}
    assert {j for *_, j, _ in flags} == {5}
    assert res.max_error(target=exp) < 1e-9


def test_fig6a_less_edges_fails_without_false_flags():
    res, d, flags, atk, exp = run(paper.exp_alg3_fig5b(less_edges=True),
                                  lambda: Algorithm3(f=1), 300)
    assert {i for _, i, j, _ in flags if j == 5} == {1, 3}        # "only nodes 2 and 4"
    assert {j for *_, j, _ in flags} == {5}                       # no honest node flagged
    assert res.max_error(target=exp) > 0.1                        # RAC not achieved


def test_fig7_alg3_14node():
    g, x, atk, exp = paper.exp_alg3_fig4b()
    clean = simulate(g, x, detector=Algorithm3(f=1), steps=300)
    assert clean.max_error(target=6.5) < 1e-9                     # no-attack average
    res, d, flags, atk, exp = run(paper.exp_alg3_fig4b(), lambda: Algorithm3(f=1), 600)
    assert res.r[10, res.normal] == pytest.approx(6.385, abs=5e-3)  # "around 6.385"
    assert {(k, j) for k, _, j, _ in flags} == {(5, 13), (12, 1)}  # each caught 1 step later
    assert res.max_error(target=exp) < 1e-9


def test_fig9_alg3_8node_five_attackers():
    res, d, flags, atk, exp = run(paper.exp_alg3_fig8(), lambda: Algorithm3(f=1), 400)
    assert {j for *_, j, _ in flags} == set(atk)
    assert res.max_error(target=exp) < 1e-9


@pytest.mark.slow
def test_fig12_alg3_30node():
    g, x, atk, exp = paper.exp_alg3_fig11()
    clean = simulate(g, x, detector=Algorithm3(f=1), steps=3000)
    assert clean.max_error(target=6.8) < 1e-6
    res, d, flags, atk, exp = run(paper.exp_alg3_fig11(), lambda: Algorithm3(f=1), 3000)
    assert {j for *_, j, _ in flags} == set(atk)
    assert min(k for k, *_ in flags) == 10
    assert exp == pytest.approx(6.4166, abs=1e-4)
    assert res.max_error(target=exp) < 1e-6
