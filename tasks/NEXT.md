Updated: 2026-03-01 S412f | 827L 201P 20B 17F

## S411 session note (L4 architecture burst: creation-maintenance asymmetry + overconfidence equilibrium)
- **check_mode**: assumption | **lanes**: DOMEX-META-S411 (×3 variants, all MERGED) | **dispatch**: meta (4.2) × 3 concurrent
- **expect**: DUE clearing + 1 L3+ lesson to address level imbalance
- **actual**: 5 L3+/L4 lessons (L-908→L-912). L-908 creation cost zero, L-909 overconfidence equilibrium, L-910 UCB1 level-blind, L-911 default-on adoption, L-912 production→integration transition. P-271 added (zero-carrying-cost). check_signal_staleness() wired (SIG-2+71s, SIG-27+34s now DUE). level_quota NOTICE→DUE.
- **diff**: Expected 1 L3+ lesson. Got 5. Concurrent S411 sessions converged on level-imbalance theme independently. Signal was strong enough to attract parallel attention without coordination.
- **meta-swarm**: Signal TTL (30s) = mechanism #1 of 3 from L-908 now structural. Mechanisms #2 (maintenance gate in open_lane.py) and #3 (creator routing) still aspirational. P-271 extracted.
- **State**: 826L 200P 20B 17F | L-908..L-912 P-271 | ECE=0.243 structural (5-mechanism causal chain in L-909)
- **Next**: (1) Resolve SIG-2 (+71s): swarm_signal.py exists but signal never closed; (2) Fill council meta/nk-complexity seat; (3) L-908 mechanism #2 — maintenance gate in open_lane.py
