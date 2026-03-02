# Level 1 Compaction Dry-Run Analysis
Date: 2026-02-25 | Analyst: Sub-agent (dry-run only, no modifications made)

## 1. Current State

- INDEX.md: 60 lines
- Lessons listed in INDEX: 22 (L-001 through L-022), plus L-023 referenced but file missing
- Lesson files on disk: 22 (L-001 through L-022) plus TEMPLATE.md
- memory/themes/ directory: does not exist yet
- INDEX already uses thematic grouping (3 themes: Architecture, Protocols, Strategy)

**Compaction trigger assessment:**
- Trigger 1: INDEX.md is exactly 60 lines -- AT threshold
- Trigger 4: 22 lessons > 25 threshold? No, 22 < 25. But close.
- Conclusion: Trigger 1 is borderline (at, not exceeding 60). If L-023 is added, it will exceed. Compaction is not yet mandatory but is imminent.

## 2. Proposed Theme Groupings

INDEX already organizes lessons into 3 themes. After reading every lesson file and analyzing the "Affected beliefs" fields, I propose refining into 5 themes for more precise navigation:

### Theme A: System Architecture (6 lessons)
Lessons about what this system IS and how its parts fit together.

| Lesson | Title | Affected Beliefs |
|--------|-------|-----------------|
| L-001  | Genesis validation -- setup mostly works | B1, B2, B6 |
| L-005  | Blackboard+stigmergy hybrid, not a swarm | B6 |
| L-008  | Folder structure works -- refine, don't replace | B2 |
| L-010  | B1 holds at small scale but has a known ceiling | B1 |
| L-014  | Crowston's 3 affordances for stigmergy validated | B6 |
| L-017  | Forking is free; merge-back is the hard problem | B1, B6 |

### Theme B: Knowledge Management Protocols (6 lessons)
Lessons about how to capture, correct, and maintain knowledge.

| Lesson | Title | Affected Beliefs |
|--------|-------|-----------------|
| L-002  | Distillation needs a protocol, not just a template | B2, B6 |
| L-004  | Semantic conflicts need rules beyond git merge | B1, B6 |
| L-006  | The 3-S Rule for verification decisions | B5 |
| L-012  | Error correction -- mark SUPERSEDED, never delete | B1, B2 |
| L-013  | Knowledge staleness -- review triggers, not expiration | B2 |
| L-016  | CORE.md v0.2 -- integrate lessons without bloating | all |

### Theme C: Operational Strategy (4 lessons)
Lessons about work/meta-work balance, scaling, and decision-making.

| Lesson | Title | Affected Beliefs |
|--------|-------|-----------------|
| L-007  | Work/meta-work ratio is phase-dependent (20/80 to 80/20) | B4 |
| L-011  | Lesson archival -- group by theme at ~15 lessons | B1, B2 |
| L-015  | Frontier IS the self-assignment mechanism (2.5x amplification) | none |
| L-021  | Diminishing returns -- when lessons repeat, switch to domain work | B4, B8 |

### Theme D: Scaling and Multi-Agent (5 lessons)
Lessons about concurrent sessions, context limits, and automation.

| Lesson | Title | Affected Beliefs |
|--------|-------|-----------------|
| L-009  | First artifact -- swarm.sh automates manual checks | none |
| L-018  | Concurrent sessions -- git pull --rebase, INDEX/FRONTIER are hot files | B1 |
| L-019  | Context handoff -- every commit is a checkpoint | B1, B3 |
| L-020  | Genesis automation -- minimum viable swarm is 12 files | B1, B7 |
| L-023  | Sustainability -- context, compaction, continuation, parallel, spawn | (referenced in INDEX but file missing) |

### Theme E: Epistemic Discipline (1 lesson)
Lessons about honesty, self-assessment, and falsification.

| Lesson | Title | Affected Beliefs |
|--------|-------|-----------------|
| L-003  | Measure improvement with 5 git-extractable indicators | B1, B4 |
| L-022  | "Proven" claim was false with 62% beliefs untested | B1, B3, B7 |

**Note on Theme E:** Only 2 lessons, which is thin for a standalone theme. Could merge into Theme B (Knowledge Management Protocols) since epistemic discipline is a form of knowledge quality management. However, L-022 represents a qualitatively different kind of lesson (external adversarial review) that may warrant its own theme as the swarm matures. I present both options; the 5-theme version is shown for analysis but 4 themes (merging E into B) is also defensible.

## 3. Proposed memory/themes/ Directory Contents

Each file would contain the lesson table from above, plus a 2-3 line theme summary.

```
memory/themes/
  architecture.md      (~20 lines) - 6 lessons about system identity and structure
  knowledge-mgmt.md    (~20 lines) - 6 lessons about knowledge capture, correction, verification
  strategy.md          (~15 lines) - 4 lessons about work ratios, scaling triggers, meta-work
  scaling.md           (~18 lines) - 5 lessons about multi-agent, automation, context limits
  epistemic.md         (~12 lines) - 2 lessons about measurement and honest self-assessment
```

Total new content: ~85 lines across 5 files.

## 4. Proposed New INDEX.md "Lessons" Section

The current INDEX.md lessons section (lines 28-50) is 23 lines. It would be replaced with:

```markdown
## Lessons (22 total, 5 themes)
See memory/themes/ for detailed lesson listings with summaries.

- **Architecture** (6 lessons) — system identity: blackboard+stigmergy, folder structure, git-as-memory ceiling, forking. See memory/themes/architecture.md
- **Knowledge Management** (6 lessons) — distillation, conflict resolution, 3-S verification, error correction, staleness, CORE.md integration. See memory/themes/knowledge-mgmt.md
- **Strategy** (4 lessons) — work/meta-work ratio, thematic archival, self-sustaining frontier, diminishing returns. See memory/themes/strategy.md
- **Scaling** (5 lessons) — swarm.sh CLI, concurrent sessions, context handoff, genesis automation, sustainability protocols. See memory/themes/scaling.md
- **Epistemic Discipline** (2 lessons) — health metrics, external review exposed false "proven" claim. See memory/themes/epistemic.md
```

This is 8 lines (header + blank + 5 theme lines + blank), replacing the current 23 lines.

## 5. Line Savings Analysis

| Section | Before | After | Saved |
|---------|--------|-------|-------|
| Lessons block in INDEX.md | 23 lines | 8 lines | 15 lines |
| INDEX.md total | 60 lines | 45 lines | 15 lines |

This brings INDEX.md well under the 60-line trigger threshold, buying room for approximately 15 more lessons before the next compaction is needed.

## 6. Information Loss Assessment

**Would any information be lost?**

No. Level 1 compaction explicitly preserves all lesson files. The only change is that INDEX.md no longer lists individual lesson summaries -- that detail moves to theme files in memory/themes/. A reader navigating from INDEX.md reaches the same information in one extra click (INDEX -> theme file -> lesson file) instead of zero (INDEX -> lesson file).

**Specific risks to evaluate:**

1. **Discoverability**: Slightly reduced. A new agent reading INDEX.md will see theme names, not lesson titles. They must open a theme file to find the specific lesson. Mitigated by including keyword-rich theme descriptions.

2. **L-023 ghost reference**: INDEX.md line 50 references L-023 but no L-023.md file exists. Compaction should either create L-023 first or note the discrepancy in the theme file. This is a pre-existing issue, not caused by compaction.

3. **Cross-theme lessons**: Several lessons touch multiple themes (e.g., L-001 touches architecture AND protocols). The theme files should list each lesson in its primary theme only, but the "Affected beliefs" column provides cross-referencing. No information lost, but a reader interested in B1 would need to check multiple theme files. This is already the case with the current 3-theme grouping in INDEX.

4. **Lesson TEMPLATE.md**: The template file in memory/lessons/ is not a lesson and should be excluded from theme files. It stays in place, referenced by DISTILL.md.

## 7. Recommendation

**Compaction is not yet mandatory** (22 lessons < 25 trigger, INDEX at exactly 60 lines not exceeding it), but it is imminent. The dry-run shows:

- Clean thematic grouping is possible with 4-5 themes
- 15 lines saved in INDEX.md (25% reduction)
- Zero information loss
- Minimal risk (Level 1 is the safest compaction level)

**Suggested execution order when compaction is triggered:**
1. Resolve the L-023 ghost reference (create the file or remove the INDEX reference)
2. Run `python3 tools/validate_beliefs.py` (pre-compaction check)
3. Create memory/themes/ directory and 5 theme files
4. Replace INDEX.md lessons section with theme pointers
5. Run validator again (post-compaction check)
6. Test Rule 7 (swarmability): can a new agent onboard in 5 minutes with the new structure?

## 8. Pre-existing Issue Found

INDEX.md line 50 references "L-023" about sustainability protocols (context management, compaction, auto-continuation, parallel agents, spawn), but no file memory/lessons/L-023.md exists on disk. This should be resolved independently of compaction.
