Updated: 2026-03-01 S395 | 726L 169P 20B 24F

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

