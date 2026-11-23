"""Redraw of the paper's Fig. 5(a) and 5(b) networks from rac_sim/paper.py -> fig5_networks.png
Usage: python draw_fig5.py"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
from rac_sim import paper

BLUE, RED, GREY = "#3B6FD8", "#D9483B", "#9AA3AF"
RING, CHORDS = paper.FIG5B_RING, paper.FIG5B_CHORDS


def node(ax, p, i, att, val):
    ax.add_patch(Circle(p, 0.2, fc="#FBE4E1" if att else "#E4ECFB", ec=RED if att else BLUE, lw=3, zorder=3))
    ax.text(p[0], p[1] + 0.04, str(i), ha="center", va="center", fontsize=17, fontweight="bold", zorder=4)
    ax.text(p[0], p[1] - 0.1, f"({val})", ha="center", va="center", fontsize=9.5, color="#555", zorder=4)


def edge(ax, a, b, arrow=False, col=GREY, lw=2.2, rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>" if arrow else "-", mutation_scale=18,
                                 connectionstyle=f"arc3,rad={rad}", color=col, lw=lw, shrinkA=19, shrinkB=19, zorder=1))


fig, (A, B) = plt.subplots(1, 2, figsize=(14, 7.2))
for ax in (A, B):
    ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-1.9, 1.9); ax.set_ylim(-2.25, 1.75)

# ---- Fig 5(a): wheel, hub 1, rim 2-3-4-5, all links two-way (Algorithm 2)
pa = {1: (0, 0)}
for n, ang in zip((2, 3, 4, 5), (135, 45, -45, -135)):
    pa[n] = (1.25 * math.cos(math.radians(ang)), 1.25 * math.sin(math.radians(ang)))
g = paper.fig5a()
for u, v in g.edges:
    if u < v: edge(A, pa[u + 1], pa[v + 1])
x5a, att5a = [8, 6, 1, 3, 9], {4: "lies at k=13", 5: "lies at k=4"}
for n, p in pa.items(): node(A, p, n, n in att5a, x5a[n - 1])
for n, t in att5a.items():
    A.text(pa[n][0], pa[n][1] + (-0.43 if pa[n][1] < 0 else 0.43), t, ha="center", fontsize=10, color=RED, fontweight="bold")
A.set_title("Fig. 5(a): 5-node wheel, Algorithm 2 (all links two-way)", fontsize=13, fontweight="bold")
A.text(0, -2.0, "Experiment: nodes 4 and 5 lie one after the other.\nBoth are caught and the honest nodes end at 5.", ha="center", fontsize=10.5)

# ---- Fig 5(b): directed ring 1->...->6->1 plus 9 two-way chords (Algorithm 3)
pb = {n: (1.4 * math.cos(math.radians(90 - 60 * (n - 1))), 1.4 * math.sin(math.radians(90 - 60 * (n - 1)))) for n in range(1, 7)}
for u, v in CHORDS: edge(B, pb[u], pb[v])
for u, v in RING: edge(B, pb[u], pb[v], arrow=True, col=BLUE, lw=3, rad=-0.18)
x5b = [9, 7, 1, 3, 4, 6]
for n, p in pb.items(): node(B, p, n, n == 6, x5b[n - 1])
B.text(pb[6][0] - 0.32, pb[6][1] + 0.02, "attacker", ha="right", va="center", fontsize=10, color=RED, fontweight="bold")
B.set_title("Fig. 5(b): 6-node directed network, Algorithm 3", fontsize=13, fontweight="bold")
B.text(0, -2.15, "Blue arrows = one-way ring.  Grey lines = two-way links.  (n) = starting value.\n"
       "Node 6 lies; nodes 1 to 4 hear it directly, node 5 only through the vote.", ha="center", fontsize=10.5)
fig.tight_layout()
fig.savefig("fig5_networks.png", dpi=130)
print("wrote fig5_networks.png")
