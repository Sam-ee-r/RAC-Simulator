"""Algorithm 2 demo -> demo_alg2.png
 1. Paper 5-node scenario: node 5 attacks at k=4, node 4 at k=13. Both caught, average 5.
 2. Lemma 1, caught: colluding neighbors 5 & 6 share a normal neighbor (node 1).
 3. Lemma 1, missed: no normal common neighbor -> invisible attack, wrong average."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from rac_sim import undirected, simulate, Algorithm2, Offset, TamperInbox

E5 = [(u, v) for u in range(1, 6) for v in range(u + 1, 6) if (u, v) != (1, 2)]
BASE = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (4, 0), (4, 1), (5, 2), (5, 3), (4, 5)]
X6 = [2, 9, 4, 7, 5, 1]
collude = lambda: {4: TamperInbox(at=5, src=5, dy=6.0), 5: Offset(at=10**9)}

cases = [
    ("Paper 5-node: attacks at k=4, k=13", undirected(5, E5, one_indexed=True), [8, 6, 1, 3, 9],
     {4: Offset(at=4, dy=5.0), 3: Offset(at=13, dy=-3.0)}, 5.0),
    ("Colluding pair, common normal neighbor", undirected(6, BASE + [(0, 5)]), X6, collude(), 23 / 5),
    ("Colluding pair, NO common neighbor", undirected(6, BASE), X6, collude(), 22 / 4),
]

fig, axes = plt.subplots(1, 3, figsize=(14, 3.8))
for ax, (title, g, x, atk, target) in zip(axes, cases):
    d = Algorithm2()
    res = simulate(g, x, atk, d, steps=40)
    for i in res.normal:
        ax.plot(res.r[:, i], lw=1.4, label=f"node {i + 1}")
    ax.axhline(target, color="k", ls="--", lw=1, label=f"correct avg {target:.2f}")
    for j in sorted(res.flagged_by_normals()):
        k = res.first_detection(j)
        ax.axvline(k, color="red", lw=0.8, alpha=0.6)
        ax.text(k + 0.4, ax.get_ylim()[1] * 0.97, f"node {j + 1} caught", color="red",
                fontsize=7, va="top")
    if not d.log:
        ax.text(0.98, 0.04, "no detection", transform=ax.transAxes, ha="right", color="red")
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("k")
    ax.legend(fontsize=6.5, loc="upper right" if d.log else "lower left")
axes[0].set_ylabel("r_i[k]")
fig.tight_layout()
fig.savefig("demo_alg2.png", dpi=150)
print("wrote demo_alg2.png")
