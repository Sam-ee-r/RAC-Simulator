"""Sweep: one equivocating attacker, misbehaving toward a subset of its out-neighbours.
Usage: python experiments/equiv_sweep.py  -> experiments/equiv_results.json + printed table"""
import json, random, sys, time, os
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from collections import Counter, defaultdict
from rac_sim import Digraph, paper, satisfies_assumption4
from equiv_lib import run, classify, subsets


def random_a4(rng, n, p, f=1):
    while True:
        E = [(u, v) for u in range(n) for v in range(n) if u != v and rng.random() < p]
        g = Digraph(n, E)
        if g.is_strongly_connected() and satisfies_assumption4(g, f) and len(g.edges) < n * (n - 1) \
                and any(g.two_hop_in(i) for i in range(n)):
            return g


def build_graphs(rng, n_random=6):
    graphs = [("paper fig5b (6 nodes)", paper.fig5b(), [9, 7, 1, 3, 4, 6]),
              ("paper fig4b (14 nodes)", paper.fig4b(), [11, 2, 9, 3, 2, 10, 1, 4, 6, 9, 7, 5, 14, 8])]
    for t in range(n_random):
        n = rng.choice([7, 8, 9, 10]); g = random_a4(rng, n, {7: .7, 8: .65, 9: .62, 10: .6}[n])
        graphs.append((f"random A4 #{t + 1} ({n} nodes)", g, [rng.uniform(-10, 10) for _ in range(n)]))
    return graphs


def main(seed=11, n_random=6, per_attacker=14):
    rng = random.Random(seed)
    graphs = build_graphs(rng, n_random)
    rows, t0 = [], time.time()
    for name, g, x in graphs:
        cands = [m for m in range(g.n) if len(g.out_nbrs[m]) >= 2]
        for m in rng.sample(cands, min(3, len(cands))):
            outs = g.out_nbrs[m]
            allsub = list(subsets(outs))
            pick = [s for s in allsub if len(s) == 1] + rng.sample(
                [s for s in allsub if len(s) > 1], min(per_attacker - len(outs), max(0, len(allsub) - len(outs))))
            for vic in pick:
                res, d = run(g, x, m, vic, steps=250)
                rows.append(dict(graph=name, attacker=m, outs=len(outs), victims=list(vic),
                                 nv=len(vic), all_out=len(vic) == len(outs), outcome=classify(res, d, m)))
        print(f"{name}: done ({time.time() - t0:.0f}s)", flush=True)
    json.dump(rows, open(os.path.join(os.path.dirname(__file__), "equiv_results.json"), "w"))
    return rows


def table(rows):
    by = defaultdict(Counter)
    for r in rows:
        key = "all out-neighbours (= broadcast)" if r["all_out"] else (
            "1 victim" if r["nv"] == 1 else "2 victims" if r["nv"] == 2 else "3+ victims (not all)")
        by[key][r["outcome"]] += 1
    order = ["1 victim", "2 victims", "3+ victims (not all)", "all out-neighbours (= broadcast)"]
    print(f"\n{'victim set':34s} {'runs':>5s} {'CORRECT':>8s} {'FALSE_FLAG':>11s} {'WRONG_AVG':>10s} {'NO_CONS':>8s}")
    for k in order:
        c = by.get(k, Counter()); n = sum(c.values())
        if n: print(f"{k:34s} {n:5d} {c['CORRECT']:8d} {c['FALSE_FLAG']:11d} {c['WRONG_AVG']:10d} {c['NO_CONSENSUS']:8d}")


if __name__ == "__main__":
    table(main())
