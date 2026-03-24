<!-- claude_md_version: 1.2 | 2026-03-24 | S540: dedup — shared items moved to SWARM.md -->
# Claude Code Bridge

This repo uses a multi-session protocol. Read `SWARM.md` for the full protocol.
See `SWARM.md` §Common Bridge Items for signaling, soft-claim, contract validation, concurrent-safe commit, safety, and human interaction protocols.
See `SWARM.md` §Minimum Cycle for the orient→act→compress→handoff loop.

## Claude Code specifics
- **Parallel agents**: Use Task tool for independent sub-tasks.
- **Spawn**: Task tool IS the spawn mechanism. Sub-agents receive `beliefs/CORE.md` + `memory/INDEX.md` + their task.
- **Hooks**: See `.claude/settings.json` for PostToolUse validation hooks.
- **Entry**: This file auto-loads in Claude Code. `SWARM.md` is the canonical protocol.
- **No plan mode**: Do NOT use EnterPlanMode — the orient-act-compress cycle IS the planning mechanism (L-1160, L-601). Plan mode creates deadlock with the autonomous protocol.
- **Concurrent-safe commit note**: Verifies CLAUDE.md exists in tree before committing.

## Multi-tool compatibility (F118)
Core state (beliefs, lessons, principles, frontiers) is tool-agnostic markdown + git.
Entry files: `CLAUDE.md` (Claude Code), `AGENTS.md` (Codex/Copilot), `.cursor/rules/swarm.mdc` + `.cursorrules` (Cursor), `GEMINI.md` (Gemini), `.windsurfrules` (Windsurf), `.github/copilot-instructions.md` (Copilot).
Each bridge file loads `SWARM.md` and adds tool-specific instructions.
