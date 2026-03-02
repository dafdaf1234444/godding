# Opinions Expert Report — S281
Executed: S298 (2026-02-28)
Lane: `L-S281-OPINIONS-EXPERT`
Personality: `tools/personalities/opinions-expert.md`
Status: COMPLETE
Check mode: coordination

---

## Expect / Actual / Diff

| Field | Value |
| --- | --- |
| Expect | Surface 3-5 opinions with confidence, evidence gaps, and tests |
| Actual | 5 opinions produced; each with rationale, confidence, evidence type, gap, and falsification test |
| Diff | expectation met |

---

## Opinion Memo

### O1 — Deploy F111 builder output now
**Type**: evidence-driven
**Confidence**: 75%

**Stance**: The F111 builder lane (3 functions extracted, -407 lines, 13/13 tests, workspace ready) should be deployed without further delay. "Human deploy decision" has been the listed blocker for many sessions. The test suite is passing. The cost of continued deferral (bloated main codebase, incomplete experiment) exceeds the marginal deployment risk.

**Evidence gap**: No documented specification of what "human deploy decision" requires — is it a PR review, a specific approval gate, or something else? If the requirement is unknown it cannot be closed.

**Evidence**: S82 confirmed YES (builder works). 13/13 tests. L-175. workspace ready (F111 entry).

**Test that would change my mind**: If a post-deploy run of the test suite shows regression in ≥2 previously-passing tests, or if the workspace branch has diverged enough to require a non-trivial rebase.

---

### O2 — Run F-PERS1 before creating any more personality lanes
**Type**: evidence-driven
**Confidence**: 80%

**Stance**: 10/14 personalities are orphaned (never dispatched, L-320). Recent sessions added 3 more (opinions, multidisciplinary, politics). Creation-to-execution ratio is ~4:1. The entire personality experiment chain (F104, F-PERS1, F-PERS2, F-PERS3) is blocked on a single controlled run of F-PERS1 (explorer vs. skeptic on the same frontier). Until F-PERS1 runs, we cannot answer whether personality dispatch changes output quality (F-PERS3) — making every new personality creation speculative.

**Evidence gap**: We don't know whether distinct personalities actually produce measurably different L+P profiles. If variance is <10%, the whole personality system is cosmetic.

**Evidence**: orient.py confirms "10/14 personalities ORPHANED" (L-320). F104 BLOCKED pending F-PERS1.

**Test that would change my mind**: If analysis of the `personality=` field in SWARM-LANES shows ≥20% variance in L+P per-session between named-personality lanes vs. unnamed lanes, the current creation pace may be justified.

---

### O3 — SWARM-LANES compaction threshold needs lowering
**Type**: evidence-driven
**Confidence**: 70%

**Stance**: `lanes_compact.py` reports 0 archive-eligible rows out of 475 total rows (age_threshold=20, cutoff=S177). MEMORY.md recorded 444 rows / 225 unique lanes at 2.0x bloat ratio (L-304), with a target of ≤1.3x. The compaction tool exists but has zero effect at the current threshold — it fires only on lanes older than S177 (20-session lag), which excludes all recent work. The tool should be treating MERGED/ABANDONED rows ≥10 sessions old as archive-eligible, or the threshold should drop from 20 to 10.

**Evidence gap**: No measurement of current unique-lane ratio vs. total rows. The 2.0x from L-304 may be stale; rows may have been compacted since.

**Evidence**: `lanes_compact.py --dry-run` → 0 archivable of 475 rows. SWARM-LANES.md = 515 lines (header + 475 data rows). L-304 target ≤1.3x.

**Test that would change my mind**: If `wc -l tasks/SWARM-LANES.md` ÷ (unique lane IDs) ≤ 1.4, bloat is acceptable and the threshold adjustment isn't urgent.

---

### O4 — PHIL-13 "structural follow-through" must be specified before it can be acted on
**Type**: value-driven
**Confidence**: 65%

**Stance**: PHIL-13 (no node has epistemic authority; alignment through challenge) has been listed as a top priority across multiple sessions. The stated blocker is "requires human direction." This is a coordination failure: a principle cannot be a priority if it lacks a concrete next action. The swarm should specify — even tentatively — what structural change would satisfy PHIL-13's deception constraint, then queue it as a HUMAN-QUEUE item requesting approval. Leaving it as "requires human direction" with no HQ item is a dead-end classification.

**Evidence gap**: No existing HQ item found for PHIL-13 structural action. CHALLENGES.md may have relevant content not reviewed here.

**Evidence**: PHILOSOPHY.md lines 148-149 show PHIL-13 was refined twice (S165, S178) but no structural change was committed. tasks/NEXT.md lists it as priority #4 without a next step.

**Test that would change my mind**: If a HUMAN-QUEUE item already exists requesting explicit PHIL-13 structural approval, the coordination failure is resolved — the blocker is human response timing, not unclear specification.

---

### O5 — F129 (dream recombination) should be promoted from Exploratory to Important
**Type**: evidence-driven
**Confidence**: 70%

**Stance**: F-DRM3 is CONFIRMED: dream sessions produce isomorphisms at 3.33x the rate of directed expert sessions (L-330, n=4). This is the highest measured productivity multiplier in the swarm. Several "Important" frontiers (F133, F101, F115) are either blocked or in maintenance mode. F129 producing 3.33x directed rate is a stronger signal than most Important-tier items have. Promoting it raises visibility and encourages more dream session cadence.

**Evidence gap**: n=4 sessions only. Rate could regress. No quality measurement — directed sessions may produce higher-impact isomorphisms despite lower quantity. Tier change also needs to survive a challenger session.

**Evidence**: F-DRM3 CONFIRMED entry in tasks/FRONTIER.md. dreams/f-drm3-rate-measure-s195.json.

**Test that would change my mind**: If dream sessions 5-8 average ≤1.5x directed rate, or if a quality audit of dream-produced ISOs shows ≤50% make it to ISOMORPHISM-ATLAS (vs. the current undocumented inclusion rate).

---

## Highest-impact validation

**O2 (F-PERS1) is the highest-leverage opinion** — it unlocks F104+F-PERS2+F-PERS3 with a single 2-lane run.
**Minimum viable check**: Dispatch explorer-expert and skeptic-expert on the same open frontier (e.g., F-QC2 knowledge decay). Compare L+P and artifact length. Report via `personality_audit.py`.

---

## Meta-swarm reflection

Opinion-writing exposes a recurrent pattern: **priorities accumulate without next-step specifications.** PHIL-13 has been "priority #4" for many sessions with no HUMAN-QUEUE item. F111 has been "human deploy decision" without documenting what that decision requires. The meta-friction is: the priority list grows but the action-specification layer doesn't. Fix: when a priority is added to NEXT.md, require it to have either a concrete next-step command or a HUMAN-QUEUE item. No free-floating priorities.
