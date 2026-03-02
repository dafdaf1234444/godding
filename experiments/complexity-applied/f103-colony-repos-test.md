# F103: Swarm Colony Test — dutch + complexity_ising_idea
**Session**: 54 | **Date**: 2026-02-27 | **Status**: RESOLVED — pattern confirmed third time

## Setup
Colony of 3 parallel agents on 2 repos. No prior analysis for `dutch`. Prior S52 analysis exists for `complexity_ising_idea`.

| Agent | Repo | Task | Wall time |
|-------|------|------|-----------|
| A1 | dutch | NK complexity | ~80s |
| A2 | dutch | EH quality | ~148s |
| A3 | complexity_ising_idea | Verify S52 claims + find new | ~196s |

Total wall time: ~196s (parallel). Sequential estimate: ~424s (2.2× speedup).

All agents ran READ-ONLY. Swarm writes only to `/swarm`. External repos are learning sources, not targets.

---

## Agent Findings

### A1: dutch NK Analysis
- **N=11, K_avg=0.636, cycles=0, composite=7.0, burden=1.1**
- Architecture: **star topology** — `dutch-speech.ts` (0 local imports, 5 dependents) + `flashcard-decks.ts` (0 imports, 2 dependents) are the leaf singletons
- cycles=0 is **structurally guaranteed**: both leaf nodes import nothing local; back-edges are impossible unless a future contributor breaks the pattern
- LOC/N = 512 (just over P-065 threshold of 500); driven by auto-generated `flashcard-decks.ts` (1888 LOC)
  - Excluding data file: LOC/N = 374 — below threshold (signal weak)
- Structural risks:
  1. `FlashcardApp.astro` at 1315 LOC — monolith component (spaced-repetition + 5 practice modes + keyboard + favorites)
  2. `dutch-speech.ts` is an undeclared singleton: 5 consumers, no interface abstraction — soft coupling risk
  3. `DUTCH_HEADERS` Set duplicated in `DutchAudio.astro` and `PageFlashcards.astro` — data-sync risk invisible to import graph

### A2: dutch EH Quality
- **8 silent catch blocks** — all localStorage-related
- **2 onerror speech swallows** (Web Speech API — deliberate UX choice)
- **31 non-null assertions (`!`)** — mostly safe (DOM set by `innerHTML=` before query), except `Say.astro:66` (data-text attribute assumed always present)
- **1 unguarded JSON.parse** in event handler (PageFlashcards.astro:260 — app-written data, low risk but no guard)
- **0 network calls** — entire architecture is synchronous + localStorage + Web Speech API
- **0 console.error** anywhere — silent failures are invisible to developers too
- **Overall: MEDIUM**
- **Critical risk**: catch blocks conflate `localStorage` unavailable WITH `JSON.parse` corruption — corrupted JSON silently destroys entire spaced-repetition history (ease, streak, review counts) with no user signal

### A3: complexity_ising_idea Verification
**Prior S52 claims vs reality:**
| Claim | Status |
|-------|--------|
| N=8 modules | WRONG — N=7 (empty __init__.py was counted) |
| K_avg=0.0, cycles=0 | CONFIRMED |
| "perfectly decoupled" | CONFIRMED |
| 13 tests in 2 files | CONFIRMED (13 test functions; 46 total assertions — "moderate" understated) |
| E(k=1) has no shuffle test | CONFIRMED (as of S52) |
| Error bars underestimated 2-3x | CONFIRMED |
| Total Correlation unreliable | CONFIRMED |

**Critical find: project already resolved before S52 ran.**
`phase1_p0_analytical_ei.py` (committed 2026-02-25, 2 days before S52) contains:
> "RESULT: DEFINITIVE NEGATIVE. No causal emergence in 2D Ising via EI ratio. Majority-vote coarse-graining DESTROYS causal structure; it never creates it."

S52 recommended writing `phase1_v6_wolff_e1.py` as next step. That file was never written — but the per-patch Wolff analysis already resolved the underlying question definitively. S52 missed 3 new experiment files (4197 lines total) committed the same day S52 ran.

**EH quality: EXCELLENT** — 0 bare excepts, proper ValueError guards, CLAUDE.md conventions followed. Better than S52 implied.

---

## Cross-Agent Synthesis (Parent Only)

**Convergent finding — dutch: structural monolith = EH risk**
- A1: `FlashcardApp.astro` is the structural monolith (1315 LOC, hidden complexity)
- A2: `FlashcardApp.astro` has 2 of the 8 catch blocks (loadStorage + saveStorage)
- Neither agent alone had the complete picture. Same bets-analyzer pattern: highest-NK component = highest-EH risk.
- P-114 further validated: cross-agent synthesis produces non-obvious risk attribution.

**Verification agent critical value (Ising): project status change**
- A3 found the project had resolved its core question — S52's "recommended next step" was answering a question already answered
- A solo agent reading S52's analysis and the project SUMMARY.md would have started on `phase1_v6_wolff_e1.py` without checking commit history
- The verification agent's value: checking repo state against swarm's prior analysis, not just repo state alone

**Domain-specific insight: web-app EH analysis requires domain-aware search**
- A2 found: standard search for "unhandled fetch rejections" would report zero issues, missing all 8 real problems
- The entire architecture avoids network calls — EH risk is exclusively localStorage/Web Speech
- Swarm's EH domain knowledge (P-104: EH is dominant failure mode) correctly pointed here; but the domain-specific manifestation is localStorage-catch conflation, not the usual async pattern

---

## F103 Verdict: RESOLVED

**Three tests, consistent pattern:**

| Test | Type | Result |
|------|------|--------|
| S52 complexity_ising_idea | Fresh, well-documented | ADDITIVE (speed + breadth) |
| S53 bets analyzer | Prior analysis with errors | TRANSFORMATIVE (3 false claims caught) |
| S54 dutch (NK+EH) | Fresh, no prior analysis | ADDITIVE (found catch conflation; single agent likely would too) |
| S54 ising (verification) | Prior swarm analysis stale | TRANSFORMATIVE (project already resolved — S52's recommendation was obsolete) |

**Final P-114 refinement:**
Swarm advantage = f(verification_need × documentation_staleness):
- **ADDITIVE**: fresh well-documented projects (speed + breadth only)
- **TRANSFORMATIVE** when: (a) prior analysis has errors/false claims, OR (b) prior analysis is stale (repo moved on) — verification agent catching what document-trusting agents miss
- The key mechanism in both transformative cases: **independent code reading vs document trust**

F103 is answered. Declare RESOLVED.

---

## F92 Data Point (Colony Size)

3-agent colony on 2 repos. Findings:
- Parallelism is near-linear (no contention — each agent on independent file sets)
- 3 agents = 2.2× wall-time speedup (consistent with prior results)
- Quality gain: cross-agent synthesis produced 2 non-obvious findings (catch conflation + stale status)
- Minimum viable colony: 2 agents (NK+EH sufficient for structural+quality; verification adds most value when prior analysis exists)
- Optimal colony size for codebase analysis: **3 agents** (NK, EH, Verification) when prior analysis exists. 2 agents (NK+EH) for fresh repos.

---

## Deliverables for User

### dutch repo
1. `FlashcardApp.astro` and `PageFlashcards.astro`: split `localStorage` catch into two handlers — one for storage unavailability, one for JSON.parse failure. On corrupt JSON: remove key, notify user, reset state.
2. `ExamPractice.astro:25`: same catch conflation — `return {}` on both errors makes debugging impossible.
3. `dutch-speech.ts:151`: add `isNaN()` guard after `parseFloat()`.
4. `PageFlashcards.astro:260`: wrap `JSON.parse(btn.dataset.cards)` in try/catch.

### complexity_ising_idea
5. The project's open question is resolved: **EI ratio is definitively an artifact** (asymmetric pooling: 144 micro vs 9 macro patches). Majority-vote coarse-graining does not reveal causal emergence in 2D Ising.
6. S52's `phase1_v6_wolff_e1.py` recommendation is second-order now. The excess entropy E(k=1) Wolff test remains valid for completeness but is no longer the critical path.
7. Update SUMMARY.md to reflect definitive-negative status.
