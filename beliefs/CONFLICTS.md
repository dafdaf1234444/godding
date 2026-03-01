# Conflict Resolution Protocol v0.1

> **SUPERSEDED (S399):** 0 invocations in 399 sessions (L-830 challenge audit). The semantic conflicts this protocol addressed are resolved in practice by: soft-claiming (claim.py), merge-on-close (close_lane.py), and cross-citation with FALSIFIED/SUPERSEDED markers. Rules below remain historically valid but are not operationally used. See CHALLENGES.md entry "CONFLICTS.md (dead protocol)" for evidence.

## When conflicts happen
Concurrent sessions may produce contradictory outputs. Git handles file-level merge conflicts mechanically. This protocol handles *semantic* conflicts — contradictions in meaning.

## Types of semantic conflict

| Type | Example | Resolution |
|------|---------|------------|
| Belief contradiction | Session A: "B1 is verified" / Session B: "B1 is disproven" | The session with *evidence* wins. If both have evidence, create a new frontier question. |
| Lesson contradiction | L-005: "always X" / L-007: "never X" | Keep both, add a cross-reference note. Create a task to reconcile. |
| Frontier collision | Both sessions claim to resolve F3 differently | The human (or next session) reviews both, picks the stronger answer or synthesizes. |
| Index divergence | Both sessions update INDEX.md differently | Merge both additions. INDEX is append-friendly by design. |

## Resolution rules (in priority order)
1. **Evidence beats assertion.** Verified > Assumed > Inherited. Always.
2. **Specificity beats generality.** A lesson from testing a specific case outranks a general principle.
3. **Later evidence beats earlier evidence.** If both are verified, the more recent verification wins (the world changes).
4. **When in doubt, escalate.** Write the conflict to `tasks/FRONTIER.md` and let the next session (or human) decide.

## Prevention
- Before updating a belief, `git pull` first.
- Check DEPS.md before changing any belief — understand what depends on it.
- Use branches for speculative belief changes. Only merge to master when confident.

## This file depends on: B1 (git-as-memory), B6 (swarm model)
