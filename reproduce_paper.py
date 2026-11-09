"""Re-creates the paper's Section VI result figures with rac_sim -> paper_reproduction.png"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from rac_sim import simulate, Algorithm2, Algorithm3, paper

runs = [
    ("Fig. 6(a): 6-node, less edges (should fail)", paper.exp_alg3_fig5b(True), Algorithm3, 20),
    ("Fig. 6(b): 6-node, Alg 3", paper.exp_alg3_fig5b(), Algorithm3, 20),
    ("Fig. 7(b): 14-node, Alg 3", paper.exp_alg3_fig4b(), Algorithm3, 30),
    ("Fig. 9: 8-node, 5 attackers, Alg 3", paper.exp_alg3_fig8(), Algorithm3, 20),
    ("Fig. 10: 5-node, Alg 2", paper.exp_alg2_fig5a(), Algorithm2, 30),
    ("Fig. 12(b): 30-node, Alg 3", paper.exp_alg3_fig11(), Algorithm3, 400),
]

fig, axes = plt.subplots(2, 3, figsize=(15, 7.5))
for ax, (title, (g, x, atk, exp), Det, steps) in zip(axes.flat, runs):
    det = Det(f=1) if Det is Algorithm3 else Det()
    res = simulate(g, x, atk, det, steps=steps)
    for i in range(g.n):
        bad = i in atk
        ax.plot(res.r[:, i], color="red" if bad else None, lw=1.6 if bad else 1.0,
                alpha=0.8 if bad else 0.9)
    ax.axhline(exp, color="k", ls="--", lw=1)
    final = res.r[-1, res.normal]
    ax.set_title(f"{title}\nexpected {exp:.4g}, normal nodes end at "
                 f"{final.min():.4g}" + ("" if abs(final.max() - final.min()) < 1e-6
                                          else f"-{final.max():.4g}"), fontsize=9)
    ax.set_xlabel("k")
    lo, hi = min(x) - 2, max(x) + 2
    ax.set_ylim(lo, hi)
axes[0, 0].set_ylabel("r_i[k]")
axes[1, 0].set_ylabel("r_i[k]")
fig.suptitle("rac_sim reproduction of Yuan & Ishii, Section VI (red = malicious nodes)", fontsize=11)
fig.tight_layout()
fig.savefig("paper_reproduction.png", dpi=140)
print("wrote paper_reproduction.png")
