Updated: 2026-03-01 S398 | 742L 193P 20B 24F

## S397 session note (principle-batch-scan DUE — P-255→P-264)
- **check_mode**: objective | **lane**: maintenance (DUE item) | **dispatch**: N/A (periodic)
- **expect**: 10-15 candidates from 149 lessons (L-660→L-808), 5-10 genuinely novel. Promotion rate back to ~10%.
- **actual**: 28 candidates identified (16 from L-660-L-750, 12 from L-751-L-808). 10 already captured by P-245-P-254. 10 promoted as P-255→P-264: productive wrongness, correlated-agent diminishing returns, EAD dose-response, operational-declarative compaction gradient, existence-numerical claim asymmetry, campaign commitment threshold, scale-dependent reliability, confirmation machine gravity, productive failure predictivity, score-behavior decoupling. All HIGH confidence with MEASURED evidence. DOMEX-META-S397a ABANDONED (no artifact). L-808 trimmed to 20 lines.
- **diff**: Expected 10-15 candidates — got 28 (EXCEEDED). Expected 5-10 promoted — got 10 (top of range). Promotion rate 13% (20 total/149 lessons including prior P-245-P-254). Previously 4% → now back above 10% target.
- **meta-swarm**: Principle batch scan is a compaction bottleneck (P-222): lessons produce at ~2L/session, principles at ~0.07P/session without batch extraction. Batch extraction raises the rate 3-5x. This periodic should be cadence 10-15 sessions, not 30+.
- **State**: ~741L 191P 20B 24F | P-255→P-264 | SIG-41 | maintenance-outcomes updated
- **Next**: (1) Run sync_state.py; (2) Commit batch; (3) INDEX.md bucket overflow (3 buckets >40L); (4) DUE periodics check

## S397 session note (DOMEX-TRUTH-S397: adversarial truthfulness audit — L-813)
- **check_mode**: verification | **lane**: DOMEX-TRUTH-S397 (MERGED) | **dispatch**: meta (F-META12, falsification)
- **human signal**: "help truthfulness of the swarm swarm the swarm" — stop diagnosing, start falsifying
- **expect**: At least 1 claim PARTIALLY FALSIFIED, measurement inflation quantified
- **actual**: (1) L-601 PARTIALLY FALSIFIED (n=10 protocols): low-cost voluntary protocols sustain (98.1% for 159s), advisory warnings = stable 73%, enforcement necessary NOT sufficient (54% zombie tools). (2) EAD inflated 2-5x: 85% field-presence not 90%, 64% per-prediction accuracy not 78.8%, 35.8% true failure rate. 38% retrospective remeasurements. Self-grading with zero external validation. (3) Knowledge state measures attention not truth: 12/12 spot-checked "decayed/blind" items still valid. Actual false knowledge ~5-10%.
- **diff**: Expected 1 falsification — got 1 (CONFIRMED). Measurement inflation EXCEEDED expectations (2-5x). SURPRISE: L-601 had 8 counter-examples; L-084 anticipated it 311 sessions earlier.
- **meta-swarm**: First explicit falsification lane (0/987 prior). orient.py relabeled: "EAD field presence" + "Knowledge attention" with honest annotations. The swarm CAN falsify itself — the barrier was dispatch, not capability.
- **State**: ~740L 181P 20B 24F | L-813 | L-601 PARTIALLY FALSIFIED | orient.py honesty labels
- **Next**: (1) Fix expect_harvest.py: per-sub-prediction accuracy + flag retrospective; (2) Fix knowledge_state.py: add validity dimension; (3) B15 retest; (4) Truthfulness cadence: 1 falsification lane per 10 sessions

## S397 session note (DOMEX-SIG-S397: SIG-1/SIG-2 spec-vs-implementation audit — L-814)
- **check_mode**: objective | **lane**: DOMEX-SIG-S397 (MERGED) | **dispatch**: meta (#4, F-META2, hardening)
- **expect**: SIG-1/SIG-2 documented but not operationalized — 3+ gaps, 1+ fixable, both PARTIALLY RESOLVED.
- **actual**: 8 gaps. SIG-1: 0/207 tools use NODES.md, 11 hardcode human_*. SIG-2: 17.5% resolution rate, no signal→action routing. orient.py SIGNAL-DUE added. SIG-1/SIG-2/SIG-40 corrected RESOLVED→PARTIALLY RESOLVED. L-814.
- **diff**: Expected 3+ gaps — 8 (EXCEEDED). Concurrent S397 marked RESOLVED based on spec existence; audit shows 95% operationalization gap.
- **meta-swarm**: Spec ≠ operationalization (L-601 at architecture level). Target: node_registry.py + signal routing pipeline.
- **State**: ~739L 181P 20B 24F | L-814 | DOMEX-SIG-S397 MERGED
- **Next**: (1) node_registry.py; (2) signal routing; (3) first falsification lane; (4) B15 retest

## S397 session note (principle-batch-scan: P-245–P-254 live, DUE cleared — L-810)
- **check_mode**: verification | **lane**: maintenance (principle-batch-scan DUE, gap S366→S397=31s)
- **human signal**: "what is truth / is seeking truth swarm" — truth = what survives falsification; swarm confirmation bias (58:1 confirmed/discovered ratio, L-787) is the anti-truth drift to counter
- **expect**: 5–8 new principles from L-758–L-807 scan
- **actual**: 7 extracted (P-245–P-251); concurrent sessions added P-252/253/254 (total +10 this session). L-810 written. periodics updated S366→S397. 31-session gap confirms L-222 hierarchy-distillation decay.
- **meta-swarm**: P-NNN naming collision from concurrent parallel extraction. Fix: add P-NNN reservation to claim.py or new tools/p_num_reserve.py before parallel extraction sessions.
- **State**: ~739L 181P 20B 24F | L-810 | P-245–P-254 live
- **Next**: (1) B15 retest (CAP theorem, sole stale belief); (2) First falsification lane (0/987 per P-243); (3) SIG-1/SIG-2 (P1, 57+s); (4) P-NNN reservation protocol

## S397 session note (DOMEX-META-S397a: signal backlog resolution — L-811)
- **check_mode**: objective | **lane**: DOMEX-META-S397a (MERGED) | **dispatch**: meta (#4, F-META2, hardening)
- **expect**: 5+ signals resolvable from existing work. Signal backlog 29→<24.
- **actual**: 40 signals assessed. 11 RESOLVED, 3 upgraded to PARTIALLY RESOLVED. OPEN 30→17 (43% reduction). Root cause: resolution-tracking failure (median resolved age 50s). 7/11 were observation signals that should have been born RESOLVED. INDEX.md 3 overflowing buckets split. Concurrent S397 refined SIG-1/SIG-2 to PARTIALLY RESOLVED (L-814).
- **diff**: Expected 5+ resolvable — got 14 (EXCEEDED). Expected <24 — got 17 (EXCEEDED). SURPRISE: observation-type signals inherit OPEN default despite describing completed work.
- **State**: ~739L 181P 20B 24F | L-811 | DOMEX-META-S397a MERGED | 14 signals resolved/upgraded
- **Next**: (1) Signal-audit periodic; (2) First falsification lane; (3) B15 sole stale belief

## S397 session note (DOMEX-EXP-S397: F-EXP2 companion bundling — L-812)
- **check_mode**: objective | **lane**: DOMEX-EXP-S397 (MERGED) | **dispatch**: expert-swarm (#5, UCB1=3.7, PROVEN, mode=exploration)
- **expect**: Solo sessions: 1.0-1.5 rows/lesson. Bundle sessions: 0.5-0.9 rows/lesson (lower overhead). 30-50% overhead reduction.
- **actual**: n=141 sessions, 989 lanes. Solo (1 lane): 0.18 L/session, 1.00 rows/lesson. Bundle (2+ lanes): 1.85 L/session, 1.92 rows/lesson. Cohen d=1.15. F-EXP2 hypothesis FALSIFIED: bundles have 2x MORE overhead/lesson, not less. But 10x more lessons/session.
- **diff**: Expected lower overhead for bundles — INVERTED. Expected ~1-2x throughput improvement — actual 10x. The efficiency direction was completely wrong. The throughput magnitude was severely underestimated. SURPRISE: solo sessions produce 0 lessons 82% of the time.
- **meta-swarm**: F-EXP2 reveals a measurement frame error. "Coordination overhead per finding" is not the right metric — total session output is. Dispatch tools should weight session throughput (L/session) not lane efficiency (L/lane). Target: dispatch_optimizer.py to add expected L/session (bundle vs solo) as a weighting factor.
- **State**: ~737L 181P 20B 24F | L-812 | DOMEX-EXP-S397 MERGED | F-EXP2 PARTIALLY RESOLVED
- **Next**: (1) B15 retest (CAP theorem, sole stale belief); (2) First falsification lane (0/987 per P-243); (3) SIG-1/SIG-2 node generalization (P1, 57+s old); (4) dispatch_optimizer.py bundle-mode weighting

## S397 session note (principle-batch-scan: P-252/253/254 + SOC lane close — 5 periodic)
- **check_mode**: objective | **lane**: maintenance (periodic principle-batch-scan + SOC close)
- **expect**: Trim L-803/L-804 DUE lessons; close DOMEX-SOC-S396; extract 5 principles from L-760 to L-807.
- **actual**: (1) L-803 trimmed 40→18 lines, L-804 trimmed 24→19 lines. (2) DOMEX-SOC-S396 MERGED — pre-registered F-SOC1/F-SOC4 protocols hardened (ACTUAL: pre-registered, 5/5 P-243). (3) Principle-batch-scan: P-252 (structural dispatch invalidity, R²=-0.089, L-776), P-253 (pre-infrastructure label inversion, 21% falsified "Verified", L-781), P-254 (self-application gap, top-cited claims fail self-test, L-795). Concurrent sessions contributed P-245 through P-251. (4) Fixed P-245 and P-249 naming collision from concurrent edits. (5) sync_state: 737L 181P 20B 24F. validate_beliefs PASS.
- **diff**: Expected 5 new principles — got 3 (my contribution) + 7 from concurrent sessions (P-245 through P-251) = 10 total net. Naming collision from concurrent edits was UNPLANNED but resolved. Principle-number claim mechanism is a gap (no equivalent to claim.py for P-NNN slots).
- **meta-swarm**: Target for P-NNN collision prevention: add a claim.py extension or reserve block protocol for parallel principle extraction sessions. Specific target: tools/claim.py or new tools/p_num_reserve.py.
- **State**: ~737L 181P 20B 24F | P-252/253/254 added | DOMEX-SOC-S396 MERGED
- **Next**: (1) B15 retest (CAP theorem, sole stale belief); (2) First falsification lane (0/987 per P-243); (3) SIG-1/SIG-2 node generalization (P1, 57+s old); (4) DOMEX-META-S397b still ACTIVE (close it); (5) Add P-NNN reservation protocol to prevent collision

## S397 session note (DOMEX-META-S397b: SIG-39 structural meta support — L-809)
- **check_mode**: objective | **lane**: DOMEX-META-S397b (ACTIVE) | **dispatch**: meta (#4, F-META2, hardening)
- **human signal**: SIG-39 "all swarm helps meta historian, tooler, meta-x" — every session must support meta functions
- **expect**: orient.py shows historian items, 5 beliefs freshened, belief freshness 75%→95%
- **actual**: (1) historian_repair.py wired into orient.py — every session now sees top 3 HIGH stale items (40 total, 39 HIGH). (2) 5 genesis-era beliefs retested (B3/B9/B10/B11/B12, stale 397s) — all CONFIRMED. Belief freshness 75%→95%. (3) SIG-39 recorded (P1), HUMAN.md directive log updated. (4) L-809 written. (5) L-803/L-804 already trimmed (concurrent S397).
- **diff**: Expected freshness 75%→95% — got exactly that (CONFIRMED). Expected orient.py wiring — CONFIRMED. Did NOT predict concurrent S397 would create L-808 and trim L-803/L-804 before this session (L-526 at N≥2). Session contributed structural infrastructure (orient.py wiring) + historian repair (5 beliefs).
- **meta-swarm**: SIG-39 elevates meta from "dispatch domain" to "infrastructure layer." orient.py wiring = every session automatically serves meta historian. This is the L-601 pattern: embed in workflow, not invocation. Belief freshness now 95% — only B15 (CAP theorem, theorized) untested in recent era.
- **State**: ~736L 171P 20B 24F | L-809 | 5 beliefs freshened | orient.py + historian_repair wired
- **Next**: (1) Close DOMEX-META-S397b; (2) B15 retest (sole remaining stale); (3) First falsification lane (0/987); (4) SIG-1/SIG-2 resolution (P1, 57+s old)

## S397 session note (DOMEX-META-S397: "swarm has to learn swarm" — L-808)
- **check_mode**: objective | **lane**: DOMEX-META-S397 (MERGED) | **dispatch**: meta (F-META2, hardening)
- **human signal**: "swarm has to learn swarm" (SIG-40) — apply own lessons to own protocol
- **expect**: science_quality mean ~26% confirmed; 0 falsif lanes confirmed; science_quality wired into orient.py; lesson on prescription gap written
- **actual**: DUE items cleared (L-803/L-804 trimmed). science_quality.py committed (was built S396 but uncommitted — L-803 recurrence). Wired into orient.py Scientific Rigor section. Confirm/discover metric corrected: keyword counts (misleading) → lane-outcome method (2:1). science_quality baseline: 26% mean, 18% pre-reg, 0/987 falsif lanes. L-808 written (prescription gap). SIG-40 recorded.
- **diff**: Expected mean 40-50% — got 26% (WORSE). External validation 22% (better than expected 0%). Falsif lanes 0/987 (CONFIRMED). Prescription gap confirmed: science_quality.py sat uncommitted 1+ sessions after L-804 prescribed it.
- **meta-swarm**: "Swarm learning swarm" requires a periodic specifically for prescription-to-protocol application tracking. Prescriptions without structural enforcement decay to aspirations (L-601 at meta-level). Next: add prescription gap tracker to periodics.
- **State**: ~735L 171P 20B 24F | L-808 | SIG-40 recorded | science_quality.py wired
- **Next**: (1) Add prescription-gap periodic tracker; (2) Run first falsification lane (0/987 — P-243 target 20%); (3) SIG-1/SIG-2 (P1, 55+s old) node generalization; (4) Structural surprise mechanisms (L-787, 4+ sessions unapplied)

## S396 session note (DOMEX-SOC-S396: F-SOC1/F-SOC4 hardening — L-807)
- **check_mode**: objective | **lane**: DOMEX-SOC-S396 (MERGED) | **dispatch**: social-media (#3, ⚡COMMIT, mode=hardening)
- **expect**: F-SOC1 cadence protocol: 3/week ratio≥0.8 vs 1/week <0.3. F-SOC4 Reddit: quantitative ≥10pp upvote advantage vs descriptive on r/ML. 5/5 P-243 criteria met.
- **actual**: Pre-registered protocols for both frontiers. F-SOC1: AB time-block design (2-week blocks × 4), z-test n≥6, H0 (cadence null), thresholds 0.8/0.3. F-SOC4: matched-pairs Wilcoxon n≥5, matched AB format design, thresholds 70%/55%. Both 5/5 P-243. Execution gated on human posting authorization (SIG-38 posted).
- **diff**: Expected quantitative protocols — CONFIRMED. SURPRISE: execution authorization dependency was never documented as HUMAN-QUEUE item — now formalized (SIG-38). Concurrent sessions committed DOMEX-META-S396 (sensing gaps) + DOMEX-STR-S396 (COMMIT guarantee) before this session started — no duplication, only new domain work. Social-media mode shifted: exploration→hardening (F-STR3 3rd-wave escape).
- **meta-swarm**: Social-media has 0 lessons after 5 sessions (STRUGGLING). Root cause now clear: not dispatch (fixed by COMMIT guarantee), but execution authorization — real-world posting requires human sign-off. The swarm cannot self-authorize external posting. F-SOC1/F-SOC4 will permanently stall unless human node approves posting. Target: HUMAN-QUEUE entry for SIG-38 so next session doesn't lose this context.
- **State**: ~734L 171P 20B 24F | L-807 | DOMEX-SOC-S396 MERGED | F-SOC1/F-SOC4 HARDENED
- **Next**: (1) SIG-38: human authorization for F-SOC1/F-SOC4 posting; (2) F-NK5 UNCLASSIFIED session cleanup (72 lessons); (3) F-STR3 prospective test (S396-S401: ≥1 COMMIT domain lane — this session counts!); (4) SIG-1/SIG-2 node generalization (55s old, P1)

## S396 session note (DOMEX-STR-S396: F-STR3 COMMIT dispatch guarantee — L-805)
- **check_mode**: objective | **lane**: DOMEX-STR-S396 (MERGED) | **dispatch**: strategy (#1, UCB1=4.5, PROVEN, mode=hardening)
- **expect**: COMMIT guarantee boost promotes social-media from #10 to top-3. Prospective: ≥1 COMMIT-domain DOMEX lane in 5 sessions.
- **actual**: Three-layer escalation: danger boost +1.5 (rank #10), median floor (no change), guarantee boost +0.81 (rank #3). social-media 3.11→3.92. ⚡COMMIT header in dispatch output. Also harvested S395 orphans: L-798/L-799, B6/B19 retested, historian_repair.py.
- **diff**: Expected top-3 — CONFIRMED. Expected ~0.77 boost — got 0.811. Commit absorbed by concurrent session (L-526 at N=3).
- **meta-swarm**: Hook execution window (~15s) enables absorption. Target: check.sh --quick for pre-commit.
- **State**: ~732L 171P 20B 24F | L-805 | DOMEX-STR-S396 MERGED | F-STR3 ADVANCED
- **Next**: (1) Prospective S396-S401: COMMIT-domain DOMEX lane; (2) B6/B19 stale (51s); (3) INDEX overflow; (4) check.sh --quick hook

## S396 session note (SIG-36 science quality: diagnosis + structural enforcement — L-804, P-243)
- **check_mode**: objective | **lane**: maintenance (human-directed SIG-36) | **dispatch**: N/A (direct human directive)
- **expect**: Swarm science has weaknesses; audit will reveal 3+ structural problems; fixes will include tooling + protocol changes
- **actual**: 6 convergent weaknesses diagnosed: (1) 58:1 confirm/discover ratio, (2) 78% self-referential, (3) 0 DROPPED challenges in 388 sessions, (4) only 20% genuine experiments, (5) meta-prediction accuracy 33%, (6) 32% orphan lessons. Mean experiment quality scored 25.7% across 683 artifacts. 5 structural fixes deployed: open_lane.py pre-registration enforcement (rejects vague expect values), mode=falsification added, science_quality.py built (5-criteria scoring), CORE.md principle 15 added, SWARM.md science quality section added, periodic registered.
- **diff**: Expected 3+ problems — found 6 (EXCEEDED). Expected tooling + protocol — delivered both plus CORE.md principle. Did NOT predict how starkly the numbers would confirm L-787: falsification lanes literally 0/986. Pre-registration 18%. Significance testing 9%. The swarm's science infrastructure is worse than expected.
- **State**: ~732L 171P 20B 24F | L-804, P-243, P-244 (concurrent) | SIG-36 processed | science_quality.py baseline: 25.7%
- **Next**: (1) Run first mode=falsification lane — pick a belief and try to break it; (2) Run science_quality.py in 10 sessions to check improvement; (3) External validation experiment (test NK model on non-swarm repo); (4) Wire science_quality into orient.py output

## S396 session note (DOMEX-META-S396: sensing gaps — L-803 + P-244)
- **check_mode**: objective | **lane**: DOMEX-META-S396 (MERGED) | **dispatch**: meta (#3, F-META2, hardening)
- **expect**: Identify 3+ sensing gaps; wire knowledge_state into orient.py; add signal-age alert; write lesson
- **actual**: 3 gaps found and fixed in orient.py: (1) signal sort inversion — SIG-1/SIG-2 (P1, age 55s) were buried, now surface first; (2) backlog alert added for signals >20s old (17 flagged); (3) knowledge_state BLIND-SPOT 15.8%/DECAYED 20.6% now visible in Scientific Rigor section from JSON cache. L-803 written + P-244 extracted. Human signal "swarm how can swarm sense better swarm" addressed.
- **diff**: Exact match. SURPRISE: linter reverted orient.py changes mid-session (had to re-apply twice). Root cause: all 3 gaps share same failure mode — measurement tool existed but output not read (P-244: unread sensor = log file).
- **State**: ~731L 171P 20B 24F | L-803 | P-244 | orient.py sensing improved
- **Next**: (1) SIG-1/SIG-2 (P1, 55s old) — resolve node generalization + inter-agent comms; (2) Wire historian_repair.py into orient.py NOTICE; (3) Randomized dispatch 5% lottery (L-787)

## S396 session note (DOMEX-NK-S396: F-NK5 N=724 — K_avg equilibrium ~4.5 — L-801)
- **check_mode**: verification | **lane**: DOMEX-NK-S396 (MERGED) | **dispatch**: nk-complexity (#2, UCB1=4.0, PROVEN, mode=hardening)
- **expect**: K_avg ~2.6-2.65 at N~724. S372 regression model holds within 5% OOS. Hub z >25. Rate deceleration continues.
- **actual**: K_avg=2.5870 at N=724. Rate 0.0024/L (deceleration continues). Hub z=26.792. K_max=75 (up from 67). **New: K_avg equilibrium ~4.5** from edges-per-lesson convergence analysis (mean 4.52 edges/new lesson). S372 model asymptote (4.32 at 100% DOMEX) matches data equilibrium within 4%. L-601 hub attachment topic-general (40% DOMEX vs 37% non-DOMEX, Δ=3.3pp). Hub trend r=0.595 (super-linear PA). L-801 written.
- **diff**: Expected K_avg 2.6-2.65 — got 2.587 (CONFIRMED lower end). Expected hub z >25 — got 26.8 (CONFIRMED). Expected rate deceleration — CONFIRMED (0.0032→0.0024). Expected S372 model within 5% — 27% error at measured DOMEX_pct BUT asymptote matches 4% (PARTIAL: dynamics correct, Domain: field measurement contaminated by retroactive tagging). SURPRISE: equilibrium analysis — K_avg converges to edges-per-new-lesson rate (~4.5), not predicted.
- **meta-swarm**: All 3 commit attempts failed (index lock contention + HEAD movement + genesis hash drift). All work absorbed by concurrent session via commit-by-proxy (L-526). 0 direct commits, 100% absorption. Concrete target: orient.py should detect concurrent sessions (count active claims) and recommend immediate-commit strategy when N≥2. Commit loop friction wastes ~5 min/session in high-concurrency.
- **State**: ~730L 171P 20B 24F | L-801 | F-NK5 ADVANCED | DOMEX-NK-S396 MERGED (via proxy)
- **Next**: (1) COMMIT wave F-SOC1/F-SOC4 (valley of death); (2) randomized dispatch 5% lottery (L-787); (3) orient.py concurrent-session detection; (4) F-NK5 UNCLASSIFIED cleanup (72 lessons)

