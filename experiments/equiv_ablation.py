"""Interpretation sensitivity: single-victim equivocation on every sweep graph, under Alg-3 variants."""
import os, sys, random
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from collections import Counter
from equiv_lib import run, classify
from equiv_sweep import build_graphs

VARIANTS = {"grace=0": dict(grace=0), "grace=1 (default)": dict(grace=1), "grace=3": dict(grace=3),
            "grace=10": dict(grace=10), "no claim checks": dict(claims=False)}

def main():
    graphs = build_graphs(random.Random(11))
    out = {v: Counter() for v in VARIANTS}
    for name, g, x in graphs:
        for m in range(g.n):
            for v in g.out_nbrs[m]:
                if len(g.out_nbrs[m]) < 2: continue
                for label, kw in VARIANTS.items():
                    res, d = run(g, x, m, (v,), steps=250, **kw)
                    out[label][classify(res, d, m)] += 1
    print(f"{'variant':20s} {'runs':>5s} {'CORRECT':>8s} {'FALSE_FLAG':>11s} {'WRONG_AVG':>10s} {'NO_CONS':>8s}")
    for label, c in out.items():
        print(f"{label:20s} {sum(c.values()):5d} {c['CORRECT']:8d} {c['FALSE_FLAG']:11d} {c['WRONG_AVG']:10d} {c['NO_CONSENSUS']:8d}")

if __name__ == "__main__":
    main()
