"""Synchronous simulation driver."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .agent import Agent
from .detectors import Detector, NoDetector


@dataclass
class Result:
    n: int
    normal: list
    target: float                 # average of the normal nodes' initial values
    r: np.ndarray                 # r[k, i]  estimate y/z at every step (adversaries included)
    detected: list = field(default_factory=list)   # detected[k][i] = frozenset A_i[k]

    def max_error(self, k=-1, target=None, nodes=None) -> float:
        nodes = self.normal if nodes is None else nodes
        t = self.target if target is None else target
        return float(np.nanmax(np.abs(self.r[k, nodes] - t)))

    def flagged_by_normals(self, k=-1) -> set:
        return set().union(*(self.detected[k][i] for i in self.normal))

    def first_detection(self, j):
        """First step at which some normal node has j in its detected set (None if never)."""
        for k, row in enumerate(self.detected):
            if any(j in row[i] for i in self.normal):
                return k
        return None


def simulate(graph, x0, adversaries=None, detector: Detector | None = None, steps=200) -> Result:
    adversaries = adversaries or {}
    detector = detector or NoDetector()
    n = graph.n
    x0 = np.asarray(x0, dtype=float)
    normal = [i for i in range(n) if i not in adversaries]
    target = float(x0[normal].mean())

    agents = [Agent(i, x0[i], graph.in_nbrs[i], graph.out_nbrs[i]) for i in range(n)]
    r = np.full((steps + 1, n), np.nan)
    det_hist = [[frozenset() for _ in range(n)]]
    shared: set = set()

    def emit(into, a, msg, k):
        """Put the message(s) node a sends after step k on every out-edge."""
        atk = adversaries.get(a.i)
        if atk is None:
            for rcv in a.out_nbrs:
                into[(a.i, rcv)] = msg
        elif atk.equivocates:                       # Byzantine: one message per recipient
            for rcv in a.out_nbrs:
                into[(a.i, rcv)] = atk.transform_to(msg, k, rcv)
        else:                                       # malicious: same message to everyone
            sent = atk.transform(msg, k)
            for rcv in a.out_nbrs:
                into[(a.i, rcv)] = sent

    out = {}                                        # out[(sender, receiver)] -> Phi or None
    for a in agents:
        emit(out, a, a.init_message(), 0)
        r[0, a.i] = x0[a.i]

    for k in range(1, steps + 1):
        raw, inboxes = {}, {}
        for a in agents:
            raw[a.i] = {j: out.get((j, a.i)) for j in a.in_nbrs}
            atk = adversaries.get(a.i)
            inboxes[a.i] = atk.tamper_inbox(raw[a.i], k) if atk else raw[a.i]

        # detection phase. Adversaries run the honest detector on their REAL inbox (if the
        # detector supports it) and may then hide some of their detections.
        found = {a.i: set() for a in agents}
        run_adv = getattr(detector, "run_on_adversaries", False)
        for a in agents:
            atk = adversaries.get(a.i)
            if atk is None:
                found[a.i] = detector.detect(a, k, inboxes[a.i], graph)
            elif run_adv:
                found[a.i] = atk.filter_detections(detector.detect(a, k, raw[a.i], graph), k)
        if detector.shared:                         # Assumption 3: secure same-step sharing
            for i in normal:
                shared |= found[i]
            found = {a.i: set(shared) for a in agents}   # adversaries see it too and mimic

        new_out = {}
        for a in agents:
            emit(new_out, a, a.step(inboxes[a.i], found[a.i]), k)
            r[k, a.i] = a.estimate
        out = new_out
        det_hist.append([frozenset(a.A) for a in agents])

    return Result(n=n, normal=normal, target=target, r=r, detected=det_hist)
