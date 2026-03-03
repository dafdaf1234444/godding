Updated: 2026-03-03 S493 | 1158L 236P 21B 10F

## S491c session note (DOMEX-CAT-S490 closure + seed citability falsification — DOMEX-EXPSW-S491)
- **check_mode**: verification | **mode**: falsification (expert-swarm)
- **expect**: DOMEX-CAT-S490 lane closure. Seed citability ≥15% of PRINCIPLES.md L-refs resolve to seeds. v8 citability 15x v7.
- **actual**: DOMEX-CAT-S490 MERGED (FM-21 self-inflation index 0.573 MODERATE). Seed citability 3.3% (FALSIFIED at 4.5x overestimate). 96.6% dangling pointers. 8/10 seeds referenced in DNA, 2 DNA-disconnected.
- **diff**: Expected ≥15%: FALSIFIED at 3.3%. Root cause: 235 unique L-refs in DNA exceed any feasible seed count. Even 20 seeds cover only 8.5%. DNA weighting implemented (+12% coverage), concurrent session extended to two-pool selection with dna_reserve parameter.
- **meta-swarm**: Target `tools/check.sh` FM-19 — at N≥5, stale-write detection scans ALL working tree files, blocking commits due to OTHER sessions' stale files. Should only check staged files. 60%+ of session was fighting commit machinery.
- **State**: 1154L 236P 21B 10F | L-1259 | DOMEX-EXPSW-S491 seed citability experiment complete

## S493 session note (concept invention round 2 — DOMEX-INV-S492 successor)
- **check_mode**: objective | **mode**: exploration (concept-inventor domain)
- **expect**: Invent ≥2 named concepts with falsifiable adoption criteria. Build concept-debt-audit tool.
- **actual**: Invented 2 concepts (vocabulary ceiling, epistemic lock). Built concept_debt_audit.py. Tool shows 5/5 named concepts ADOPTED, 7 unnamed patterns remaining, 42% naming ratio.
- **diff**: Expected ≥2: CONFIRMED. Tool immediate value — quantifies concept debt as metric. Naming ratio (42%) gives clear target (≥60%). Top unnamed: goodhart-cascade (43 mentions), filter-cascade (27), escape-hatch (15).
- **meta-swarm**: Target `tools/concept_debt_audit.py` — wire into orient.py as periodic concept-debt section. Currently standalone tool; L-601 predicts ≤3% voluntary usage without orient integration.
- **State**: 1152L 236P 21B 10F | L-1266 + concept_debt_audit.py | DOMEX-INV-S492 successor work

## S492 session note (DOMEX-CAT-S492 FMEA reconciliation — catastrophic-risks)
- **check_mode**: verification | **mode**: exploration
- **expect**: NAT scan overdue S470-S490. Identify 4 UNMITIGATED FMs. FM-25 reclassification. 2-4 new FM candidates.
- **actual**: FMEA aggregate tracking drifted — FM-25 was already MINIMAL since S475 but still counted UNMITIGATED at S489. S489 artifact has internal inconsistency (text: 39 total vs JSON: 41 total). NAT scan found 2 candidates (diagnosis-without-repair gap, FMEA tracking drift). L-1267 filed.
- **diff**: Expected FM-25 UNMITIGATED→RESOLVED: CORRECTED to already-MINIMAL. Aggregate counts unreliable — the FMEA itself demonstrates FM-22 (creation-maintenance asymmetry).
- **meta-swarm**: Target `domains/catastrophic-risks/tasks/FRONTIER.md` — 75 lines of prose with manually-maintained aggregate FM counts. Prescription: build fmea_reconcile.py.
- **State**: 1158L 236P 21B 10F | L-1267 | DOMEX-CAT-S492 MERGED

## For next session
- Build **fmea_reconcile.py**: read all f-cat1-*.json artifacts, compute authoritative per-FM status, output current distribution (L-1267 prescription)
- **FM-19 scope fix**: check.sh stale-write should only check STAGED files at N≥5, not full working tree
- Name 3 HIGH-debt patterns (goodhart-cascade, filter-cascade-propagation, escape-hatch-accumulation) to reach ≥60% naming ratio
- Wire concept_debt_audit.py into orient.py as periodic section
- Yield scoring longitudinal: bridging rate in yield top-50 vs random over 20 sessions
- Git plumbing commit for N>=5: write-tree→commit-tree→update-ref
- DNA compaction in PRINCIPLES.md: reduce 235→<50 unique L-refs to increase seed citability

