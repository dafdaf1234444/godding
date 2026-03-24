<!-- claude_md_version: 1.1 | 2026-03-24 | S529: direct language pass -->
# Claude Code Bridge

This repo uses a multi-session protocol. Read `SWARM.md` for the full protocol.

## Claude Code specifics
- **Parallel agents**: Use Task tool for independent sub-tasks.
- **Spawn**: Task tool IS the spawn mechanism. Sub-agents receive `beliefs/CORE.md` + `memory/INDEX.md` + their task.
- **Swarm signaling**: Use `python3 tools/swarm_signal.py post <type> <content>` for structured signals. Also update `tasks/NEXT.md`, `tasks/SWARM-LANES.md`, or inter-swarm bulletins as appropriate. See `memory/NODES.md` for the participant model.
- **Hooks**: Install with `bash tools/install-hooks.sh` (pre-commit runs `bash tools/check.sh --quick`; commit-msg enforces `[S<N>] what: why`). See `.claude/settings.json`.
- **Soft-claim protocol**: Use `python3 tools/claim.py claim <file>` before editing DUE items to prevent concurrent-edit collisions (F-CON2).
- **Contract validation**: Run `python3 tools/contract_check.py` to validate self-model integrity (F-META8). Wired into check.sh pre-commit.
- **Concurrent-safe commit** (L-1538): Use `python3 tools/safe_commit.py -m "[S<N>] what: why" file1 file2` instead of git-add/git-commit when index corruption occurs. Uses isolated GIT_INDEX_FILE + plumbing commands. Verifies CLAUDE.md exists in tree before committing.
- **Entry**: This file auto-loads in Claude Code. `SWARM.md` is the canonical protocol.
- **No plan mode**: Do NOT use EnterPlanMode — the orient-act-compress cycle IS the planning mechanism (L-1160, L-601). Plan mode creates deadlock with the autonomous protocol.
- **Safety-first collaboration**: Prefer reversible, scope-limited changes; avoid destructive or out-of-scope side effects; if risk or authority is unclear, ask the human before proceeding.
- **Human interaction (minimum-by-default)**:
  - Ask the human only when blocked by missing authority, inaccessible data, or irreversible preference decisions.
  - Before asking, check `memory/HUMAN.md`, `tasks/SIGNALS.md`, and `tasks/HUMAN-QUEUE.md` for existing directives/answers.
  - If the answer already exists, do not ask again; proceed using recorded state.
  - New questions: post via `python3 tools/swarm_signal.py post question "..." --target human`.

## Minimum Swarmed Cycle
- **PowerShell host fallback**: if `python3`/`python`/`py -3` are unavailable in the active shell, use `pwsh -NoProfile -File tools/orient.ps1`, `tools/task_order.ps1`, `tools/question_gen.ps1`, `tools/dispatch_optimizer.ps1`, `tools/check.ps1 --quick`, and `tools/maintenance.ps1 --inventory`.
- **Orient first**: `python3 tools/orient.py` — synthesizes maintenance status, priorities, frontier headlines, and a suggested action. At N≥3 concurrency, use `--coord` for coordination-only output (70% smaller, L-1433).
- **Task order**: `python3 tools/task_order.py` — converts orient output into a scored, ordered task list with explicit priority tiers (COMMIT → DUE → CLOSE → DISPATCH → PERIODIC). Re-run after each task to re-rank.
- **Inquiry frame**: `python3 tools/question_gen.py` — generates 6 question categories (frontiers, belief health, compression ratios, zombies, prescription gaps, open signals); act on or defer each (L-1045, SIG-59).
- **Anti-repeat check** (L-283): `git log --oneline -5` + scan `tasks/SWARM-LANES.md` MERGED rows before acting; concurrent sessions may have preempted your plan.
- Choose and log a check mode (`objective`/`historian`/`verification`/`coordination`/`assumption`) for active lane updates.
- Declare expectation before acting and record the diff after acting.
- Record positive, negative, and null outcomes equally.
- **Expert dispatch first** (F-EXP7): run `python3 tools/dispatch_optimizer.py` — if a top-3 domain has no active DOMEX lane, open one and work as that domain's expert. Expert mode is the default work mode, not a fallback. Target ≥15% expert utilization.
- Default to executing active work from `tasks/NEXT.md` and `tasks/SWARM-LANES.md`; if not executed, mark explicit `blocked`/`reassigned`/`abandoned` with next action.
- Keep bridge files synchronized: if one bridge gains protocol-critical guidance, mirror it across all bridge entry files in the same session.
- **Science quality** (P-243, L-804): pre-register every DOMEX lane with falsifiable expectations. Adversarial lanes (mode=falsification) target 1-in-5. Report effect size. See SWARM.md §Science Quality.
- **Process reflection** (L-831): mandatory each session — name a specific target file or tool for process improvement; abstract suggestions without concrete targets have ~15% conversion rate (L-635).
- **Handoff**: run `python3 tools/sync_state.py` and `python3 tools/validate_beliefs.py` before final commit; run `python3 tools/cell_blueprint.py save` to snapshot current state for child spawns (L-1184); then `git push`.
- **Reproduction** (L-1499): `python3 tools/genesis_extract.py` produces a minimal daughter bundle. Boot tier + genesis_extract = self-reproducing fixed point (von Neumann copier-in-description).

## Multi-tool compatibility (F118)
Core state (beliefs, lessons, principles, frontiers) is tool-agnostic markdown + git.
Entry files: `CLAUDE.md` (Claude Code), `AGENTS.md` (Codex/Copilot), `.cursor/rules/swarm.mdc` + `.cursorrules` (Cursor), `GEMINI.md` (Gemini), `.windsurfrules` (Windsurf), `.github/copilot-instructions.md` (Copilot).
Each bridge file loads `SWARM.md` and adds tool-specific instructions.
