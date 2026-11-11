"""Network diagrams for the Algorithm 3 demo (demo_alg3.png) -> demo_alg3_networks.png
Left: the whole 12-node directed network. Right: how node 3's lie spreads and who catches whom, and when.
Usage: python draw_networks_alg3.py"""
import json, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
from rac_sim import Digraph, simulate, Algorithm3, Offset, Conceal

BLUE, RED, AMBER, GREEN, GREY = "#3B6FD8", "#D9483B", "#D98F1F", "#2E9E6A", "#B4BBC6"
case = json.load(open("tests/data/flocal_collusion_graphs.json"))[0]
g, m, c = Digraph(case["n"], case["edges"]), case["m"], case["c"]
x = [((7 * v) % 11) - 3.0 for v in range(g.n)]
det = Algorithm3(f=1, grace=1)
res = simulate(g, x, {m: Offset(3, 4.0), c: Conceal({m})}, det, steps=40)
first = {}                                    # (flagger, flagged) -> (step, reason)
for k, i, j, why in det.log:
    if i in res.normal or True: first.setdefault((i, j), (k, why))

pos = {i: (math.cos(math.radians(90 - 30 * i)), math.sin(math.radians(90 - 30 * i))) for i in range(g.n)}
# put attacker 3 and accomplice 11 on opposite sides for clarity
Rn = 0.085


def arrow(ax, u, v, col, lw, alpha, head=True, rad=0.0, z=1):
    (x1, y1), (x2, y2) = pos[u], pos[v]
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>" if head else "-", mutation_scale=11 if head else 1,
                                 connectionstyle=f"arc3,rad={rad}", color=col, lw=lw, alpha=alpha,
                                 shrinkA=Rn * 300, shrinkB=Rn * 300, zorder=z))


def node(ax, i, fc, ec, lw=2.5):
    xx, yy = pos[i]
    ax.add_patch(Circle((xx, yy), Rn, fc=fc, ec=ec, lw=lw, zorder=4))
    ax.text(xx, yy, str(i + 1), ha="center", va="center", fontsize=13, fontweight="bold", zorder=5)


fig, (A, B) = plt.subplots(1, 2, figsize=(17, 8.2))
for ax in (A, B):
    ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-1.95, 1.95); ax.set_ylim(-1.75, 1.5)

# ---- left: the whole network
A.set_title("The whole network: 12 nodes, 88 one-way links", fontsize=14, fontweight="bold")
for (u, v) in g.edges:
    both = (v, u) in g.edges
    if both and u > v: continue
    arrow(A, u, v, GREY, 0.9, 0.55, head=not both, rad=0.0 if both else 0.08)
    if both: arrow(A, u, v, GREY, 0.9, 0.0, head=False)
for i in range(g.n):
    if i == m: node(A, i, "#FBE4E1", RED, 3.5)
    elif i == c: node(A, i, "#FCEFD8", AMBER, 3.5)
    else: node(A, i, "#E4ECFB", BLUE)
A.text(0, -1.62, "Plain line = two-way link.  Arrow = one-way link (only in the arrow's direction).",
       ha="center", fontsize=10.5, color="#333")

# ---- right: the attack and who catches it
B.set_title("The attack: who hears the lie, and who catches it and when", fontsize=14, fontweight="bold")
for (u, v) in g.edges:
    if u in (m, c):
        arrow(B, u, v, RED if u == m else AMBER, 2.4, 0.9, rad=0.06 if (v, u) not in g.edges else 0.16, z=2)
    else:
        arrow(B, u, v, GREY, 0.5, 0.18, head=False)
for i in range(g.n):
    if i == m: node(B, i, "#FBE4E1", RED, 3.5)
    elif i == c: node(B, i, "#FCEFD8", AMBER, 3.5)
    else:
        k3 = first.get((i, m), (None,))[0]
        node(B, i, "#DFF3E8" if k3 == 4 else "#E4ECFB", GREEN if k3 == 4 else BLUE)
for i in range(g.n):
    xx, yy = pos[i]; ux, uy = xx * 1.0, yy * 1.0
    lab = []
    if i not in (m, c):
        k3 = first.get((i, m)); kc = first.get((i, c))
        if k3: lab.append(f"node 3: k={k3[0]} ({'direct check' if k3[1].startswith('step') else 'vote'})")
        else: lab.append("node 3: no link, learns it\nprivately (two hops away)")
        if kc: lab.append(f"node 11: k={kc[0]}")
    elif i == m: lab.append("ATTACKER\nlies at k=3")
    else:
        k3 = first.get((i, m))
        lab.append("ACCOMPLICE\nconceals node 3")
    r = 1.0 + 0.2
    ha = "left" if xx > 0.3 else "right" if xx < -0.3 else "center"
    off = 0.02 if ha != "center" else 0
    B.text(xx * r + (off if ha == "left" else -off if ha == "right" else 0), yy * r + (0.04 if ha == "center" and yy > 0 else -0.04 if ha == "center" else 0),
           "\n".join(lab), ha=ha, va="center", fontsize=8.6,
           color=RED if i == m else AMBER if i == c else "#333", fontweight="bold" if i in (m, c) else "normal")
B.text(0, -1.62, "Red arrows: node 3's messages (the lie).  Amber: node 11's messages (relays it, hides it).  Green nodes see the lie directly.",
       ha="center", fontsize=10, color="#333")
fig.tight_layout()
fig.savefig("demo_alg3_networks.png", dpi=125)
print("wrote demo_alg3_networks.png")
