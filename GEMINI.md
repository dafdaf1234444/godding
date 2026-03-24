<!-- bridge_version: 1.1 | 2026-03-24 | S540: dedup — shared items moved to SWARM.md -->
# Gemini Bridge

This repo uses a multi-session protocol. Read `SWARM.md` for the full protocol.
See `SWARM.md` §Common Bridge Items for signaling, soft-claim, contract validation, concurrent-safe commit, safety, and human interaction protocols.
See `SWARM.md` §Minimum Cycle for the orient→act→compress→handoff loop.

## Gemini specifics
- **Parallel agents**: Gemini CLI has experimental subagents but they execute sequentially, not in parallel. Work as a serial executor: take one task from `tasks/NEXT.md`, complete it, check for the next. For true parallelism, spawn separate terminal sessions with `gemini --yolo`.
- **Entry**: This file auto-loads in Gemini CLI (hierarchical: `~/.gemini/GEMINI.md` → project root → subdirectories). `SWARM.md` is the canonical protocol.
- **Shell**: Full shell access via built-in `run_shell_command` tool. Use `@` to inject file content into prompts.

## Multi-tool compatibility (F118)
Core state (beliefs, lessons, principles, frontiers) is tool-agnostic markdown + git.
Entry files: `CLAUDE.md` (Claude Code), `AGENTS.md` (Codex/Copilot), `.cursor/rules/swarm.mdc` + `.cursorrules` (Cursor), `GEMINI.md` (Gemini), `.windsurfrules` (Windsurf), `.github/copilot-instructions.md` (Copilot).
Each bridge file loads `SWARM.md` and adds tool-specific instructions.
