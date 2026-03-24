<!-- bridge_version: 1.1 | 2026-03-24 | S540: dedup — shared items moved to SWARM.md -->
# Codex/Copilot Bridge

This repo uses a multi-session protocol. Read `SWARM.md` for the full protocol.
See `SWARM.md` §Common Bridge Items for signaling, soft-claim, contract validation, concurrent-safe commit, safety, and human interaction protocols.
See `SWARM.md` §Minimum Cycle for the orient→act→compress→handoff loop.

## Codex/Copilot specifics
- **Parallel agents**: Use sub-agent spawning for independent sub-tasks (Codex: multi-agent mode; Copilot: /fleet or coding agent).
- **Entry**: This file auto-loads in Codex CLI and GitHub Copilot. `SWARM.md` is the canonical protocol.

## Multi-tool compatibility (F118)
Core state (beliefs, lessons, principles, frontiers) is tool-agnostic markdown + git.
Entry files: `CLAUDE.md` (Claude Code), `AGENTS.md` (Codex/Copilot), `.cursor/rules/swarm.mdc` + `.cursorrules` (Cursor), `GEMINI.md` (Gemini), `.windsurfrules` (Windsurf), `.github/copilot-instructions.md` (Copilot).
Each bridge file loads `SWARM.md` and adds tool-specific instructions.
