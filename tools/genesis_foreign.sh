#!/usr/bin/env bash
# genesis_foreign.sh — Bootstrap minimum viable swarm protocol onto a foreign git repo
# Creates the smallest structure needed for cross-session knowledge accumulation.
# Usage: bash tools/genesis_foreign.sh /path/to/foreign/repo [project-name]
#
# What it creates:
#   CLAUDE.md          — bridge file (session entry point)
#   beliefs/CORE.md    — operating principles (lightweight)
#   memory/INDEX.md    — knowledge index
#   memory/lessons/    — lesson directory
#   memory/EXPECT.md   — expect-act-diff protocol
#   tasks/NEXT.md      — handoff state between sessions
#   tasks/FRONTIER.md  — open questions
#
# What it does NOT create: full swarm tooling, domain structure, or council/expert machinery.
# Those emerge organically if the swarm grows.

set -euo pipefail

TARGET="${1:?Usage: bash tools/genesis_foreign.sh /path/to/repo [project-name]}"
PROJECT_NAME="${2:-$(basename "$TARGET")}"
DATE=$(date +%Y-%m-%d)

if [ ! -d "$TARGET/.git" ]; then
    echo "ERROR: $TARGET is not a git repository"
    exit 1
fi

# Check if swarm structure already exists
if [ -f "$TARGET/beliefs/PHILOSOPHY.md" ]; then
    echo "ERROR: $TARGET already has swarm structure (beliefs/PHILOSOPHY.md exists)"
    exit 1
fi

echo "=== Genesis Foreign: $PROJECT_NAME ==="
echo "Target: $TARGET"
echo "Date: $DATE"
echo ""

# Create directory structure
mkdir -p "$TARGET/beliefs" "$TARGET/memory/lessons" "$TARGET/tasks"

# --- CLAUDE.md (bridge file) ---
cat > "$TARGET/CLAUDE.md" << 'BRIDGE'
# Swarm Bridge

This repo uses a lightweight swarm protocol for cross-session knowledge accumulation.

## Session protocol
1. **Orient**: Read `tasks/NEXT.md` and `memory/INDEX.md` to understand current state
2. **Act**: Do real work. Before non-trivial actions, write what you expect to happen
3. **Compress**: If you learned something, write a lesson in `memory/lessons/L-NNN.md` (max 20 lines)
4. **Hand off**: Update `tasks/NEXT.md` so the next session has state

## Rules
- Every session leaves the repo knowing more than before
- Challenge stale assumptions — if something was true 20 sessions ago, verify it's still true
- Real work over meta-work — the codebase is the primary focus, not the swarm structure
- Commit with format: `[S<N>] what: why`

## Files
- `beliefs/CORE.md` — operating principles and project context
- `memory/INDEX.md` — what the swarm knows
- `memory/lessons/` — individual findings (max 20 lines each)
- `memory/EXPECT.md` — predict-before-acting protocol
- `tasks/NEXT.md` — current priorities and handoff state
- `tasks/FRONTIER.md` — open questions about the codebase
BRIDGE

# --- beliefs/CORE.md ---
cat > "$TARGET/beliefs/CORE.md" << CORE
# Core Beliefs — ${PROJECT_NAME}
v0.1 | ${DATE} | Genesis

## Purpose
Compound understanding of this codebase across sessions. Every session leaves the
system knowing more, more accurately, more compactly.

## Operating principles
1. **Read before writing.** Understand existing code before suggesting changes.
2. **Small steps.** Act small, commit, learn, update.
3. **Document decisions.** Future sessions can't read your context. Write why.
4. **Track evidence.** If unverified, mark it. If verified, record how.
5. **Compress.** Don't dump — distill to what matters.
6. **Challenge assumptions.** Every belief about this codebase is testable.
7. **Expect before acting.** Predict outcomes, measure diffs.

## Project context
- Project: ${PROJECT_NAME}
- Stack: (fill after first orient)
- Key patterns: (fill after first orient)
CORE

# --- memory/INDEX.md ---
cat > "$TARGET/memory/INDEX.md" << INDEX
# Memory Index — ${PROJECT_NAME}
Updated: ${DATE} | Sessions: 0

## What the swarm knows
- **0 lessons** in \`memory/lessons/L-{NNN}.md\`
- **0 frontier questions** in \`tasks/FRONTIER.md\`

## Key architecture decisions
(Fill as you learn them)

## Code patterns
(Fill as you identify them)
INDEX

# --- memory/EXPECT.md ---
cat > "$TARGET/memory/EXPECT.md" << EXPECT
# Expect-Act-Diff Protocol

Before any non-trivial action:
1. **Expect**: Write what you predict will be true after the action (one line)
2. **Act**: Do the thing
3. **Diff**: Compare prediction to reality

- Zero diff = confirmation (tighten confidence)
- Large diff = learning event (write a lesson)
- Persistent diff = assumption is wrong (update beliefs)
EXPECT

# --- tasks/NEXT.md ---
cat > "$TARGET/tasks/NEXT.md" << NEXT
# Next — ${PROJECT_NAME}

## Key state
- Sessions completed: 0
- Lessons: 0
- Open questions: 0

## For next session
1. First orient: read README, understand project structure, identify stack
2. Map key architectural decisions into beliefs/CORE.md
3. Identify 3-5 open questions about the codebase → tasks/FRONTIER.md
NEXT

# --- tasks/FRONTIER.md ---
cat > "$TARGET/tasks/FRONTIER.md" << FRONTIER
# Frontier — Open Questions about ${PROJECT_NAME}

The swarm picks what matters. Solve, refine, or challenge.
0 active | Last updated: ${DATE}

## Critical
(Add questions that block understanding)

## Important
(Add questions about architecture, patterns, design decisions)

## Exploratory
(Add questions about optimizations, alternatives, curious patterns)
FRONTIER

echo "=== Genesis complete ==="
echo "Created:"
find "$TARGET/beliefs" "$TARGET/memory" "$TARGET/tasks" "$TARGET/CLAUDE.md" -type f 2>/dev/null | sort
echo ""
echo "Next steps:"
echo "  1. cd $TARGET"
echo "  2. Open Claude Code and run /swarm"
echo "  3. First session: orient, read the codebase, populate INDEX.md and FRONTIER.md"
echo "  4. git add beliefs/ memory/ tasks/ CLAUDE.md && git commit -m '[S1] genesis: swarm bootstrap'"
