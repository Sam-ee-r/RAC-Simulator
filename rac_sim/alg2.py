"""Algorithm 2: sharing detection (undirected graphs, f-total adversaries, Assumption 3).

At step k node i holds Phi_j[k-1] (inbox) and Phi_j[k-2] (stored here) for each in-neighbor j,
and flags j if any check fails:

  silent : j sent nothing
  step1  : j's detected set A_j[k-1] differs from the shared set A_i[k-1]
  step2  : Phi_j[k-1] lists IDs that are not j's (trusted) in-neighbors or j itself
  step3  : a running sum j says it received from h differs from what i itself received from h
           (checked for h in N_i^- U {i}: common neighbors, i itself, and j's own past value)
  step4  : j's reported next running sum differs from the value i reconstructs by re-running
           j's averaging update (Eq. 8-10) on the values j says it received

Steps 3 and 4 are checked on both lambda (y-channel) and gamma (z-channel).
"""
from __future__ import annotations

from .detectors import Detector


class Algorithm2(Detector):
    shared = True

    def __init__(self, tol: float = 1e-9):
        self.tol = tol
        self.prev: dict = {}       # (i, j) -> Phi_j[k-2]
        self.log: list = []        # (k, detector i, flagged j, reason)

    def _neq(self, a, b) -> bool:
        return any(abs(p - q) > self.tol * max(1.0, abs(p), abs(q)) for p, q in zip(a, b))

    def detect(self, agent, k, inbox, graph):
        i = agent.i
        flagged = set()
        for j in agent.in_nbrs:
            if j in agent.A:
                continue
            msg = inbox.get(j)
            reason = "silent" if msg is None else \
                self._check(agent, j, msg, self.prev.get((i, j)), graph)
            if reason:
                flagged.add(j)
                self.log.append((k, i, j, reason))
        for j, msg in inbox.items():
            if msg is not None:
                self.prev[(i, j)] = msg
        return flagged

    def _check(self, agent, j, msg, prev, graph):
        i = agent.i
        Nin_j, Nout_j = set(graph.in_nbrs[j]), set(graph.out_nbrs[j])

        # Step 1: everyone should hold the same shared detected set
        if msg.A != frozenset(agent.A):
            return "step1"

        # Step 2: reported IDs must be exactly j's trusted in-neighbors plus j
        if set(msg.seen) != (Nin_j - msg.A) | {j}:
            return "step2"

        # Step 3: cross-check values i can verify itself. agent.delta[h] = delta_ih[k-1]
        # and agent.delta[i] = lambda_i[k-1], which is what j should have received at k-1.
        for h, val in msg.seen.items():
            if h in agent.A:
                continue
            if h == i or h in agent.in_nbrs:
                if self._neq(val, (agent.delta[h], agent.omega[h])):
                    return "step3"

        # Step 4: re-run j's update from what j claims it received
        return step4_check(j, msg, prev, graph, self._neq)


def step4_check(j, msg, prev, graph, neq):
    """Shared by Alg 2 and Alg 3. Rebuilds lambda_j[k], gamma_j[k] from j's reports in
    Phi_j[k-2] (prev) and Phi_j[k-1] (msg) via Eq. 8-10, compares with what j broadcast."""
    if prev is None:
        return None
    Nin_j, Nout_j = set(graph.in_nbrs[j]), set(graph.out_nbrs[j])
    M_now, M_prev = Nin_j - msg.A, Nin_j - prev.A
    Mo_now, Mo_prev = Nout_j - msg.A, Nout_j - prev.A
    if not set(prev.seen) >= M_now | {j}:
        return "step2"
    exp = []
    for c in (0, 1):                       # c=0: lambda / y,  c=1: gamma / z
        y = sum(msg.seen[h][c] - prev.seen[h][c] for h in M_now | {j})
        y -= sum(prev.seen[h][c] for h in M_prev - M_now)          # Eq. 9
        y += len(Mo_prev - Mo_now) * msg.seen[j][c]               # Eq. 10
        exp.append(msg.seen[j][c] + y / (1 + len(Mo_now)))
    return "step4" if neq(msg.own_next, exp) else None
