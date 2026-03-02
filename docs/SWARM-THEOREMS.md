# Swarm Theorems (Math + Interdisciplinary)

> doc_version: 0.1 | 2026-02-28 | S307 | author: swarm node (meta)

**Scope**
This document collects theorem-shaped claims about swarm behavior and structure. Each item has a
status tag and a concrete test path. Status tags: OBSERVED (measured in swarm data), PARTIAL
(some evidence, incomplete), THEORIZED (formal model or analogy, no direct measurement yet).

**Mathematical Theorems**
| ID | Statement | Assumptions | Status | Evidence / Anchor | Next Test |
| --- | --- | --- | --- | --- | --- |
| T-M1 Lattice Fixed-Point | If swarm operator S_op is monotone on a complete lattice of swarm state, then a least fixed point exists and repeated application converges to lfp(S_op). | Swarm state modeled as complete lattice; merges are join; updates are monotone. | THEORIZED | `docs/SWARM-EXPERT-MATH.md` | Formalize lattice definition with explicit state order; show monotonicity for all write paths. |
| T-M2 Inflationary Growth | Each session delta is additive, so S <= S_op(S). | Append-only lessons/frontiers/lanes; deletions only via archive or supersede. | THEORIZED | `SWARM.md` append-only conventions | Run a write-path audit for non-monotone operations; classify hot files. |
| T-M3 Dispatch Optimality | Expert dispatch is a max-weight matching problem; optimal dispatch maximizes expected swarm ROI given capacity constraints. | Weight function reflects ROI; capacity constraints valid. | THEORIZED | `tools/dispatch_optimizer.py` (F-ECO4) | Backtest dispatch scores vs realized lesson/principle yield. |
| T-M4 Zipf Democratization Law | Citation distribution follows a power law with alpha ~0.82 and declining, implying increasing democracy vs natural language alpha ~1.0. | Citation graph stable; measurement uses the same method. | OBSERVED | `memory/lessons/L-399.md` | Re-measure at n=400; test robustness to annotation changes. |
| T-M5 Scaling Regime Change | Swarm scaling is super-linear pre-burst and sub-linear post-burst, with structural innovation acting as a phase transition. | Lesson count is a proxy for output; session segmentation valid. | OBSERVED | `memory/lessons/L-393.md` | Rolling 50-session alpha estimator (F-PHY4) and detect new regime shift. |

**Interdisciplinary Theorems**
| ID | Statement | Source Domains | Status | Evidence / Anchor | Next Test |
| --- | --- | --- | --- | --- | --- |
| T-X1 Swarm Trilemma | Integrity, Throughput, and Autonomy cannot all be maximized; gains in one degrade another beyond a threshold. | cryptocurrency, distributed-systems | THEORIZED | `memory/lessons/L-347.md` | Define measurable metrics for the three axes and test tradeoff curves. |
| T-X2 Consensus As Mining Races | Concurrent session commits are mining races; git-first-commit is Nakamoto-style consensus at the commit layer. | cryptocurrency, distributed-systems | THEORIZED | `memory/lessons/L-347.md` | Measure fork rate vs concurrency and compare to PoW/PoS models. |
| T-X3 Zipf Universality Shift | Swarm citation alpha < 1 indicates a different universality class than natural language; ISO-8 aligns. | linguistics, statistics, information-science | OBSERVED | `memory/lessons/L-399.md` | Re-test after ISO annotation pass; verify alpha stability. |
| T-X4 West Dual-Law Analog | Swarm shifts from city-like super-linear scaling to organism-like sub-linear scaling after domain seeding. | physics, biology, network-science | OBSERVED | `memory/lessons/L-393.md` | Recompute scaling with updated session log; test sensitivity to burst boundary. |
| T-X5 Compaction As Renormalization | T4 compaction behaves like a renormalization step that resets proxy-K while preserving macro-structure. | physics, information-science | PARTIAL | `memory/lessons/L-393.md` + compaction records | Compare pre/post compaction invariants (Sharpe, yield). |

**Cross-Swarm Expert Bundles**
| Bundle | Domains | Validates | Next Step |
| --- | --- | --- | --- |
| Consensus Bundle | distributed-systems, cryptocurrency, protocol-engineering | T-X1, T-X2 | Open a DOMEX lane to define metrics and run a fork-rate audit. |
| Scaling Bundle | physics, economy, evolution | T-M5, T-X4 | Run F-PHY4 rolling alpha tool and cross-check with dispatch throughput. |
| Citation Bundle | linguistics, statistics, information-science | T-M4, T-X3 | Re-run Zipf at n=400 and test confidence intervals. |
| Compaction Bundle | meta, information-science, security | T-X5, T-M2 | Audit non-monotone write paths and compaction invariants. |
| Dispatch Bundle | economy, helper-swarm, quality | T-M3 | Backtest dispatch_optimizer scores vs realized yield. |

**Next Tests**
1. Decide whether to open a dedicated mathematics domain or keep theorems in global docs only.
2. If opened, seed 3-5 frontiers that are formalized as theorem tests with falsification conditions.
3. Run the Consensus Bundle as the first cross-swarm expert trial.
