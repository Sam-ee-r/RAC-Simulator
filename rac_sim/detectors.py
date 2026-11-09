"""Detector interface.

Algorithm 2 and Algorithm 3 (FYP work item) implement `Detector.detect`. Everything else in
the simulator is agnostic to which detector is plugged in.

detect() runs at the start of step k at node `agent` and returns the set of node IDs the agent
newly flags. It may read: inbox (Phi_j[k-1] for each in-neighbor j), the agent's own state, and
the graph (A1 in the paper: topology of two-hop in-neighbors and direct out-neighbors is known).
"""
from __future__ import annotations


class Detector:
    # If True, the runner unions every normal node's flags each step and gives the union to
    # all nodes in the same step (paper Assumption 3, needed by Algorithm 2).
    shared = False

    def detect(self, agent, k: int, inbox: dict, graph) -> set:
        raise NotImplementedError


class NoDetector(Detector):
    """Negative control: plain averaging with no defence."""
    def detect(self, agent, k, inbox, graph):
        return set()


class OracleDetector(Detector):
    """Placeholder that knows the attacks. Flags adversary j at the first step where a corrupted
    message is consumed, for every normal node that has j as an in- or out-neighbor.

    Used ONLY to validate the averaging and recovery logic of Algorithm 1 in isolation. It is
    what Algorithm 2 / 3 are supposed to approximate with local information.
    """
    def __init__(self, attacks: dict):
        self.attacks = attacks

    def detect(self, agent, k, inbox, graph):
        flagged = set()
        for j in set(agent.in_nbrs) | set(agent.out_nbrs):
            atk = self.attacks.get(j)
            if atk is not None and k >= atk.at + 1:   # Phi_{at} is consumed at step at+1
                flagged.add(j)
        return flagged
