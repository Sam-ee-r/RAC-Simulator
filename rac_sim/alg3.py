"""Algorithm 3: fully distributed detection (directed graphs, f-local adversaries).

No sharing assumption: node i only sees Phi_j[k-1] from its in-neighbors j. Everything about
nodes further away is learned by voting over relays. A relay of node m (for i) is a trusted
in-neighbor j of i that has m as its own in-neighbor, i.e. a two-hop path m -> j -> i.

Per step k, node i:
  1. VALUE VOTE  for every node h that is not i's in-neighbor: the copies of lambda_h, gamma_h
     that relays report in Phi_j.seen. A value backed by >= f+1 identical copies is the truth
     (f-local: at most f liars among i's in-neighbors). [Decision 1]
  2. ID VOTE     for every ID m in the relays' detected sets: if >= f+1 relays report m, m is
     malicious. If m is i's in/out-neighbor it goes into A_i (and triggers recovery),
     otherwise into the private set A2_i.
  3. DIRECT CHECKS on each trusted in-neighbor j (same as Alg 2 minus Step 1):
       silent, badA (A_j names a non-neighbor of j), step2 (ID set), step3 (claimed received
       values vs i's own copies or voted values), step4 (reconstruction).
  4. CLAIM CHECKS (Steps 1a/1b + 'faulty reporter'): for every neighbor m of j, compare j's
     claim "m in A_j" with what i knows about m (malicious / honest / unknown). A mismatch must
     persist for more than `grace` consecutive steps before j is flagged, because honest
     out-neighbor detections arrive one step late. [Decisions 2 and 3]
       1a: m is an in-neighbor of j      1b: m is an out-neighbor of j
     A relay that contradicts an ID vote is exactly such a mismatch, so the 'faulty reporter'
     j' of the listing is covered by the same rule.

Guarantees (paper Thm 1) need the graph to satisfy Assumption 4: see graph.satisfies_assumption4.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .alg2 import step4_check
from .detectors import Detector
from .graph import detectable


def can_verify(graph, m, j, f) -> bool:
    """Can node j check everything m reports? j must get m's own values (m detectable by j)
    and the true value of every in-neighbor h of m that m reports about."""
    return detectable(graph, m, j, f) and all(
        h == j or detectable(graph, h, j, f) for h in graph.in_nbrs[m])


class Algorithm3(Detector):
    shared = False
    run_on_adversaries = True     # adversaries run the honest rule internally to stay hidden

    def __init__(self, f: int = 1, tol: float = 1e-9, grace: int = 1, claims: bool = True):
        self.f, self.tol, self.grace, self.claims = f, tol, grace, claims   # claims=False: ablation, no 1a/1b
        self.prev: dict = {}                      # (i, j) -> Phi_j[k-2]
        self.A2: dict = defaultdict(set)          # i -> private two-hop detections
        self.strikes: dict = defaultdict(int)     # (i, j, m) -> consecutive mismatches
        self.log: list = []                       # (k, i, j, reason)

    def _neq(self, a, b) -> bool:
        return any(abs(p - q) > self.tol * max(1.0, abs(p), abs(q)) for p, q in zip(a, b))

    def detect(self, agent, k, inbox, graph):
        i, f = agent.i, self.f
        Nin_i, Nout_i = set(agent.in_nbrs), set(agent.out_nbrs)
        A_i, A2 = set(agent.A), self.A2[i]
        # Claims in Phi_j[k-1] can only reflect knowledge up to step k-1, so they are judged
        # against what i knew at the START of step k (not this step's new detections).
        known_mal = A_i | set(A2)
        trusted = {j: m for j, m in inbox.items() if j not in A_i and m is not None}
        flagged: dict = {}

        for j in Nin_i - A_i:
            if inbox.get(j) is None:
                flagged[j] = "silent"

        def relays(m):
            return [j for j in trusted if m in graph.in_nbrs[j]]

        # 1. value vote
        voted = {}
        far = set().union(*(set(graph.in_nbrs[j]) for j in trusted)) - Nin_i - {i} \
            if trusted else set()
        for h in far:
            cnt = Counter(trusted[j].seen[h] for j in relays(h) if h in trusted[j].seen)
            if cnt:
                val, c = cnt.most_common(1)[0]
                if c >= f + 1:
                    voted[h] = val

        # 2. ID vote
        reported = set().union(*(m.A for m in trusted.values())) if trusted else set()
        for m in reported - {i}:
            if sum(1 for j in relays(m) if m in trusted[j].A) >= f + 1:
                if m in Nin_i | Nout_i:
                    if m not in A_i:
                        flagged.setdefault(m, "vote")
                else:
                    A2.add(m)

        # 3. direct checks
        for j, msg in trusted.items():
            if j in flagged:
                continue
            reason = self._direct(agent, j, msg, voted, graph)
            if reason:
                flagged[j] = reason

        # 4. claim checks (1a / 1b / faulty reporter), with grace
        def status(m):
            if m == i:
                return "honest"
            if m in known_mal:
                return "mal"
            if m in Nin_i or len(relays(m)) >= 2 * f + 1:
                return "honest"
            return None                               # i cannot judge m

        for j, msg in (trusted.items() if self.claims else ()):
            if j in flagged:
                continue
            for m in (set(graph.in_nbrs[j]) | set(graph.out_nbrs[j])) - {j}:
                st = status(m)
                claim = m in msg.A
                key = (i, j, m)
                # Only blame j for a MISSING detection if j was positioned to make it
                # (m detectable by j). Matters only on graphs violating Assumption 4.
                if st == "mal" and not claim and not can_verify(graph, m, j, f):
                    st = None
                if st is not None and (claim != (st == "mal")):
                    self.strikes[key] += 1
                    if self.strikes[key] > self.grace:
                        flagged[j] = "1a" if m in graph.in_nbrs[j] else "1b"
                        break
                else:
                    self.strikes.pop(key, None)

        for j, reason in flagged.items():
            self.log.append((k, i, j, reason))
        for j, msg in inbox.items():
            if msg is not None:
                self.prev[(i, j)] = msg
        return set(flagged)

    def _direct(self, agent, j, msg, voted, graph):
        i = agent.i
        Nin_j, Nout_j = set(graph.in_nbrs[j]), set(graph.out_nbrs[j])
        if not msg.A <= Nin_j | Nout_j:
            return "badA"
        if set(msg.seen) != (Nin_j - msg.A) | {j}:
            return "step2"
        for h, val in msg.seen.items():
            if h in agent.A or h in self.A2[i]:
                continue
            if h == i or h in agent.in_nbrs:
                ref = (agent.delta[h], agent.omega[h])
            elif h in voted:
                ref = voted[h]
            else:
                continue                                  # not verifiable by i
            if self._neq(val, ref):
                return "step3"
        return step4_check(j, msg, self.prev.get((i, j)), graph, self._neq)
