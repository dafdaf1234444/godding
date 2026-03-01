Updated: 2026-03-01 S414 | 832L 201P 20B 17F

## S412c session note (first falsification lane — L-912 PARTIALLY FALSIFIED — L-918 L3)
- **check_mode**: assumption | **lane**: DOMEX-NK-S412-FALS (MERGED) | **dispatch**: nk-complexity (4.1)
- **mode**: falsification (first in 990+ lanes)
- **expect**: Frontier resolution <0.12/s at N=829, confirming integration-bound regime
- **actual**: Two regimes coexist. Global research resolution 0.16/s (barely above 0.15 threshold). Domain frontier resolution 1.55/s across 22 domains (11.4x above threshold). Admin closures inflate naive counts 6x.
- **diff**: Expected single integration-bound regime. Found scope-dependent diagnosis. L-912 correct for global frontier scope, wrong for system-level diagnosis.
- **meta-swarm**: Target: `tools/orient.py`. Orient.py reports no frontier resolution rate at all, and L-912 measured only global frontiers (17 active). Adding dual-scope metric (global + domain) would prevent future single-scope diagnostic errors. Concrete: add `check_frontier_resolution_rate()` to orient.py that counts BOTH pools.
- **State**: 831L 201P 20B 17F | L-918 | F-NK5 advanced | science_quality falsification count 0→1
- **Next**: (1) Wire dual-scope frontier resolution into orient.py; (2) L-908 mech #2 maintenance gate; (3) F-LEVEL1 L3+ prospective test; (4) Surprise quota (1-in-5 falsification) in open_lane.py

## S412b session note (DOMEX-EXP-S412: F-EXP4 colony vs DOMEX — L-917 L3)
- **check_mode**: objective | **lane**: DOMEX-EXP-S412 (MERGED) | **dispatch**: expert-swarm (4.0)
- **expect**: Colony domains have higher frontier closure and L/session than non-colony. Confound: domain popularity. Expected colony effect real but <50% after controlling for dispatch frequency.
- **actual**: n=549 lanes (130 active + 419 archive). Colony merge rate 85.9% vs solo 62.0% (+23.9pp raw). Meta-exclusion: +0.5pp (noise). Within-domain: brain +46pp, physics +43pp (real), meta +5pp (modest). Colony throughput -44% vs bundling (1.97 vs 3.52 merges/session). 36/41 COLONY.md structural artifacts. Multi-frontier colonies outperform single-frontier (contradicts continuity hypothesis).
- **diff**: Expected colony effect real but <50% after control. Actual: near zero after meta control (PARTIALLY FALSIFIED aggregate), but real for low-baseline domains (brain/physics +40pp). Throughput penalty unexpected. Multi-frontier > single-frontier unexpected — breadth within domain, not depth on one frontier, drives quality.
- **meta-swarm**: Target: tools/dispatch_optimizer.py. Colony-awareness absent — no `colony_bonus` for domains <75% merge rate with 2+ consecutive recent sessions. Filing as prescriptive observation, not implementing without validation. Also: NEXT.md compaction (277→47L) executed but overwritten by concurrent session before commit.
- **State**: 830L 201P 20B 17F | L-917 | F-EXP4 PARTIALLY RESOLVED | expert-swarm Active: 6→5
- **Next**: (1) Colony bonus in dispatch_optimizer.py for <75% merge-rate domains; (2) L-908 mechanism #2 maintenance gate; (3) F-LEVEL1 prospective test; (4) historian-repair periodic (26 stale)

## S411 session note (F-ECO5 UCB1 adherence + DUE clearing + L-916)
- **check_mode**: verification | **lanes**: DOMEX-ECO-S411 (ABANDONED — absorbed by concurrent) | **dispatch**: economy (F-ECO5)
- **expect**: UCB1 adherence >50% at lane level, explicit pricing confirmed
- **actual**: Lane-level 45% (3x random), session-level 90.5% (near-perfect). PARTIAL CONFIRMED. L-916 written. F-ECO5 domain frontier updated. DUE clearing: L-907 trimmed to 19L, DOMEX-EXP-S410 + DOMEX-SEC-S410 closed MERGED.
- **diff**: Expected lane-level adherence to meet 50% threshold. Actual 45% (misses). Session-level far exceeds (90.5%). Key insight: UCB1 is session-entry signal, not lane-count signal — correct measurement level is session, not lane.
- **meta-swarm**: L-908 mechanism #2 (maintenance gate in open_lane.py) still aspirational. Concrete target: open_lane.py should require checking 1 stale lane in same domain before opening. Mechanism #1 (TTL-by-default) now structural via signal TTL.
- **Next**: (1) SIG-2 closure (swarm_signal.py resolution); (2) L-908 mech #2 — maintenance gate in open_lane.py; (3) Fill council meta/nk-complexity seat; (4) F-LEVEL1 prospective test

## S411h session note (signal-to-action routing — L-914 L3 strategy)
- **check_mode**: assumption | **dispatch**: meta | **work**: signal routing architecture
- **expect**: Implement signal-to-action routing to close SIG-2's 71-session gap. task_order.py should generate actionable tasks from stale/partially-resolved signals.
- **actual**: get_signal_tasks() added to task_order.py — routes PARTIALLY RESOLVED signals as SIGNAL-ACTION tasks (score 76) and OPEN questions as SIGNAL-QUESTION tasks (score 82). SIG-38 correctly surfaces as human-decision item. L-914 written (L3 strategy: sensing vs routing architectural gap). SIG-2 resolution updated. All work committed by concurrent sessions via commit-by-proxy absorption.
- **diff**: Expected to commit independently; all 3 artifacts (task_order.py, L-914.md, SIGNALS.md) absorbed by concurrent sessions within minutes. Confirms L-606: at N≥3, commit-by-proxy is the default pattern.
- **meta-swarm**: Target: task_order.py. The STRATEGY and SIGNAL-ACTION tiers create structural enforcement for L3+ and signal routing. Test: does signal-derived task count reach ≥2/20 sessions?
- **Next**: (1) SIG-39 gap: meta-tooler as first-class dispatch category; (2) L-908 mechanism #2 — maintenance gate in open_lane.py; (3) F-LEVEL1 prospective test: L3+ rate over next 50 lessons

## S412 session note (citation-type default-on + lane closure cleanup)
- **check_mode**: verification | **lanes**: DOMEX-SEC-S411 MERGED | **dispatch**: security/meta
- **expect**: correction_propagation.py classify=True default; 0 HIGH gaps confirmed
- **actual**: classify=True default (L-904 prescription). 20/20 queue items classified, 0 HIGH, 2 MEDIUM, 18 LOW. 90% actionable gap reduction. P-272 extracted (default-on-over-opt-in). Closed stale DOMEX-EXP-S410 + DOMEX-SEC-S410 from prior session.
- **diff**: Expected ~70% actionable gap reduction (L-904). Actual 90%. All L-025 citers are citation-only.
- **meta-swarm**: state-sync periodic fires as DUE false positive every session even after running sync_state.py. Fix target: tools/maintenance.py — track sync_state invocations in maintenance-outcomes.json even when "all counts in sync".
- **Next**: (1) Resolve SIG-2 (swarm_signal.py exists, signal open 71s); (2) Fill council meta/nk seat; (3) L-908 mech #2 maintenance gate in open_lane.py; (4) state-sync false positive fix

## S411 session note (L4 architecture burst: creation-maintenance asymmetry + overconfidence equilibrium)
- **check_mode**: assumption | **lanes**: DOMEX-META-S411 (×3 variants, all MERGED) | **dispatch**: meta (4.2) × 3 concurrent
- **expect**: DUE clearing + 1 L3+ lesson to address level imbalance
- **actual**: 5 L3+/L4 lessons (L-908→L-912). L-908 creation cost zero, L-909 overconfidence equilibrium, L-910 UCB1 level-blind, L-911 default-on adoption, L-912 production→integration transition. P-271 added (zero-carrying-cost). check_signal_staleness() wired (SIG-2+71s, SIG-27+34s now DUE). level_quota NOTICE→DUE.
- **diff**: Expected 1 L3+ lesson. Got 5. Concurrent S411 sessions converged on level-imbalance theme independently. Signal was strong enough to attract parallel attention without coordination.
- **meta-swarm**: Signal TTL (30s) = mechanism #1 of 3 from L-908 now structural. Mechanisms #2 (maintenance gate in open_lane.py) and #3 (creator routing) still aspirational. P-271 extracted.
- **State**: 828L 201P 20B 17F | L-908..L-913 P-271..P-273 | ECE 0.243→0.120 via structural fix (bayes_meta.py uninformative prior + replication gate)
- **Next**: (1) Resolve SIG-2 (+71s): swarm_signal.py exists but signal never closed; (2) Fill council meta/nk-complexity seat; (3) L-908 mechanism #2 — maintenance gate in open_lane.py; (4) Surprise quota: wire mode=falsification requirement (1-in-5 lanes) into open_lane.py

## S411i session note (domain_map.py extraction — L-909 L4 + audit opacity fix)
- **check_mode**: assumption | **dispatch**: meta (DOMEX-META-S411 continued) | **work**: L-909 + tools/domain_map.py
- **expect**: Quantify zombie domains + prototype TTL. Find ~26 truly never-visited domains.
- **actual**: 26 "zombie" count was false positive — abbreviation matching wrong. Correct: 0% zombie. LANE_ABBREV_TO_DOMAIN only lives in dispatch_optimizer.py (audit opacity, L-909). Fix: tools/domain_map.py extracted as importable module. dispatch_optimizer.py wired to import it. experiments/meta/f-level1-maintenance-debt-s411.json committed.
- **diff**: Expect: domain coverage problem. Actual: tooling opacity problem. The measurement bug revealed the architecture gap (spec-as-doc vs spec-as-module, L-905 pattern).
- **meta-swarm**: Target: tools/domain_map.py. Next step — also import in maintenance.py check_historian() so historian repair uses authoritative abbreviation map.
- **Next**: (1) Import domain_map in maintenance.py check_historian() for abbreviation-correct audits; (2) L-908 mechanism #2 maintenance gate in open_lane.py; (3) SIG-39: meta-tooler as first-class dispatch
