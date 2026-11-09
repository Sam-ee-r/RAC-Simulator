"""Demo: 6-node run, node 6 attacks at k=2. Compares no defence vs detection+recovery.
Usage: python run_demo.py   -> writes demo.png"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from rac_sim import circulant, simulate, NoDetector, OracleDetector, Offset

X = [9, 7, 1, 3, 4, 6]
g = circulant(6, (1, 2))           # placeholder topology, see tests/test_alg1.py
attacks = {5: Offset(at=2, dy=5.0)}

runs = {
    "No attack": simulate(g, X, steps=60),
    "Attack, no defence": simulate(g, X, attacks, NoDetector(), steps=60),
    "Attack, detection + recovery": simulate(g, X, attacks, OracleDetector(attacks), steps=60),
}

fig, axes = plt.subplots(1, 3, figsize=(13, 3.6), sharey=True)
for ax, (title, res) in zip(axes, runs.items()):
    for i in res.normal:
        ax.plot(res.r[:, i], lw=1.4, label=f"node {i + 1}")
    ax.axhline(res.target, color="k", ls="--", lw=1, label=f"target {res.target:.2f}")
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("k")
axes[0].set_ylabel("r_i[k] = y/z")
axes[0].legend(fontsize=7, ncol=2)
fig.tight_layout()
fig.savefig("demo.png", dpi=150)
print("wrote demo.png")
