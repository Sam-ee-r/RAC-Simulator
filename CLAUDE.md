# RAC-Simulator: project context for Claude Code

## What this is
Final year project (FAST-NUCES Karachi) by Sameer Rajani (group leader), Minaal Fatima Jilani and Hamza Nasir Lodi. Supervisor: Abuzar Zafar. FYP-I defence Jan 2027, FYP-II June 2027.

Topic: Resilient Average Consensus (RAC). Base paper: Yuan and Ishii, arXiv:2405.18752, IEEE TAC 70(1), 2025. An earlier FYP proposal was rejected for lacking novelty, so novelty claims must be careful and honest.

Plan: FYP-I = working simulator and toolkit plus a seeded vulnerability proof of concept (equivocation / two-faced liar). FYP-II = attacker optimization plus a learned detector, possibly an equivocation-resistant defence.

## Code map
- `rac_sim/`: graph, agent, attacks, detectors, alg2, alg3, sim, paper (graphs from the paper's figures).
- `tests/`: run with `python -m pytest -m "not slow"` (142 passing at last run). On Windows use `python`, not `python3`.
- `experiments/`: equivocation sweeps, ablation, literal Step 1a check (`literal_step1a.py`).
- `run_demo*.py`, `draw_*.py`, `reproduce_paper.py`: figures. `literature.md`: literature check.
- Alg 1 = averaging with recovery. Alg 2 = shared-noticeboard detection (undirected, f-total). Alg 3 = fully distributed detection (directed, f-local).

## Our three Alg 3 interpretation decisions (awaiting supervisor confirmation)
1. Accept a relayed value or ID once at least f+1 copies agree (paper says only "majority").
2. "Faulty reporter" = relay whose report contradicts what node i knows; a missing report is blamed only if i `can_verify` it.
3. "For the second time" = one-step grace: a mismatch must persist more than one step. Claims are judged against knowledge at the START of the step.
Questions for the supervisor are in the FYP Project doc `questions-for-abuzar.md`.

## Key findings so far
- All Section VI experiments of the paper reproduce (close, not identical).
- Equivocation (a liar that deceives only some out-neighbours) makes Alg 3 flag honest nodes: 425/425 single-victim runs, robust to grace 0/1/3/10 and to a literal Step 1a reading. Broadcast (all neighbours lied to) is handled correctly.
- Wording to use: "Algorithm 3 misfires under equivocation", not a general vulnerability of detection-based consensus. Literature search found no direct prior work (see `literature.md`), but the citation list was not checked.

## Open items
- Literal-mode Step 1b not tested. Eq. 8/9 undo formula never checked against the typeset paper.
- Why only victim pair (1,2) on Fig 5b is CORRECT is untraced.
- Known bug: `run_demo_alg2.py` panel 1 and `demo_alg2_networks.png` panel 1 use `E5`, not the paper's Fig 5a wheel (`paper.fig5a()`), and are mislabelled "paper's 5-node network". Fix and regenerate.
- User to check the Google Scholar "cited by" list for arXiv:2405.18752.
- Next build steps: many-seed evaluation harness (time to detection, false flags, error), web demo, report writing, roles for Minaal and Hamza.

## Working rules
- Do not overstate novelty. Lemma 1 of Alg 2 is the paper's own result, not ours.
- Keep paper-reproduction tests green before and after any change to `alg2.py` or `alg3.py`.
- The user prefers short, plain-language explanations. Avoid double hyphens.
