"""Demo: the same lie (+4 at k=3) sent to all out-neighbours of node 6 vs only to node 1.  -> demo_equivocation.png"""
import sys, os
sys.path.insert(0, "experiments")
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rac_sim import paper
from equiv_lib import run, classify

G, X, ATT = paper.fig5b(), [9, 7, 1, 3, 4, 6], 5
OUTS = list(G.out_nbrs[ATT])
cases = [("Same lie to all 4 out-neighbours (paper's model)", tuple(OUTS), {}),
         ("Lie to node 1 only (equivocation)", (OUTS[0],), {}),
         ("Lie to node 1 only, claim checks disabled", (OUTS[0],), dict(claims=False))]
fig, axs = plt.subplots(1, 3, figsize=(15, 4.2), sharey=True)
for ax, (title, vic, kw) in zip(axs, cases):
    res, d = run(G, X, ATT, vic, steps=120, **kw)
    out = classify(res, d, ATT)
    for i in res.normal:
        ax.plot(res.r[:, i], lw=1.6, label=f"node {i + 1}")
    ax.axhline(res.target, color="k", ls="--", lw=1)
    ax.set_title(f"{title}\n-> {out}", fontsize=10)
    ax.set_xlabel("step k")
    hf = sorted({(i + 1, j + 1) for k, i, j, w in d.log if i in res.normal and j in res.normal})
    if hf: ax.text(0.03, 0.04, "honest->honest flags:\n" + ", ".join(f"{a}->{b}" for a, b in hf[:6]), transform=ax.transAxes, fontsize=8)
axs[0].set_ylabel("estimate r_i = y/z"); axs[0].legend(fontsize=7, ncol=2)
axs[0].set_ylim(0, 10)
plt.tight_layout(); plt.savefig("demo_equivocation.png", dpi=130)
for t, v, kw in cases:
    res, d = run(G, X, ATT, v, steps=120, **kw); print(t, "->", classify(res, d, ATT))
