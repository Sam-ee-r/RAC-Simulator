"""Graphs and experiments from Yuan & Ishii (arXiv:2405.18752), read off the figures in the PDF.

Node numbers in comments follow the paper (1-indexed); the Digraphs are 0-indexed.
Each scenario returns (graph, x0, adversaries, expected average of the normal nodes).
Attack timings follow Section VI. Where the paper says only "manipulates its values" the exact
manipulation is our choice; the expected averages do not depend on it.
"""
from __future__ import annotations

from .attacks import Frozen, Offset, RandomLie, TamperInbox
from .graph import Digraph, undirected


def fig5a() -> Digraph:
    """5-node wheel: hub 1, rim 2-3-4-5. Undirected. Used for Algorithm 2."""
    return undirected(5, [(1, 2), (1, 3), (1, 4), (1, 5), (2, 3), (3, 4), (4, 5), (5, 2)],
                      one_indexed=True)


FIG5B_RING = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1)]
FIG5B_CHORDS = [(1, 3), (1, 4), (1, 5), (2, 4), (2, 5), (2, 6), (3, 5), (3, 6), (4, 6)]


def fig5b(remove=()) -> Digraph:
    """6-node directed: directed ring 1->2->...->6->1 plus 9 undirected chords.
    remove=((1,4),(2,5),(3,6)) gives the 'less edges' graph of Fig. 6(a)."""
    ch = [c for c in FIG5B_CHORDS if c not in set(remove)]
    return Digraph.from_one_indexed(6, FIG5B_RING + ch + [(v, u) for u, v in ch])


def fig4b() -> Digraph:
    """14-node five-layer directed graph. Layers {1,2,3},{4,5,6},{7,8,9} undirected
    complete-bipartite between neighbours; {7,8,9} <-> {12,13,14} undirected;
    {12,13,14} -> {10,11}; {10,11} -> {7,8,9}; 10 <-> 11."""
    L = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    und = [(a, b) for c in range(2) for a in L[c] for b in L[c + 1]]
    und += [(a, b) for a in (7, 8, 9) for b in (12, 13, 14)] + [(10, 11)]
    dire = [(a, b) for a in (12, 13, 14) for b in (10, 11)]
    dire += [(a, b) for a in (10, 11) for b in (7, 8, 9)]
    return Digraph.from_one_indexed(14, und + [(b, a) for a, b in und] + dire)


def fig8() -> Digraph:
    """8 nodes: complete except node 2 -> {4,5,6,7} are one-way."""
    E = [(u, v) for u in range(1, 9) for v in range(1, 9)
         if u != v and not (v == 2 and u in (4, 5, 6, 7))]
    return Digraph.from_one_indexed(8, E)


def fig11(columns=10) -> Digraph:
    """Layered construction of Sec. V-D with f=1: columns of 3 nodes (column c holds nodes
    3c+1..3c+3), each node linked both ways to every node in the neighbouring columns."""
    E = [(3 * c + a + 1, 3 * (c + 1) + b + 1)
         for c in range(columns - 1) for a in range(3) for b in range(3)]
    return undirected(3 * columns, E, one_indexed=True)


# ---- Section VI experiments --------------------------------------------------------
def exp_alg2_fig5a():
    """Fig. 10: node 5 sends arbitrary values at k=4, node 4 manipulates its own value at k=13."""
    return fig5a(), [8, 6, 1, 3, 9], {4: RandomLie(4, 5.0, seed=3), 3: Offset(13, -3.0)}, 5.0


def exp_alg3_fig5b(less_edges=False):
    """Fig. 6: node 6 follows the protocol until k=2, then changes the past values of node 2
    in its information set. With less edges the paper reports failure."""
    g = fig5b(((1, 4), (2, 5), (3, 6)) if less_edges else ())
    return g, [9, 7, 1, 3, 4, 6], {5: TamperInbox(3, 1, 5.0)}, 4.8


def exp_alg3_fig4b():
    """Fig. 7: after k=3 node 14 holds a fixed value; at k=11 node 2 changes the past values
    of an in-neighbour (node 4). Paper: ~6.385 at k=11, final 6.75."""
    return fig4b(), [11, 2, 9, 3, 2, 10, 1, 4, 6, 9, 7, 5, 14, 8], \
        {13: Frozen(4), 1: TamperInbox(11, 3, 4.0)}, 6.75


def exp_alg3_fig8():
    """Fig. 9: nodes 3-7 all attack at k=3 with arbitrary values. Paper: final 10."""
    atk = {2: Offset(3, 6.0), 3: RandomLie(3, 4.0, seed=1), 4: Frozen(3),
           5: Offset(3, -5.0, 0.4), 6: RandomLie(3, 3.0, seed=2)}
    return fig8(), [3, 15, 9, 8, 4, 7, 1, 12], atk, 10.0


FIG11_X0 = [8, 7, 5, 3, 2, 11, 1, 4, 6, 9, 10, 12, 11, 13, 14, 3, 5, 2, 8, 7, 5, 3, 2, 11,
            1, 4, 6, 9, 10, 12]


def exp_alg3_fig11():
    """Fig. 12: from k=9 the malicious neighbour pairs (3,6), (15,18), (27,30) each change the
    past values of their partner. Paper: no attack 6.8, with attack 6.4166."""
    atk = {}
    for a, b in [(3, 6), (15, 18), (27, 30)]:
        atk[a - 1] = TamperInbox(9, b - 1, 4.0)
        atk[b - 1] = TamperInbox(9, a - 1, -3.0)
    return fig11(), FIG11_X0, atk, 77 / 12
