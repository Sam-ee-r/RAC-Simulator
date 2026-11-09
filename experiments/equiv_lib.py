"""Shared helpers for the equivocation experiments."""
import itertools
import numpy as np
from rac_sim import simulate, Algorithm3, Equivocate


def classify(res, d, attacker, tol=1e-6):
    """Outcome of one run.
    FALSE_FLAG : some normal node flagged another normal node
    WRONG_AVG  : nobody honest flagged, but normal nodes did not reach the normal-node average
    NO_CONSENSUS: normal estimates disagree or are NaN
    CORRECT    : exact average of the normal nodes' initial values, no honest node flagged
    """
    honest_flags = {(i, j) for k, i, j, why in d.log if i in res.normal and j in res.normal}
    final = res.r[-1, res.normal]
    if honest_flags:
        return "FALSE_FLAG"
    if np.isnan(final).any() or final.max() - final.min() > tol:
        return "NO_CONSENSUS"
    if abs(final[0] - res.target) > tol:
        return "WRONG_AVG"
    return "CORRECT"


def run(g, x, attacker, victims, at=3, dy=4.0, repeat=False, steps=400, f=1, **kw):
    atk = {attacker: Equivocate(at, {v: dy for v in victims}, repeat=repeat)}
    d = Algorithm3(f=f, **kw)
    res = simulate(g, x, atk, d, steps=steps)
    return res, d


def subsets(nodes):
    for r in range(1, len(nodes) + 1):
        for c in itertools.combinations(nodes, r):
            yield c
