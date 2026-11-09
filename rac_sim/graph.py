"""Directed graph utilities. Nodes are 0-indexed; edge (j, i) means j -> i (i receives from j)."""
from __future__ import annotations


class Digraph:
    def __init__(self, n: int, edges):
        self.n = n
        self.edges = sorted(set((int(j), int(i)) for j, i in edges if j != i))
        self.out_nbrs = [[] for _ in range(n)]
        self.in_nbrs = [[] for _ in range(n)]
        for j, i in self.edges:
            self.out_nbrs[j].append(i)
            self.in_nbrs[i].append(j)

    def two_hop_in(self, i: int) -> set[int]:
        """N_i^{2-}: in-neighbors of in-neighbors, excluding i and its direct in-neighbors."""
        direct = set(self.in_nbrs[i])
        two = set()
        for j in direct:
            two.update(self.in_nbrs[j])
        return two - direct - {i}

    def is_strongly_connected(self, nodes=None) -> bool:
        """Strong connectivity of the subgraph induced on `nodes` (default: all)."""
        nodes = set(range(self.n)) if nodes is None else set(nodes)
        if len(nodes) <= 1:
            return True
        start = next(iter(nodes))
        return self._reach(start, nodes, self.out_nbrs) == nodes and \
            self._reach(start, nodes, self.in_nbrs) == nodes

    @staticmethod
    def _reach(start, nodes, adj):
        seen, stack = {start}, [start]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v in nodes and v not in seen:
                    seen.add(v)
                    stack.append(v)
        return seen

    @classmethod
    def from_one_indexed(cls, n: int, edges):
        """Convenience for copying edge lists from the paper, which uses 1-indexed nodes."""
        return cls(n, [(j - 1, i - 1) for j, i in edges])


def circulant(n: int, offsets=(1, 2)) -> Digraph:
    """Edge i -> (i + o) mod n for each offset. Offsets (1, 2) give in/out-degree 2."""
    return Digraph(n, [(i, (i + o) % n) for i in range(n) for o in offsets])


def detectable(g: Digraph, h: int, i: int, f: int) -> bool:
    """Paper Def. 3: h is detectable by i if h is an in-neighbor of i, or there are at least
    2f+1 two-hop paths h -> j -> i (distinct middle nodes j)."""
    if h in g.in_nbrs[i]:
        return True
    return len(set(g.in_nbrs[i]) & set(g.out_nbrs[h])) >= 2 * f + 1


def assumption4_violations(g: Digraph, f: int) -> list:
    """Paper Assumption 4. Returns [(i, h, why)] for every node h that i must be able to judge
    but cannot. Empty list means the graph satisfies Assumption 4."""
    bad = []
    for i in range(g.n):
        need = {h: "two-hop in-neighbor" for h in g.two_hop_in(i)}
        need.update({q: "out-neighbor" for q in g.out_nbrs[i]})
        for j in g.in_nbrs[i]:
            for l in g.out_nbrs[j]:
                need.setdefault(l, f"out-neighbor of in-neighbor {j}")
        need.pop(i, None)
        bad += [(i, h, why) for h, why in need.items() if not detectable(g, h, i, f)]
    return bad


def satisfies_assumption4(g: Digraph, f: int) -> bool:
    return not assumption4_violations(g, f)


def undirected(n: int, edges, one_indexed=False) -> Digraph:
    """Each undirected edge {u, v} becomes the two directed edges u->v and v->u."""
    off = 1 if one_indexed else 0
    pairs = [(u - off, v - off) for u, v in edges]
    return Digraph(n, pairs + [(v, u) for u, v in pairs])


def bidirectional_ring(n: int) -> Digraph:
    return Digraph(n, [(i, (i + 1) % n) for i in range(n)] + [((i + 1) % n, i) for i in range(n)])
