# Literature check: equivocation against detection-based resilient average consensus

Date of search: 24 Nov 2026. Method: web search and reading summaries only. IEEE Xplore, Google Scholar and the base paper's full citation list were NOT accessible, so "not found" is not "does not exist". Check each claim against the full text before quoting it.

Base paper: Yuan and Ishii, "Resilient Average Consensus with Adversaries via Distributed Detection and Recovery", arXiv:2405.18752, IEEE TAC 70(1), 2025.

## Summary table

| Paper | What it does | Covers a two-faced liar (equivocation)? |
|---|---|---|
| Yuan and Ishii, base paper (TAC 2025) | Algorithms 1-3. Says a Byzantine node can send different values to different neighbours and studies the "malicious" model (same message to all) instead. | No, out of scope by design. |
| Yuan and Ishii, "Secure Consensus with Distributed Detection via Two-hop Communication" (Automatica 2021, arXiv:2101.05087) | Earlier two-hop detection paper. Same malicious vs Byzantine distinction. | No, same malicious model. |
| Dibaji, Safi, Ishii 2019, "Resilient distributed averaging" | Byzantine average consensus. The only Byzantine method in the base paper's comparison table. Uses flooding. | Yes, but a different and heavier approach (flooding), not running-sum detection and recovery. |
| Hadjicostis and Dominguez-Garcia, "Trustworthy Distributed Average Consensus based on Locally Assessed Trust Evaluations" (CDC 2022, arXiv:2309.00920) | Nearest relative. Running-sum scheme with a broadcast assumption. Admits an honest node can become "possibly untrustworthy" when neighbours give conflicting reports; handled by argument, not a full proof. Assumes no two malicious nodes are neighbours. | No. |
| Hadjicostis et al., "Shadow Banning in Directed Graphs for Fault-Tolerant Averaging" (ECC 2025) | Newer running-sum detection scheme. Does not explicitly address Byzantine behaviour or false accusation from manipulated two-hop data. | No. |
| Local-broadcast model papers (Khan, Tseng, Vaidya and others, e.g. arXiv:1903.11677) | Byzantine agreement. Equivocation is possible when messages are not overheard by other neighbours; under local broadcast, conflicting information can be detected. | Yes, but for Byzantine agreement, not average consensus. |

## Two near-misses to read closely
- arXiv 2309.00920, Section V: how conflicting reports from neighbours are handled.
- ECC 2025 Shadow Banning: false-accusation discussion.

## What this means for novelty
- Not new: the idea of equivocation, and that broadcast and Byzantine models differ.
- Possibly new: a concrete demonstration that Algorithm 3 blames honest nodes when one liar deceives only some of its neighbours, including under the literal reading of Step 1a (425 of 425 single-victim runs gave false flags).
- Suggested wording: "Algorithm 3 of Yuan and Ishii misfires under equivocation." Avoid claiming a general vulnerability of detection-based consensus.
- Framing question for the supervisor: broadcast is realistic for wireless links, so when can equivocation actually occur (point-to-point links)? A natural FYP-II defence is to force messages to be overheard by neighbours, as the local-broadcast papers suggest.

## Not checked
- Papers citing the base paper (Semantic Scholar was blocked). Later citing papers seen in passing were about other topics: trust-learning attacks, Byzantine neighbour selection, Byzantine vector consensus.
- TODO (user): open the Google Scholar "cited by" list for arXiv:2405.18752 and scan for the words Byzantine, equivocation, false accusation, running-sum.

## Links
- https://arxiv.org/abs/2405.18752
- https://arxiv.org/abs/2101.05087
- https://arxiv.org/abs/2309.00920
- https://aledan.ece.illinois.edu/files/2025/08/ECC_2025.pdf
- https://arxiv.org/abs/1903.11677
