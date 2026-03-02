# Dutch Website Health Analysis — Swarm as Builder
**Session**: S53 | **Date**: 2026-02-27 | **Status**: Analysis complete, fixes in progress

## Repo
`<your-repos>/dutch` — TypeScript/Astro language-learning site
Live: https://dafdaf1234444.github.io/dutch/

## Agents Spawned (Analysis Phase — Parallel)
| Agent | Domain | Wall time |
|-------|--------|-----------|
| A | Architecture + NK coupling | ~119s |
| B | Code quality + browser API reliability | ~152s |
| C | Data integrity + content pipeline | ~323s |
Total wall time: ~323s. Sequential estimate: ~594s (1.8× speedup).

---

## Agent A: Architecture Findings

**NK Summary**: N=9 modules, K_avg=0.78, 0 cycles. Statically clean DAG.
**Reality**: Import graph understates risk by hiding two coupling mechanisms.

**Hub**: `dutch-speech.ts` — K_in=5, module-level side effects at import time (`initVoices()`, `visibilitychange` listener), global mutable state (`activeBtn`, `isSpeaking`, `dutchVoice`). If it fails, audio breaks on all 34 pages silently.

**Monoliths**: FlashcardApp.astro (1315 lines) + PageFlashcards.astro (996 lines) = 62% of all code in 2 nodes.

**Hidden coupling #1 — localStorage**: Both FlashcardApp and PageFlashcards hardcode `"dutch-fc-progress"` and maintain independent copies of the same JSON schema. Schema drift corrupts user progress data silently.

**Hidden coupling #2 — CSS class contract**: `dutch-audio-btn` class shared between DutchAudio, FlashcardApp, PageFlashcards as an undocumented runtime contract. Breaking it breaks DutchAudio's event delegation and PageFlashcards's text extraction.

**Duplication**: Table-scanning logic (`extractCards`, `DUTCH_HEADERS`) reimplemented independently in 3 components.

---

## Agent B: Code Quality Findings

**MEDIUM — `whenVoicesReady` never used**:
`dutch-speech.ts` exports `whenVoicesReady()` for async voice loading. FlashcardApp and PageFlashcards call `speakDutch()` directly with a bare 150ms timeout. On Firefox/Android, Dutch voice hasn't loaded — speech plays in English silently.
Fix: wrap 3 auto-play call sites in `whenVoicesReady(() => speakDutch(...))`.

**MEDIUM — No UI when Dutch voice unavailable**:
After 5s polling, if no Dutch voice found, module proceeds silently. User hears English pronunciation with no indication anything is wrong.

**MEDIUM — Audio panel silent when speechSynthesis undefined**:
Play button flashes then disables — no feedback to user.

**LOW — 15+ non-null assertions** on post-`innerHTML` DOM queries in FlashcardApp + PageFlashcards. Safe structurally (same-function template writes) but invisible to TypeScript, fragile to refactoring.

**LOW — `JSON.parse` storage without shape validation**: old saves could fail on `stats.streak` if schema evolved.

**GOOD**: No `as any` casts. Astro 5, minimal deps (2 only). keepalive timer correctly cleaned up. `requestIdleCallback` fallback correct.

---

## Agent C: Data Pipeline Findings

**HIGH — Extraction not in CI**:
`scripts/extract-flashcard-data.mjs` generates `src/data/flashcard-decks.ts` but is NOT called by `npm run build`. MDX content changes silently leave flashcard data stale. Fix: add `"prebuild": "node scripts/extract-flashcard-data.mjs"` to package.json.

**MEDIUM — CEFR deck count mismatch**:
CEFR A1 deck shows 86/298 cards (29%), CEFR A2 shows 297/549 (54%), due to cross-deck deduplication. No explanation shown to learner — deck implies completeness.

**LOW — Grammar tables extracted as flashcards**:
Pattern/example tables (adjective inflection) get extracted as vocabulary. `dutch="de rode auto"`, `english="the red car"` — technically valid Dutch but pedagogically incorrect context.

**LOW — `wordCount` props manually maintained**, not validated against table content.

**INFO**: 278 extractable rows in grammar files intentionally excluded from pipeline.

---

## Cross-Agent Convergence (highest confidence)

| Finding | Agents | Confidence |
|---------|--------|-----------|
| FlashcardApp + PageFlashcards = primary risk zone | A, B, C | HIGH |
| dutch-speech.ts = hub with hidden risks | A, B | HIGH |
| Data integrity: storage + pipeline | A (schema), C (CI) | HIGH |
| Table-scanning duplication | A (architecture), C (extraction) | MEDIUM |

---

## Fixes Implemented (Builder Phase — Parallel)
1. **prebuild hook** — `package.json`: `"prebuild": "node scripts/extract-flashcard-data.mjs"` (Fix agent 1)
2. **whenVoicesReady** — FlashcardApp.astro + PageFlashcards.astro: wrap 3 auto-play calls (Fix agent 2)
3. **hasDutchVoice() + UI warning** — dutch-speech.ts + DutchAudio.astro: show indicator when no Dutch TTS voice (Fix agent 3)

## Remaining (deferred — structural, higher risk)
- Extract `"dutch-fc-progress"` + localStorage schema to shared constants module
- Extract `dutch-audio-btn` to shared constants
- Split FlashcardApp.astro (1315 lines) into smaller modules
- Add content schema validation to content.config.ts

## Swarm Learning
This session demonstrates: **swarm-as-builder**, not just swarm-as-analyst.
Analysis phase (3 parallel agents) → synthesis (parent, cross-agent convergence) → fix phase (3 parallel agents on independent files).
Pattern is repeatable for any codebase. See L-111 if written.
