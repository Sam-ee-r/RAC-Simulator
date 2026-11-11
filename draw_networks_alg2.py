"""Network diagrams for the three Algorithm 2 scenarios in demo_alg2.png -> demo_alg2_networks.png
Usage: python draw_networks_alg2.py"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

BLUE, RED, AMBER, GREEN, GREY = "#3B6FD8", "#D9483B", "#D98F1F", "#2E9E6A", "#9AA3AF"
R = 0.22

E5 = [(u - 1, v - 1) for u in range(1, 6) for v in range(u + 1, 6) if (u, v) != (1, 2)]
BASE = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (4, 0), (4, 1), (5, 2), (5, 3), (4, 5)]
START5, START6 = [8, 6, 1, 3, 9], [2, 9, 4, 7, 5, 1]

pent = {i: (1.6 * math.cos(math.radians(90 + 72 * i)), 1.6 * math.sin(math.radians(90 + 72 * i))) for i in range(5)}
six = {0: (-0.9, 0.7), 1: (0.9, 0.7), 2: (0.9, -0.7), 3: (-0.9, -0.7), 4: (0, 2.1), 5: (0, -2.1)}

CASES = [
    dict(title="Panel 1: paper's 5-node network", pos=pent, edges=E5, start=START5,
         roles={4: ("attacker", "lies at k=4"), 3: ("attacker", "lies at k=13")},
         note="Links are two-way. Every node can be cross-checked by shared neighbours.\n"
              "Both attackers are caught one step after lying; final answer 5.0.", extra=None),
    dict(title="Panel 2: colluding pair, common honest neighbour", pos=six, edges=BASE + [(0, 5)], start=START6,
         roles={4: ("attacker", "lies about node 6"), 5: ("accomplice", "behaves normally")},
         note="Node 1 touches BOTH attackers, so it can compare node 5's claim\n"
              "with what node 6 really sent. Node 5 is caught; final answer 4.6.", extra="common"),
    dict(title="Panel 3: colluding pair, NO common honest neighbour", pos=six, edges=BASE, start=START6,
         roles={4: ("attacker", "lies about node 6"), 5: ("accomplice", "behaves normally")},
         note="No honest node touches both attackers (link 1-6 removed),\n"
              "so no check can expose the lie. Not detected; answer is wrong.", extra=None),
]

fig, axes = plt.subplots(1, 3, figsize=(18, 6.4))
for ax, cs in zip(axes, CASES):
    pos = cs["pos"]
    ax.set_aspect("equal"); ax.axis("off")
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    ax.set_xlim(min(xs) - 1.4, max(xs) + 1.9); ax.set_ylim(min(ys) - 1.3, max(ys) + 1.1)
    for (u, v) in cs["edges"]:
        (x1, y1), (x2, y2) = pos[u], pos[v]
        bad = {u, v} <= {4, 5} and cs["extra"] is not None or {u, v} == {4, 5}
        special = cs["extra"] == "common" and {u, v} == {0, 5}
        rad = 0.0
        if cs["pos"] is six and {u, v} == {4, 5}: rad = -1.1
        if special: rad = 0.95
        col, lw, ls = (AMBER, 3, "-") if bad and cs["pos"] is six else ((GREEN, 3.5, "-") if special else (GREY, 2, "-"))
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-", connectionstyle=f"arc3,rad={rad}",
                                     color=col, lw=lw, ls=ls, shrinkA=R * 72 * 1.35, shrinkB=R * 72 * 1.35, zorder=1))
    for i, (x, y) in pos.items():
        role = cs["roles"].get(i)
        edge = RED if role and role[0] == "attacker" else (AMBER if role else BLUE)
        fill = "#FBE4E1" if role and role[0] == "attacker" else ("#FCEFD8" if role else "#E4ECFB")
        ax.add_patch(Circle((x, y), R + 0.13, fc=fill, ec=edge, lw=3, zorder=3))
        ax.text(x, y + 0.07, str(i + 1), ha="center", va="center", fontsize=17, fontweight="bold", zorder=4)
        ax.text(x, y - 0.15, f"({cs['start'][i]})", ha="center", va="center", fontsize=10, color="#555", zorder=4)
        if role:
            dy = 0.62 if (y >= 0 and not (cs["pos"] is pent and i == 3)) else -0.62
            if cs["pos"] is pent: dy = 0.62 if i == 4 else -0.75
            ax.text(x, y + dy + (0.0 if dy > 0 else -0.18), f"{role[0]}\n{role[1]}", ha="center", va="center",
                    fontsize=10, color=edge, fontweight="bold", zorder=4,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=edge, lw=1.2))
    if cs["extra"] == "common":
        x, y = pos[0]
        ax.add_patch(Circle((x, y), R + 0.32, fc="none", ec=GREEN, lw=3, ls="--", zorder=2))
        ax.text(x - 0.65, y + 0.45, "sees both\nattackers", ha="right", va="center", fontsize=10.5,
                color=GREEN, fontweight="bold")
    ax.set_title(cs["title"], fontsize=13.5, fontweight="bold", pad=8)
    ax.text(0.5, 0.0, cs["note"], transform=ax.transAxes, ha="center", va="top", fontsize=10.5, color="#333")

fig.legend(handles=[
    plt.Line2D([], [], marker="o", ls="", mfc="#E4ECFB", mec=BLUE, mew=2.5, ms=14, label="honest node"),
    plt.Line2D([], [], marker="o", ls="", mfc="#FBE4E1", mec=RED, mew=2.5, ms=14, label="attacker"),
    plt.Line2D([], [], marker="o", ls="", mfc="#FCEFD8", mec=AMBER, mew=2.5, ms=14, label="accomplice (acts normally)"),
    plt.Line2D([], [], color=GREY, lw=2, label="two-way link   (n) = starting value"),
    plt.Line2D([], [], color=AMBER, lw=3, label="link between the colluders"),
    plt.Line2D([], [], color=GREEN, lw=3.5, label="link to node 1 (panel 2 only)")],
    loc="lower center", ncol=6, fontsize=10.5, frameon=False, bbox_to_anchor=(0.5, 0.0))
fig.tight_layout(rect=(0, 0.05, 1, 1))
fig.savefig("demo_alg2_networks.png", dpi=130)
print("wrote demo_alg2_networks.png")
