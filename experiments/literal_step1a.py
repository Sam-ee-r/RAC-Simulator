"""Does the equivocation failure survive a LITERAL reading of Algorithm 3's Step 1a?

  python experiments/literal_step1a.py            # sanity check + Fig 5b equivocation table (about 1 min)
  python experiments/literal_step1a.py --sweep    # also every (attacker, victim) pair on 8 graphs (several min)
  python experiments/literal_step1a.py --two-sided  # literal 1a that also flags omissions

Part A (gate): in literal mode the paper's own broadcast-attack experiments must still end on the
right average with no honest node flagged. If they do not, the literal reading is wrong, not the paper.
Part B: node 6 of the paper's Fig 5b graph lies to ONE or TWO of its out-neighbours, under
'ours' (grace=1, claim checks) and 'literal' (Step 1a as printed).
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from collections import Counter
import numpy as np
from rac_sim import paper, simulate, Algorithm3
from equiv_lib import run, classify, subsets

TWO = "--two-sided" in sys.argv
MODES = {"ours (grace=1)": dict(), "literal 1a": dict(claim_mode="literal", two_sided=TWO)}


def part_a():
    print("PART A: the paper's own (broadcast) attacks, literal Step 1a must still work\n")
    print(f"{'experiment':34s}{'expected':>9s}{'final (normal nodes)':>24s}{'honest flagged':>16s}{'verdict':>9s}")
    for name, fn, steps in [("Fig 5b, 6 nodes", paper.exp_alg3_fig5b, 60), ("Fig 4b, 14 nodes", paper.exp_alg3_fig4b, 80),
                            ("Fig 8, 8 nodes, 5 attackers", paper.exp_alg3_fig8, 60)]:
        g, x, adv, exp = fn()
        d = Algorithm3(f=1, **MODES["literal 1a"])
        res = simulate(g, x, adv, d, steps=steps)
        fin = res.r[-1, res.normal]
        bad = sorted({(i + 1, j + 1) for k, i, j, w in d.log if i in res.normal and j in res.normal})
        ok = (not bad) and not np.isnan(fin).any() and abs(fin - exp).max() < 1e-6
        print(f"{name:34s}{exp:9.4g}{f'{fin.min():.4g} .. {fin.max():.4g}':>24s}{len(bad):16d}{'OK' if ok else 'FAIL':>9s}")


def part_b(g, x, att, label):
    outs = list(g.out_nbrs[att]); rows = []
    for vic in [s for s in subsets(outs) if len(s) <= 2]:
        row = [label, tuple(v + 1 for v in vic)]
        for mname, kw in MODES.items():
            res, d = run(g, x, att, vic, steps=250, **kw)
            row.append(classify(res, d, att))
        rows.append(row)
    return rows


if __name__ == "__main__":
    part_a()
    print("\nPART B: node 6 of Fig 5b lies (+4 at k=3) to some of its out-neighbours only\n")
    g, x = paper.fig5b(), [9, 7, 1, 3, 4, 6]
    rows = part_b(g, x, 5, "fig5b")
    print(f"{'victims':14s}" + "".join(f"{m:>18s}" for m in MODES))
    for r in rows:
        print(f"{str(r[1]):14s}" + "".join(f"{o:>18s}" for o in r[2:]))
    for i, m in enumerate(MODES):
        print(f"  {m:16s}", dict(Counter(r[2 + i] for r in rows)))

    if "--sweep" in sys.argv:
        from equiv_sweep import build_graphs
        print("\nSWEEP: every (attacker, single victim) pair on 8 graphs")
        tot = {m: Counter() for m in MODES}
        for name, gg, xx in build_graphs(random.Random(11)):
            for att in range(gg.n):
                if len(gg.out_nbrs[att]) < 2: continue
                for v in gg.out_nbrs[att]:
                    for m, kw in MODES.items():
                        res, d = run(gg, xx, att, (v,), steps=250, **kw)
                        tot[m][classify(res, d, att)] += 1
        for m, c in tot.items():
            print(f"  {m:16s} runs={sum(c.values())}", dict(c))
