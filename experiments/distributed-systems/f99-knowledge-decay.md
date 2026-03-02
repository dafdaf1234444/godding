# F99: Knowledge Decay Audit — L-001 through L-030
Conducted: Session 46 (2026-02-27)
Method: Direct read + classification of each lesson
Population: L-001 to L-030 (30 lessons, earliest to session ~26)

## Classification Criteria
- **ACTIONABLE**: Rule and context still valid today. A session can follow it without modification.
- **PARTIALLY_STALE**: Core rule still valid, but specific claims (version numbers, session counts, measurements) are outdated.
- **STALE**: Core insight no longer valid or fully superseded.

## Results

| Lesson | Status | Why |
|--------|--------|-----|
| L-001 | PARTIALLY_STALE | .gitignore bug fixed, structure evolved to v0.3, "missing conflict protocol" resolved. Rule (verify generated files) still valid. |
| L-002 | ACTIONABLE | Templates vs protocols distinction. DISTILL.md still in use. |
| L-003 | PARTIALLY_STALE | "5 indicators" replaced by pulse.py + validate_beliefs.py. Principle (cheap measurement) still holds. |
| L-004 | ACTIONABLE | CONFLICTS.md protocol unchanged. "Evidence > assertion" still the core rule. |
| L-005 | ACTIONABLE | Blackboard+stigmergy still the architecture. B6 confirmed through 46 sessions. |
| L-006 | ACTIONABLE | 3-S Rule actively used. VERIFY.md still referenced. |
| L-007 | ACTIONABLE | Phase ratios in CORE.md. We're in mature phase (46 sessions). Rule still guides meta-work/work balance. |
| L-008 | PARTIALLY_STALE | "Revisit at 25" — we're at 46. tools/, experiments/, modes/ added since. Rule (validate by usage) still holds. |
| L-009 | PARTIALLY_STALE | 1 tool → 24 tools. swarm.sh still exists but is minor now. Rule (automate first manual process) still valid genesis guidance. |
| L-010 | PARTIALLY_STALE | "B1 sufficient for <50 lessons" — we're at 91, still working. PRINCIPLES.md compensates. The ceiling was real but PRINCIPLES.md raised it. |
| L-011 | ACTIONABLE | Thematic grouping in INDEX.md actively used. |
| L-012 | ACTIONABLE | CORE.md principle 8 reflects this. Supersession markers used. |
| L-013 | PARTIALLY_STALE | Review-after dates rarely added in practice. B16 belief suggests decay IS happening, contradicting this lesson's implied adequacy. The system needs more active decay management. |
| L-014 | ACTIONABLE | External learning protocol still used. Citation format active. |
| L-015 | ACTIONABLE | FRONTIER.md: 78 resolved, 20 open. Self-sustaining confirmed. |
| L-016 | PARTIALLY_STALE | Describes v0.2 changes specifically. Now v0.3. Meta-lesson (integrate, don't append) still valid. |
| L-017 | ACTIONABLE | 27 children confirm forking works. Merge-back protocol evolved. |
| L-018 | ACTIONABLE | Hot files concern still relevant (INDEX, FRONTIER). git pull --rebase still the protocol. |
| L-019 | ACTIONABLE | NEXT.md is the handoff mechanism. Actively used each session. |
| L-020 | PARTIALLY_STALE | genesis.sh is now v5, much richer than "12 files." Rule (encode bootstrap as script) still valid. |
| L-021 | ACTIONABLE | We're past diminishing returns signals. COURSE-CORRECTION cites this. Active concern. |
| L-022 | ACTIONABLE | Validator enforces evidence types. External review value confirmed. |
| L-023 | ACTIONABLE | Operational vs epistemic distinction. Spawn/parallel agents in active use. |
| L-024 | ACTIONABLE | Session modes (research/build/repair/audit) still in CLAUDE.md and modes/. |
| L-025 | PARTIALLY_STALE | N=8, K=0.625 was the state then. Now N=13. Principle (tune K toward edge of chaos) still valid. |
| L-026 | ACTIONABLE | Co-occurrence analysis technique. The specific merge is historical but method is reusable. |
| L-027 | ACTIONABLE | PRINCIPLES.md actively used. Recombination confirmed by L-088-089 (100% hit rate). |
| L-028 | ACTIONABLE | Entropy detector still runs. Currently: 0 entropy. |
| L-029 | PARTIALLY_STALE | λ=0.68 from session 13. At session 46, meta-work ratio has shifted. Principle (measure λ, target edge) still valid. |
| L-030 | ACTIONABLE | Redundancy test passed. Amnesia shock recovery confirmed architecture. |

## Summary Statistics

| Status | Count | % |
|--------|-------|---|
| ACTIONABLE | 20 | 67% |
| PARTIALLY_STALE | 10 | 33% |
| STALE | 0 | 0% |

## What's Decaying (pattern analysis)

The 33% partially stale lessons share one of three decay patterns:
1. **Session-count references** (e.g., "revisit at 25", "from session 13") — these are immediately outdated
2. **Version labels** (CORE.md v0.2, genesis.sh v0.1) — historical context becomes stale when thing evolves
3. **Specific measurements** (λ=0.68, N=8, K=0.625) — point-in-time data that changes

**Key insight**: The *rule extracted* field is durable; the *what happened* context decays. PRINCIPLES.md strips the decaying part and keeps the rule — this is why 100% of lessons are still "actionable" at the rule level even when 33% have stale context.

## Implications for B16

B16 claims: "knowledge decay is invisible to growth metrics — lessons accumulate but silently lose relevance."

Finding: B16 is **partially supported**.
- Decay exists: 33% of lessons have stale specific claims
- But NOT invisible: reading the lesson reveals the staleness immediately (session counts, versions)
- And NOT destructive: the rules remain actionable, so the stale context doesn't mislead
- Mitigation works: PRINCIPLES.md strips context → principles are fully actionable

**B16 falsification condition**: "A systematic review finds >80% still actionable and current."
- Strict interpretation (fully current): 67% → B16 holds (decay IS happening)
- Liberal interpretation (rule still actionable): 100% → B16 partially falsified (decay doesn't impair usefulness)

**Resolution**: B16 should be refined. The current claim is too broad. Accurate version: "Knowledge decay is invisible to growth metrics but present — lessons accumulate stale context while their extracted principles remain durable. The danger is for lessons without a separate principle layer."

## Sources of Undecayed Lessons

The 20 fully actionable lessons tend to be:
- Protocol definitions (L-002, L-004, L-006, L-012, L-019) — protocols don't expire until explicitly superseded
- Architecture validations (L-005, L-014, L-017, L-018) — architecture confirmed repeatedly
- Living mechanisms (L-011, L-015, L-021, L-028) — still in active use, self-renewing

## Recommendation

1. Add `Still-valid-as-of: [session]` field to lessons when they're read and verified (optional, low-friction)
2. The PARTIALLY_STALE lessons need a simple update: replace outdated numbers with current ones or add "(as of session N)"
3. B16 should be refined (see above) — current wording overstates the damage
