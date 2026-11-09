# rac_sim

Simulator for Resilient Average Consensus (Yuan & Ishii, arXiv:2405.18752).

```
pip install numpy pytest matplotlib
python -m pytest -q        # 125 tests (~75 s); add -m 'not slow' to skip the 30-node run
python run_demo.py         # Alg 1 with oracle detector -> demo.png
python run_demo_alg2.py    # Alg 2 scenarios -> demo_alg2.png
python run_demo_alg3.py    # Alg 3 collusion + grace ablation -> demo_alg3.png
python reproduce_paper.py  # every Section VI experiment on the paper's graphs -> paper_reproduction.png
```

## Layout

| File | Owner idea | Contents |
|---|---|---|
| `rac_sim/agent.py` | Core | `Agent` (Algorithm 1 state + update + recovery), `Phi` message |
| `rac_sim/sim.py` | Core | Synchronous driver, `Result` |
| `rac_sim/detectors.py` | Detection | `Detector` interface, `NoDetector`, `OracleDetector` (validation only) |
| `rac_sim/alg2.py` | Detection | `Algorithm2`: sharing detection, checks silent/1/2/3/4, `log` of (k, detector, flagged, reason) |
| `rac_sim/alg3.py` | Detection | `Algorithm3(f, grace)`: value/ID voting (f+1), private A2 set, direct checks, claim checks 1a/1b with grace |
| `rac_sim/attacks.py` | Graphs/eval | `Crash`, `Offset`, `Frozen`, `RandomLie`, `TamperInbox` (lie about what a neighbor sent), `FakeDetection`, `Conceal` (hide a colluder), `Equivocate` (different values to different out-neighbours) |
| `rac_sim/paper.py` | Graphs/eval | Paper graphs (Fig. 4b, 5a, 5b, 8, 11) read from the PDF + Section VI experiments |
| `rac_sim/graph.py` | Graphs/eval | `Digraph`, `undirected`, `circulant`, 1-indexed loader, `satisfies_assumption4` / `assumption4_violations` |

## Interface contract (agree on this first)

* A node broadcasts one `Phi` per step: detected set `A`, its next running sums `own_next = (lambda[k+1], gamma[k+1])`, and `seen = {j: (delta_ij[k], omega_ij[k])}`.
* A detector implements `detect(agent, k, inbox, graph) -> set of newly flagged node IDs`, where `inbox[j]` is `Phi_j[k-1]` (or `None` if j was silent).
* Silence is treated as detection by the agent itself.
* `Detector.shared = True` makes the runner union all normal nodes' flags each step and hand the union to every node (Assumption 3).
* `Detector.run_on_adversaries = True` (Alg 3): adversaries run the honest detector on their real inbox, then `Attack.filter_detections` can hide results.
* The simulator delivers per-recipient messages. Normal attacks send one (possibly corrupted) message to everyone (the paper's "malicious" model); attacks with `equivocates = True` choose a message per recipient via `transform_to` (Byzantine, outside the paper's model).
* Attacks can corrupt outgoing messages (`transform`) and/or what they claim to have received (`tamper_inbox`).

## Known gaps / TODO

1. Paper graphs are in `rac_sim/paper.py` and all Section VI results reproduce (tests/test_paper.py). Older tests still use synthetic graphs.
2. Algorithm 3 rests on three interpretation decisions (paper is ambiguous; see project doc `claude/rac-algorithms.md`):
   accept by >= f+1 identical copies; 'faulty reporter' = any relay contradicting the vote; 'for the second time' = one-step grace.
   Claims in Phi_j[k-1] are judged against what i knew at the START of step k. Without that, or with grace=0, honest nodes get flagged (see test_grace_period_is_needed and demo_alg3.png).
6. Alg 2 Step 2 is slightly stricter than the paper's wording: the reported ID set must equal j's trusted in-neighbors plus j (missing IDs are flagged too, since Step 4 needs them).
7. Float checks use a relative tolerance of 1e-9. No false positives in 25 random graphs over 2000 steps, but this tolerance is a candidate attack surface for the vulnerability PoC.
3. Eq. 8/9 ambiguity: the PDF text extraction gave two forms for Case 1. The code sums over trusted in-neighbors only (Eq. 8) and then subtracts the detected neighbor's cumulative inflow `delta_ij[k-1]` (Eq. 9). Summing over all neighbors AND subtracting would double count. Check against the typeset paper.
4. `y` and `z` can go negative or `z` near 0 right after a recovery step. `Agent.estimate` returns NaN if `|z| < 1e-12`.
8. Graphs satisfying both Assumption 4 (f=1) and admitting a 1-local colluding pair are rare among random digraphs (~6 in 130k samples at n=10-14). The three found are saved in tests/data/.
9. Alg 3 only blames j for a MISSING detection of m if j can verify everything m reports (`can_verify`). Needed to match the paper's Fig. 6(a): on the graph violating Assumption 4, honest nodes must not flag each other.
10. Attack details the paper leaves vague ("manipulates its values arbitrarily") are our choice in paper.py; the expected averages do not depend on them.

## Equivocation experiments (vulnerability proof-of-concept, `experiments/`)

The paper's threat model has a malicious node send the SAME message to all out-neighbours; different values to different neighbours (Byzantine) is out of scope. `Equivocate(at, {recipient: dy})` lets an attacker lie to only some out-neighbours.

* `experiments/equiv_sweep.py`: 8 graphs (paper Fig. 5b and 4b, 6 random Assumption-4 digraphs, n = 8-10), 3 attackers each, many victim subsets, f = 1, one corrupted message (+4) at k = 3. 336 runs.
* `experiments/equiv_ablation.py`: single victim on every (attacker, out-neighbour) pair of the same graphs, 425 runs, under grace = 0/1/3/10 and with claim checks disabled.
* `run_demo_equivocation.py` -> `demo_equivocation.png`; tests in `tests/test_equivocation.py`.

Outcomes (Algorithm 3, default interpretation): lying to ALL out-neighbours: 10/10 correct (matches the paper). Lying to exactly ONE: 138/138 false flags (honest nodes flagged, consensus off target). Two victims: 5/54 correct. Three or more (not all): 87/134 correct, depends on the graph.
Ablation (single victim, 425 runs): false flag in 425/425 for grace 0, 1, 3 and 10; with claim checks disabled, no flags at all but the average is wrong in 425/425.
Mechanism: a lone victim is the only node that sees the inconsistency, flags the attacker and reports it; the attacker's other out-neighbours see it behave normally, read the report as a lie (checks 1a/1b) and flag the honest victim. With fewer than f+1 reporters the ID vote cannot convict the attacker.

Caveats: (1) outside the paper's stated threat model, so this is a gap to explore, not a refutation; (2) rests on our reading of the ambiguous Alg 3 Step 1a/1b; the literal Step 1a would probably also flag the reporter but we have not shown this; (3) no literature check yet for prior work on equivocation against this class of algorithms.
