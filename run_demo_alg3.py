"""Algorithm 3 demo -> demo_alg3.png
Directed 1-local graph satisfying Assumption 4. Node m injects mass at k=3, its out-neighbor c
conceals m (keeps relaying the bad mass and never reports m as detected).
 1. no detection        -> wrong average
 2. Alg 3 with grace=0  -> honest nodes wrongly flagged ('second time' read too strictly)
 3. Alg 3, grace=1      -> both colluders caught, exact average of the normal nodes"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from rac_sim import Digraph, simulate, Algorithm3, NoDetector, Offset, Conceal

case = json.load(open("tests/data/flocal_collusion_graphs.json"))[0]
g, m, c = Digraph(case["n"], case["edges"]), case["m"], case["c"]
x = [((7 * v) % 11) - 3.0 for v in range(g.n)]
atk = lambda: {m: Offset(3, 4.0), c: Conceal({m})}

runs = [("No detection", NoDetector()),
        ("Alg 3, no grace period", Algorithm3(f=1, grace=0)),
        ("Alg 3, one-step grace", Algorithm3(f=1, grace=1))]

fig, axes = plt.subplots(1, 3, figsize=(14, 3.8), sharey=True)
for ax, (title, det) in zip(axes, runs):
    res = simulate(g, x, atk(), det, steps=40)
    for i in res.normal:
        ax.plot(res.r[:, i], lw=1.1)
    ax.axhline(res.target, color="k", ls="--", lw=1, label=f"correct avg {res.target:.2f}")
    flagged = res.flagged_by_normals()
    wrong = sorted(flagged - {m, c})
    note = f"caught: {sorted(v + 1 for v in flagged & {m, c})}"
    if wrong:
        note += f"\nhonest flagged: {[v + 1 for v in wrong]}"
    ax.text(0.98, 0.04, note, transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
            color="red" if wrong or not flagged else "green")
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("k")
    ax.legend(fontsize=7, loc="upper right")
axes[0].set_ylabel("r_i[k] (normal nodes)")
fig.suptitle(f"Directed {g.n}-node graph: node {m + 1} injects at k=3, node {c + 1} conceals it",
             fontsize=10)
fig.tight_layout()
fig.savefig("demo_alg3.png", dpi=150)
print("wrote demo_alg3.png")
