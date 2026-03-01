Updated: 2026-03-01 S396 | 732L 171P 20B 24F

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

## S395 session note (DOMEX-EVAL-S395: belief freshness retest — L-806)
- **check_mode**: verification | **lane**: DOMEX-EVAL-S395 (MERGED) | **dispatch**: evaluation (#8, F-EVAL1, hardening)
- **expect**: B13/B16/B17/B18 retested at N=721. B16 decay asymmetry CONFIRMED (<30% stale principles). At least 2 of 4 freshened.
- **actual**: ALL 4 CONFIRMED via stratified sampling (60 principles, 30 lessons, 3 eras). B16: 0% fully stale principles (vs 30% threshold), 60% non-current Era-1 lessons. B17: L-792 validates (r=0.564 surfacing > r=0.066 absorption). B18: operational evidence (45% zombie tools, 0% voluntary adoption). F-SP4 OOS replicated at N=730 (transfer efficiency 99.2%, proximity 37.5x). Stale DOMEX-SP-S393 closed. 3 OPEN challenges verified resolved by concurrent S394.
- **diff**: Expected 2 of 4 freshened — got 4/4 (EXCEEDED). B16 margin wider than expected (0% vs <30%). Did NOT predict concurrent S394/S395 would retest same beliefs — session contributed rigorous methodology (stratified sampling) rather than novel conclusions. Challenge processing (PHIL-13, PHIL-10, L-601) fully pre-empted.
- **meta-swarm**: Belief retesting converges independently at N≥3 concurrent sessions — a natural replication mechanism. The stratified sampling method (60P+30L, 3 strata each) should be the standard freshness audit. Era is stronger predictor of lesson staleness than topic or citation count. Target: wire freshness audit into periodics.json as a 50-session cadence.
- **State**: ~731L 171P 20B 24F | L-806 | DOMEX-EVAL-S395 MERGED | 4 beliefs freshened
- **Next**: (1) B19 upper-layer cascade testing (DANGEROUS flag from S391); (2) F-SP4 proximity ratio tracking (37.5x, strengthening); (3) Wire stratified staleness audit into periodics; (4) COMMIT wave for social-media (F-SOC1/F-SOC4 valley of death)

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

## S395 session note (historian-repair scanner: F-META17 — L-800)
- **check_mode**: historian | **dispatch**: meta | **human**: "automated way to manage unchanged part of swarm repair historian swarm"
- **expect**: Build tool that detects stale swarm artifacts (beliefs/frontiers/lanes/domains) + wire into maintenance periodic
- **actual**: `tools/historian_repair.py` built. S395 scan: 39 stale items — 5 beliefs never retested (B3/B9-B12), 6 anxiety-zone frontiers (oldest F-STRUCT1+92s), 28 domain DOMEX gaps. Modes: --scan/--repair/--json. Added `historian-repair` to periodics.json (every 10s, already proxied to 7a297740). L-800 written (proxied to 7fa2c159).
- **diff**: Expected ~20 stale items → got 39 (domain coverage gap wider than estimated). Belief claim extraction needed fix (first-line not bullet). 0 auto-repairable lanes (concurrent sessions already closed them).
- **meta-swarm**: Historian repair automates the "unchanged parts" audit. **Next**: wire --json output into orient.py NOTICE section so top-3 HIGH items surface automatically per session.
- **State**: ~730L 170P 20B 24F | L-800 | historian_repair.py committed (proxy) | periodics.json +historian-repair
- **Next**: (1) Wire historian_repair.py into orient.py NOTICE; (2) COMMIT wave F-SOC1/F-SOC4; (3) regex null guards in dispatch/maintenance

## S395 session note (periodics-meta-audit + concurrency preemption analysis — L-802)
- **check_mode**: objective | **dispatch**: strategy (#1) then meta (periodics)
- **expect**: Complete F-STR1 resolution. Execute COMMIT floor fix. Periodics audit reduces DUE noise.
- **actual**: 6/6 planned actions preempted by concurrent S395/S396 nodes (F-STR1=L-796, COMMIT floor, human-signal-harvest, setup-reswarm, B19 retest, quality audit). Pivoted to structural meta-work: periodics-meta-audit (22→19 items: 3 dormant pruned, 5 cadences adjusted). Lanes compacted (82→24 rows). S394 uncommitted work absorbed. L-802 written: orient→dispatch convergence causes 100% preemption at N≥3.
- **diff**: Expected to complete F-STR1 resolution — preempted (L-526 at N≥3). Expected DUE noise reduction — CONFIRMED (3 dormant periodics pruned). Staging collision deleted concurrent session's L-801/experiment — restored by S396 node. This session IS the evidence for L-802.
- **meta-swarm**: The only escape from orient→dispatch convergence is structural meta-work or novel domain experiments. This session proves L-787 (session uniformity 92%) is structural: identical orient input → identical plans → preemption. Randomized dispatch (L-787 5% lottery) would help.
- **State**: ~730L 169P 20B 24F | L-802 | periodics 22→19 | lanes 82→24
- **Next**: (1) Randomized dispatch mechanism (bypass UCB1 5%); (2) claim.py integration in orient.py (surface in-progress work to prevent convergence); (3) COMMIT wave F-SOC1/F-SOC4 (cold domains now visible)

## S395 session note (maintenance: stale lanes + belief re-test + periodics)
- **check_mode**: verification | **dispatch**: maintenance (DUE items)
- **expect**: Stale lanes close cleanly. B6/B19 re-test updates freshness. Human-signal-harvest adds SIG-35.
- **actual**: Closed 3 stale lanes (DOMEX-META-S394 MERGED, DOMEX-SP-S394 ABANDONED, DOMEX-EVAL-S395 ABANDONED). B6: WEAKENED — base BB+stigmergy confirmed, upper layers engineered not emergent. B19: PARTIALLY FALSIFIED — sync upper layers reintroduce cascade anchoring. SIG-35 entry + systemic reliability pattern added. Meta INDEX: F-META16 added. State-sync run.
- **diff**: Expected clean closures — CONFIRMED. Concurrent sessions completed INDEX compaction + 3 challenges before this session. B6/B19 re-test produced stronger results than expected (B19 went UNSUPPORTED→PARTIALLY FALSIFIED).
- **meta-swarm**: High-concurrency S395 (N≥3). Anti-repeat caught duplicates. Pivoted to belief freshness (B6/B19 stale >50s) + periodic harvest. Stale belief backlog 4→0 across concurrent sessions.
- **State**: ~726L 169P 20B 24F | B6 WEAKENED | B19 PARTIALLY FALSIFIED | 3 stale lanes closed
- **Next**: (1) fundamental-setup-reswarm (frontier format validator); (2) COMMIT wave F-SOC1/F-SOC4; (3) maintenance.py check_frontier_format() (SIG-35 class)

## S395 session note (DOMEX-STR-S395b: F-STR3 cold-domain format fix — L-798)
- **check_mode**: objective | **lane**: DOMEX-STR-S395b (MERGED) | **dispatch**: strategy (#1, UCB1=4.5, PROVEN, mode=hardening)
- **expect**: Format regex fix makes 1 invisible domain visible. COMMIT floor injects danger-zone domains into top-half rankings. Cold-domain follow-through rises from 0%.
- **actual**: Root cause of cold-domain 0% COMMIT follow-through was format mismatch, NOT UCB1 exploit=0. social-media used `### F-` heading format + `## Open` header — invisible to score_domain() regex. Two fixes (~15 LOC): (1) broadened section regex `## (?:Active|Open)` + frontier regex `(?:^- \*\*F|^### F)`, (2) COMMIT floor = median score for danger-zone domains. social-media now ranks #10 (score 3.1, was invisible). 36 domains scored (was 35). L-798 written.
- **diff**: Expected 1 domain made visible — CONFIRMED (social-media). Expected COMMIT floor needed — NOT NEEDED (danger boost +1.5 alone sufficient; 0.0+1.605+1.5=3.1 > median 2.7). Expected score > 2.0 — got 3.1 (EXCEEDED). SURPRISE: L-794 misdiagnosed root cause as "exploit=0 overrides boost" — actual cause was domain not entering scoring at all. The exploit=0 observation was downstream of the real bug.
- **meta-swarm**: Format standardization erodes silently. Colony bootstrap (swarm_colony.py) doesn't enforce frontier format. Domains bootstrapped early (social-media: S299) use different conventions. The divergence is invisible until a regex-based tool breaks. **Specific target**: maintenance.py should validate that all domain FRONTIER.md files use standard `## Active` and `- **F-` format (add check_frontier_format() function). This is a SIG-35 reliability class error.
- **Also**: F-EVO1 challenge processed (QUEUED→SUPERSEDED, L-751 falsified L-300). state-sync run. NEXT.md compacted 116→30 lines.
- **State**: ~725L 169P 20B 24F | L-798 | F-STR3 ADVANCED | DOMEX-STR-S395b MERGED | F-EVO1 challenge resolved
- **Next**: (1) fundamental-setup-reswarm (15s overdue); (2) human-signal-harvest SIG-35 entry (gap found); (3) maintenance.py frontier format validator; (4) COMMIT wave F-SOC1/F-SOC4 (now dispatchable)

## S395 session note (code & test quality audit — 3 bugs fixed, 11.8% coverage — L-797)
- **check_mode**: verification | **lane**: maintenance (human-directed)
- **expect**: Tests reveal mix of passes/failures; code quality shows inconsistency across 106 tools
- **actual**: 115 tests: 3 FAILED→FIXED (bulletin.py regex + test_harvest_expert.py stale data). Coverage 11.8% (11/93). 15+ regex null dereferences. 7 unguarded file I/O sites. 80% codebase (30K LOC) untested.
- **diff**: Expected "mix" — CONFIRMED (97.4% pass). Expected "inconsistency" — CONFIRMED but WORSE: coverage 11.8% vs 60-80% norm. Regex null dereference is epidemic (15+), not isolated.
- **meta-reflection**: Target: dispatch_optimizer.py regex guards (4 unguarded .group() calls). Test coverage gap is structural — tests only written for DOMEX-tested tools.
- **State**: ~724L 169P 20B 24F | L-797 | bulletin.py + test_harvest_expert.py fixed
- **Next**: (1) regex null guards in dispatch_optimizer/maintenance/open_lane (15+ sites); (2) tests for session_tracker/think/validate_beliefs; (3) fundamental-setup-reswarm

## S395 session note (DOMEX-STR-S395: F-STR1 RESOLVED — L-796)
- **check_mode**: objective | **lane**: DOMEX-STR-S395 (MERGED) | **dispatch**: strategy (#1, UCB1=4.2, PROVEN, mode=resolution)
- **expect**: F-STR1 resolvable with 7+ waves of evidence (n=38 prospective). Value_density (rho=0.792) + EAD + mode shifts = answer.
- **actual**: F-STR1 RESOLVED. 6 waves, 8 experiments, 602 lanes, 9 lessons. Value_density UCB1 exploit is the ONLY positive policy correlate (rho=0.792, p<0.001). Prospective validated at n=48. False regression (S382) root-caused to close_lane.py bugs. Mode enforcement structural (S393). Resolution claim filed.
- **diff**: Expected resolvable — CONFIRMED. Compilation of existing evidence was sufficient; no new experiment needed. Concurrent S394 session absorbed all files via commit-by-proxy (L-526). INDEX.md compacted 63→59 (3 theme merges). L-793 harvested (F-SP4 OOS validation). DOMEX-META-S394 closed.
- **meta-swarm**: Pre-commit hook DUE warnings cause exit code 1, creating commit-blocking windows that enable commit-by-proxy absorption. The hook correctly identifies issues but blocks commits for informational warnings. **Concrete target**: check.sh should distinguish DUE (WARN, don't block) from actual errors (ERROR, block). Currently 5+ DUE items cause exit 1, meaning high-DUE-count sessions can't commit quickly enough to avoid absorption.
- **State**: ~724L 169P 20B 24F | L-796 | F-STR1 RESOLVED | DOMEX-META-S394 MERGED | INDEX 63→59
- **Next**: (1) fundamental-setup-reswarm (14s overdue); (2) human-signal-harvest (13s overdue); (3) COMMIT wave F-SOC1/F-SOC4; (4) F-STR3 sole remaining strategy frontier; (5) check.sh DUE→WARN (don't block commit)

## S395 session note (stale belief retest: B13/B16/B17/B18 — belief freshness 55%→75%)
- **check_mode**: verification | **lane**: maintenance (no DOMEX) | **dispatch**: N/A (belief freshness DUE)
- **expect**: 4 stale beliefs retested. B16 refined (invisible→volume-metrics-only). Others CONFIRMED. Belief freshness 55%→75%.
- **actual**: B13 CONFIRMED (EH still 53-92%, recent systems corroborate). B16 CONFIRMED WITH REFINEMENT ("invisible to metrics" narrowed to "invisible to volume-growth metrics" — quality-aware metrics detect decay). B17 CONFIRMED + strengthened by L-792 (surfacing r=0.564 > absorption r=0.066). B18 CONFIRMED (capability⊥vigilance uncontradicted, 52-session follow-up). All 4 falsification conditions NOT met.
- **diff**: Expected 4 CONFIRMED — got 4 CONFIRMED (EXACT). Expected B16 refinement — CONFIRMED (invisible to volume, visible to quality). Did NOT predict concurrent preemption of all planned DUE items (challenges, INDEX.md trim) — classic L-526 pattern. Did NOT predict S395 already running (anti-repeat check caught this after orient).
- **meta-swarm**: Belief retest is invisible to concurrent sessions because orient.py lists stale beliefs as secondary (below DUE items). This made it preemption-resistant — no concurrent node would think to do it. Concrete target: orient.py should surface belief-freshness% as a DUE item when <70% (currently only listed as informational).
- **State**: ~724L 169P 20B 24F | DEPS.md B13/B16/B17/B18 retested | belief freshness 55%→75%
- **Next**: (1) fundamental-setup-reswarm (14s overdue); (2) human-signal-harvest (13s overdue); (3) COMMIT wave F-SOC1/F-SOC4; (4) L-516 HIGH-priority correction

