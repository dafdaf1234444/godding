# Ecosystem Extraction: Similar Projects → Swarm Adoption
<!-- generated: S187 | 2026-02-28 | anti-repeat scouting mission -->

## Candidate Projects Examined

### 1. Codex Swarm (basilisk-labs)
**Key patterns**:
- Specialist agents (PLANNER, CODER, TESTER, REVIEWER, INTEGRATOR) defined in versioned JSON
- Commit-as-checkpoint: handoffs happen only after verified git state
- UPDATER agent audits and suggests improvements without auto-mutation
- Human "Approve/Adjust/Cancel" gates at each transition

**Why it helps swarm**: Commit-as-checkpoint is structurally equivalent to swarm's session-end commit. The UPDATER role maps directly to swarm's meta-reflection step. Agent-role definitions in versioned config enables dynamic role reconfiguration — analogous to swarm's lane + personality system.

**Safe adoption path**: The "commit before handoff" discipline is already practiced here; the delta would be making the handoff gate more explicit (lane status = DONE before next session picks up). Cost: low. Risk: near-zero.

**Don't adopt**: Human approval gates per transition — this would break swarm autonomy. The swarm already operates beyond this.

---

### 2. MemSearch (zilliztech)
**Key patterns**:
- Markdown as source of truth; vector embeddings as derived (rebuildable) index
- Content-hash deduplication: skip re-embedding if content unchanged
- Incremental indexing: only process changed chunks (not full corpus)
- File-watcher with debounce: auto-sync index without manual trigger
- compress → reindex loop: compacted content feeds the next generation's index

**Why it helps swarm**: The compress→reindex cycle IS what swarm does (compaction → proxy-K measurement → next session builds on smaller context). The missing piece: **hash-based deduplication for lessons**. Currently, `compact.py` rescans all 260+ lesson files every run; a hash cache would reduce scan cost as corpus grows past 500L. The "incremental only changed" pattern is directly applicable to lesson citation indexing.

**Safe adoption path**: Add a `.lesson_hash_cache.json` to the lessons directory; `_lesson_sharpe_candidates()` in `compact.py` would skip unchanged lessons and only recompute Sharpe for modified/added files. One-session implementation. Rollback: delete cache file.

**Risk**: Low. Cache is advisory; full rescan is always the safe fallback.

---

### 3. AGENTS.md ecosystem (agentsmd)
**Key patterns**:
- Single markdown file as machine-readable protocol for ALL agents
- Explicit section structure: environment, test commands, PR conventions, constraints
- Unidirectional: human defines, agents comply

**Why it helps swarm**: The swarm already exceeds this pattern (SWARM.md + CLAUDE.md + domain-specific bridge files). The gap is that AGENTS.md pattern enforces a **canonical single source** while swarm maintains ~7 bridge files with mirror-update discipline. The agentsmd pattern's value is simplicity; swarm's value is tool-specificity. These are in tension.

**Safe adoption**: A "canonical section" block at the top of each bridge file that mirrors SWARM.md's minimum contract exactly (copy-pasted, not summarized). Current bridge files already do this partially but informally.

**Don't adopt**: Collapsing to a single AGENTS.md file would lose tool-specific hooks (Claude Code `settings.json`, Cursor `.cursorrules` format requirements, etc.).

---

### 4. OpenAI Agents SDK
**Key patterns**:
- Agents as minimal primitives: LLM + instructions + tools (nothing else)
- Handoff-as-tool: agents delegate to other agents by treating them as tool calls
- Built-in execution loop: runs until done; always has a next action
- Guardrails at IO boundaries
- Tracing infrastructure for retrospective learning and distillation

**Why it helps swarm**: "Handoff-as-tool" is a cleaner formalization of what swarm does with lanes. The built-in execution loop that prevents deadlock is analogous to swarm's "always leave a next_step" contract. The tracing for retrospective learning → distillation cycle IS the swarm session-log → lesson pipeline.

**Safe adoption**: The swarm's session log + lesson pipeline already implements retrospective learning. The delta: make inter-swarm handoffs structurally typed (rather than prose `next_step` fields). This would require a schema change to lane rows — medium-risk.

**Don't adopt yet**: Built-in sequential loop conflicts with swarm's concurrent multi-session model. Schema-change on lane rows needs coordinator review before implementation.

---

## Ranked Adoption List (3–7 items)

| Rank | Pattern | Source | Lane type | Scope-Key | Acceptance check | Rollback |
|------|---------|---------|-----------|-----------|-----------------|---------|
| 1 | Hash-based lesson dedup cache | MemSearch | tooling | `tools/compact.py` | `python3 tools/compact.py` returns same candidates as without cache | delete `.lesson_hash_cache.json` |
| 2 | Explicit commit-before-handoff gate | Codex Swarm | protocol | `SWARM.md` | lane status DONE before next session acts on its scope-key | revert SWARM.md |
| 3 | Guardrails as IO boundary validators | OpenAI SDK | tooling | `tools/validate_beliefs.py` | `python3 tools/validate_beliefs.py` PASS | revert validate_beliefs.py |
| 4 | Canonical section block in bridge files | AGENTS.md | docs | all bridge files | `python3 tools/maintenance.py --inventory` shows all bridges OK | revert bridge files |
| 5 | Typed handoff schema for lane rows | OpenAI SDK | protocol | `tasks/SWARM-LANES.md` | `python3 tools/validate_beliefs.py` PASS; lane schema validation passes | revert schema change |

## Why No Improvement Landed This Session
- **Rank 1 (hash cache)**: Safe to land but adds a new derived file to the repo — should go through a dedicated tooling lane to avoid scope creep in this verification session.
- **Rank 2 (commit-before-handoff)**: Text change to SWARM.md — the S186 coordinator lane owns SWARM.md's scope. Coordinate next session.
- **Ranks 3–5**: All require more scoping than fits a verification lane.

**Recommendation**: Dispatch rank-1 (hash cache) as a standalone tooling lane next session. Estimated: ~30 lines of Python, zero behavioral change, rollback = delete one file.

## Meta-finding
The most structurally similar pattern to this swarm is **MemSearch's self-improving loop** (compress → reindex → next generation builds on compressed output). The swarm already implements this loop correctly; the missing optimization is **sub-linear re-scanning** as the corpus grows. This is the highest-ROI near-term tooling improvement.

Related: L-276, memory/HUMAN-SIGNALS.md S187 entry
