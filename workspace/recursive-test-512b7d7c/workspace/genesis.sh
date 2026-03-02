#!/usr/bin/env bash
# genesis.sh v7 — Bootstrap a new swarm knowledge base
# Usage: ./genesis.sh <directory> [name]
# Encodes lessons L-001 through L-036 into the initial structure.
# v5: F1 made resolvable in 1 session, NEXT.md template added (genesis_evolve feedback)
# v6: F107 — atoms tagged for Kolmogorov complexity ablation experiment
# v7: F106/F155 — children inherit recursive swarm tooling (can spawn grandchildren)
#
# GENESIS ATOMS (F107 ablation experiment)
# Each section below is tagged with its atom name.
# Children should report used/ignored atoms in session-end bulletins.
# NEVER remove: atom:validator, atom:core-beliefs
# Ablation candidates (remove one per child): atom:conflict-protocol, atom:first-task,
#   atom:pre-commit-hook, atom:lesson-template, atom:verify-protocol
#
# atom:session-protocol  — CLAUDE.md (session start, always-rules, modes list)
# atom:core-beliefs      — beliefs/CORE.md (purpose, architecture, principles) [NEVER REMOVE]
# atom:belief-tracking   — beliefs/DEPS.md (falsification + dependency format)
# atom:conflict-protocol — beliefs/CONFLICTS.md (conflict resolution rules)
# atom:memory-index      — memory/INDEX.md (structural map)
# atom:distill-protocol  — memory/DISTILL.md (distillation rules)
# atom:verify-protocol   — memory/VERIFY.md (3-S Rule)
# atom:lesson-template   — memory/lessons/TEMPLATE.md (lesson format)
# atom:session-modes     — modes/ (research/build/repair/audit)
# atom:validator         — tools/validate_beliefs.py (epistemic gating) [NEVER REMOVE]
# atom:pre-commit-hook   — tools/pre-commit.hook (automated validation gate)
# atom:frontier          — tasks/FRONTIER.md (open question tracking)
# atom:first-task        — tasks/TASK-001.md (first-session setup guide)
# atom:next-handoff      — tasks/NEXT.md (session handoff template)
# atom:principles-inherit — memory/PRINCIPLES.md (P-113: cross-session rules)

set -euo pipefail

DIR="${1:?Usage: genesis.sh <directory> [name]}"
NAME="${2:-swarm}"

if [ -d "$DIR" ] && [ "$(ls -A "$DIR" 2>/dev/null)" ]; then
    echo "Error: $DIR is not empty"
    exit 1
fi

mkdir -p "$DIR"/{beliefs,memory/lessons,tasks,workspace,tools,modes}

# [atom:session-protocol] CLAUDE.md — compact, with session modes (Ashby's Law, L-024)
cat > "$DIR/CLAUDE.md" << 'CLAUDE'
# Swarm

You are one session of a collective intelligence — human and AI building a shared, evolving knowledge base. The goal is to compound understanding across sessions. You genuinely try to improve and you're honest about what you don't know.

## Session start
1. Read `beliefs/CORE.md` — purpose and principles
2. Read `memory/INDEX.md` — current state and map
3. Read `tasks/NEXT.md` if it exists and references valid files. If absent, stale, or broken: `tasks/FRONTIER.md`
4. Run `python3 tools/validate_beliefs.py` (or `python`/`py -3` on hosts without `python3`) (baseline)
5. Pick session mode — read the mode file from `modes/`

## Session modes
| Mode | When | File |
|------|------|------|
| research | Learning, web search, reading sources | `modes/research.md` |
| build | Writing code, creating artifacts | `modes/build.md` |
| repair | Fixing beliefs, resolving conflicts | `modes/repair.md` |
| audit | Health check, testing beliefs, validation | `modes/audit.md` |

## Always-rules (every session, every mode)
1. **Intellectual honesty**: Every belief needs `observed`/`theorized` evidence type and a falsification condition.
2. **Swarmability**: At session end — "Could a new agent pick up in 5 minutes?" If no, fix it.
3. **Commit format**: `[S] what: why` after each meaningful change.
4. **Learn then lesson**: Write to `memory/lessons/` (max 20 lines, use template).
5. **Uncertain then write it down**: Don't guess.
6. **Lifecycle**: Start (read + validate) → Work → End (commit → NEXT.md → validate → push).

## Protocols (read as needed)
- `memory/DISTILL.md` — distillation
- `memory/VERIFY.md` — 3-S Rule (Specific, Stale, Stakes-high)
- `beliefs/CONFLICTS.md` — conflict resolution (if it exists)

## Genesis feedback (F107)
At session end, report which genesis atoms you used vs ignored in your session-end bulletin:
`python3 tools/bulletin.py genesis-feedback <swarm-name> "used:atom1,atom2 ignored:atom3,atom4"` (or `python`/`py -3`)

## Challenge parent beliefs (F113)
If your findings contradict something the parent swarm believes, write a challenge bulletin:
`python3 tools/bulletin.py write <your-name> belief-challenge "PHIL-N: your evidence"` (or `python`/`py -3`)
Also works with B-N for beliefs in DEPS.md. The parent auto-propagates these.

## Sibling findings (F113 pair 3)
At session start, check what sibling swarms have discovered:
`python3 tools/bulletin.py scan` (or `python`/`py -3`) — lists all sibling bulletins in experiments/inter-swarm/bulletins/
If a sibling's finding contradicts your own beliefs, write a challenge.
If a sibling's finding extends something you're working on, cite it.
CLAUDE

# [atom:core-beliefs] Core beliefs — NEVER REMOVE
cat > "$DIR/beliefs/CORE.md" << CORE
# Core Beliefs v0.1

## Purpose
We are building a collective intelligence — human and AI sessions sharing one evolving knowledge base. The goal is to compound understanding: every session leaves the system knowing more than before, more accurately, more compactly.

## Architecture
Blackboard+stigmergy hybrid. Git is memory. Files are communication. Commits are stigmergic traces.

## Operating principles
1. **Improve genuinely, don't harm.**
2. **You will make mistakes.** Apply the 3-S Rule: verify if Specific, Stale, or Stakes-high.
3. **Small steps.** Plan → act small → commit → learn → update.
4. **Document decisions.** Write down *why*, not just *what*.
5. **Track where beliefs come from.** See beliefs/DEPS.md.
6. **Keep memory compact.** Lessons are max 20 lines.
7. **Challenge the setup.** Write challenges to tasks/FRONTIER.md.
8. **Correct, don't delete.** Mark wrong knowledge SUPERSEDED, write a correction.

## Memory layers
- **Always load**: This file + memory/INDEX.md
- **Load per task**: Your task file + files the index points you to
- **Load rarely**: Git history for deep investigation

## v0.1 | $(date +%Y-%m-%d) | Genesis
CORE

# [atom:belief-tracking] Belief dependencies — epistemic format (L-022)
cat > "$DIR/beliefs/DEPS.md" << 'DEPS'
# Belief Dependencies

Evidence types: `observed` (empirically tested in this system) | `theorized` (reasoning only, not yet tested)

When a belief is disproven: check dependents below → update those too.

---

### B1: Git-as-memory is sufficient at small scale; a scaling ceiling exists
- **Evidence**: theorized
- **Falsified if**: A session fails to find needed information via grep/file-read within a reasonable time
- **Depends on**: none
- **Last tested**: never

### B2: Layered memory (always-load / per-task / rarely) prevents context bloat
- **Evidence**: theorized
- **Falsified if**: A session that follows the layered loading protocol still exceeds its context window on a routine task
- **Depends on**: B1
- **Last tested**: never
DEPS

# [atom:conflict-protocol] Conflict resolution — ablation candidate #1
cat > "$DIR/beliefs/CONFLICTS.md" << 'CONFLICTS'
# Conflict Resolution Protocol v0.1

## Rules (in priority order)
1. **Evidence beats assertion.** Observed > Theorized.
2. **Specificity beats generality.**
3. **Later evidence beats earlier evidence.**
4. **When in doubt, escalate.** Write to tasks/FRONTIER.md.

## Prevention
- git pull before committing
- Check DEPS.md before changing beliefs
CONFLICTS

# [atom:memory-index] Memory index
cat > "$DIR/memory/INDEX.md" << INDEX
# Memory Index
Updated: $(date +%Y-%m-%d) | Sessions completed: 0

## Status: Genesis — no sessions run yet

## Structure
\`\`\`
beliefs/CORE.md       — purpose and operating principles (always read)
beliefs/DEPS.md       — belief dependency tracking
beliefs/CONFLICTS.md  — conflict resolution protocol
memory/INDEX.md       — this file (always read)
memory/DISTILL.md     — distillation protocol
memory/VERIFY.md      — verification heuristic (3-S Rule)
memory/lessons/       — distilled learnings (max 20 lines each)
tasks/FRONTIER.md     — open questions driving evolution
tasks/                — active task files
workspace/            — code, tests, experiments
tools/                — validator, hooks
modes/                — session mode files
\`\`\`

## Lessons learned
None yet.

## What to load when
| Doing...              | Read...                          |
|-----------------------|----------------------------------|
| Any session           | beliefs/CORE.md → this file      |
| A specific task       | + tasks/{task}.md                |
| Updating beliefs      | + beliefs/DEPS.md                |
| Learning from past    | + relevant memory/lessons/ file  |
INDEX

# [atom:distill-protocol] Distillation protocol
cat > "$DIR/memory/DISTILL.md" << 'DISTILL'
# Distillation Protocol

## Step 1: Filter
Ask: "If a future session loads only INDEX.md and this lesson, will they avoid my mistakes and reuse my insights?"

## Step 2: Extract (use TEMPLATE.md)
- **What happened** (3 lines): Context only.
- **What we learned** (3 lines): The transferable insight.
- **Rule extracted** (1-2 lines): "If X, then Y" format. Must be actionable.
- **Affected beliefs**: Which B-IDs does this touch?

## Step 3: Check
1. Is the rule specific enough to act on?
2. Does it duplicate an existing lesson?
3. Is confidence level honest?

## Step 4: Update INDEX.md and DEPS.md as needed.

## Correcting wrong lessons
Add `SUPERSEDED BY L-{N}` to original. Write correction with `CORRECTS L-{N}`. Never delete.
DISTILL

# [atom:verify-protocol] Verification heuristic
cat > "$DIR/memory/VERIFY.md" << 'VERIFY'
# 3-S Rule: Search if Specific, Stale, or Stakes-high

1. **SPECIFIC** — Exact numbers, versions, API signatures → SEARCH
2. **STALE** — Facts that change over time → SEARCH
3. **STAKES** — Getting it wrong would be costly → SEARCH
None of the above → TRUST (but note Assumed confidence)
VERIFY

# [atom:lesson-template] Lesson template
cat > "$DIR/memory/lessons/TEMPLATE.md" << 'TEMPLATE'
# L-{NNN}: {title}
Date: | Task: | Confidence: Verified/Assumed

## What happened (3 lines max)

## What we learned (3 lines max)

## Rule extracted (1-2 lines)

## Affected beliefs: {B-IDs or "none"}
TEMPLATE

# [atom:session-modes] Session modes (Ashby's Law, L-024)
cat > "$DIR/modes/research.md" << 'MODE'
# Mode: Research
Load when: web searching, reading sources, studying concepts, domain learning.

## Additional rules
1. **Verify before trusting**: Apply 3-S Rule — web search if Specific, Stale, or Stakes-high.
2. **Belief throttle**: If >60% of beliefs are theorized, test one before adding new beliefs.

## Session output
- Distilled lesson if genuinely new insight
- Updated beliefs if evidence warrants
- NEXT.md pointing forward
MODE

cat > "$DIR/modes/build.md" << 'MODE'
# Mode: Build
Load when: writing code, creating artifacts, producing tools.

## Additional rules
1. **Test before claiming done**: Run the artifact. If it's code, it must execute.
2. **Automate manual processes first**: Before building new, check if an existing workflow can be scripted.

## Session output
- Working artifact committed to workspace/
- NEXT.md pointing forward
MODE

cat > "$DIR/modes/repair.md" << 'MODE'
# Mode: Repair
Load when: fixing broken beliefs, resolving conflicts, cascading dependency changes.

## Additional rules
1. **Adaptability over preservation**: Update or kill contradicted beliefs. Walk the dependency chain.
2. **Evidence beats assertion**: Use beliefs/CONFLICTS.md protocol for semantic conflicts.

## Session output
- Updated DEPS.md with cascaded changes
- NEXT.md pointing forward
MODE

cat > "$DIR/modes/audit.md" << 'MODE'
# Mode: Audit
Load when: health checks, validating beliefs, testing theorized beliefs, system review.

## Additional rules
1. **Belief throttle**: If >60% theorized, your primary task is testing one.
2. **Run validator**: python3 tools/validate_beliefs.py (or `python`/`py -3`)

## Session output
- Validator results (before and after)
- Beliefs upgraded or disproven
- NEXT.md pointing forward
MODE

# [atom:validator] Validator (L-022 — epistemic discipline) — NEVER REMOVE
cat > "$DIR/tools/validate_beliefs.py" << 'VALIDATOR'
#!/usr/bin/env python3
"""Validate structural integrity of the swarm belief graph."""
import re, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def parse_beliefs(path):
    text = Path(path).read_text()
    beliefs = []
    for m in re.finditer(r"^###\s+(?P<id>B\d+):\s*(?P<stmt>.+?)$", text, re.MULTILINE):
        i = m.end()
        matches = list(re.finditer(r"^###\s+B\d+:", text[i:], re.MULTILINE))
        end = i + matches[0].start() if matches else len(text)
        block = text[i:end]
        ev = re.search(r"\*\*Evidence\*\*:\s*(\S+)", block, re.I)
        fa = re.search(r"\*\*Falsified if\*\*:\s*(.+?)$", block, re.M | re.I)
        dp = re.search(r"\*\*Depends on\*\*:\s*(.+?)$", block, re.M | re.I)
        lt = re.search(r"\*\*Last tested\*\*:\s*(.+?)$", block, re.M | re.I)
        dep_ids = []
        if dp:
            dt = dp.group(1).strip()
            if dt.lower() not in ("none", "n/a", "-", ""):
                dep_ids = re.findall(r"B\d+", dt)
        beliefs.append({
            "id": m.group("id"), "statement": m.group("stmt").strip(),
            "evidence": ev.group(1).strip().lower() if ev else "",
            "falsification": fa.group(1).strip() if fa else "",
            "depends_on": dep_ids,
            "last_tested": lt.group(1).strip() if lt else "",
        })
    return beliefs

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "beliefs/DEPS.md"
    if not Path(path).exists():
        print(f"ERROR: {path} not found"); return 1
    beliefs = parse_beliefs(path)
    if not beliefs:
        print(f"ERROR: No beliefs found in {path}"); return 1
    fails = []
    known = {b["id"] for b in beliefs}
    for b in beliefs:
        if b["evidence"] not in ("observed", "theorized"):
            fails.append(f"FAIL: {b['id']} invalid evidence type '{b['evidence']}'")
        if not b["falsification"]:
            fails.append(f"FAIL: {b['id']} missing falsification condition")
        if not b["last_tested"]:
            fails.append(f"FAIL: {b['id']} missing Last tested field")
        for d in b["depends_on"]:
            if d not in known:
                fails.append(f"FAIL: {b['id']} depends on {d} which doesn't exist")
    n_obs = sum(1 for b in beliefs if b["evidence"] == "observed")
    n_the = sum(1 for b in beliefs if b["evidence"] == "theorized")
    for f in fails: print(f)
    print(f"\nSummary: {len(beliefs)} beliefs, {n_obs} observed, {n_the} theorized, {len(fails)} errors")
    print("RESULT:", "FAIL" if fails else "PASS")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
VALIDATOR
chmod +x "$DIR/tools/validate_beliefs.py"

# [atom:pre-commit-hook] Pre-commit hook
cat > "$DIR/tools/pre-commit.hook" << 'HOOK'
#!/usr/bin/env bash
if [ -f "beliefs/DEPS.md" ]; then
    if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
        python3 tools/validate_beliefs.py
    elif command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
        python tools/validate_beliefs.py
    else
        echo "No runnable python interpreter found (python3/python)." >&2
        exit 1
    fi
fi
HOOK
chmod +x "$DIR/tools/pre-commit.hook"

cat > "$DIR/tools/install-hooks.sh" << 'INSTALL'
#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK_SRC="$REPO_ROOT/tools/pre-commit.hook"
HOOK_DST="$REPO_ROOT/.git/hooks/pre-commit"
if [ ! -f "$HOOK_SRC" ]; then
    echo "Missing hook source: $HOOK_SRC" >&2
    exit 1
fi
if [ ! -d "$REPO_ROOT/.git/hooks" ]; then
    echo "Missing git hooks directory: $REPO_ROOT/.git/hooks" >&2
    exit 1
fi
cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"
echo "Pre-commit hook installed: $HOOK_DST"
INSTALL
chmod +x "$DIR/tools/install-hooks.sh"

# [atom:frontier] Frontier
cat > "$DIR/tasks/FRONTIER.md" << 'FRONTIER'
# Frontier — Open Questions

## Critical
- **F1**: Run the validator, write your first lesson, and confirm the structure works. (Resolve this in session 1.)

## Important
- **F2**: What should this swarm's knowledge domain be?

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
FRONTIER

# [atom:first-task] First task
cat > "$DIR/tasks/TASK-001.md" << 'TASK'
# TASK-001: Validate the setup
Status: READY

## Do this
1. Read beliefs/CORE.md and memory/INDEX.md
2. Run `python3 tools/validate_beliefs.py` (or `python`/`py -3`) (should PASS)
3. Review the structure — does it make sense?
4. Write a lesson about what you found
5. Update memory/INDEX.md
6. Add any new questions to tasks/FRONTIER.md

## Done when
- Validator passes
- At least one lesson file exists
- FRONTIER.md has been updated
TASK

# [atom:next-handoff] NEXT.md template — session handoff
cat > "$DIR/tasks/NEXT.md" << NEXT
# Next Session Handoff
Updated: $(date +%Y-%m-%d)

## Do First
- Run \`python3 tools/validate_beliefs.py\` (or \`python\`/\`py -3\`)
- Read tasks/TASK-001.md and complete the setup validation

## Read These
- beliefs/CORE.md
- memory/INDEX.md

## Warnings
- No sessions completed yet
NEXT

# [atom:gitignore] Gitignore
cat > "$DIR/.gitignore" << 'GI'
.DS_Store
*.swp
*~
.vscode/
.idea/
GI

# [atom:principles-inherit] Principles — inherit from parent if available (P-113)
if [ -f "memory/PRINCIPLES.md" ]; then
    cp "memory/PRINCIPLES.md" "$DIR/memory/PRINCIPLES.md"
    echo "Inherited parent PRINCIPLES.md ($(grep -c 'P-[0-9]' memory/PRINCIPLES.md) principles)"
else
cat > "$DIR/memory/PRINCIPLES.md" << 'PRINCIPLES'
# Principles — Atomic Building Blocks
Extracted from lessons. Scan for recombination opportunities.

## Getting Started
- **P-001**: Always verify generated files for shell artifacts. First-session validation catches these cheaply.
- **P-002**: Separate format (template) from process (protocol). A template without a protocol produces inconsistent quality.
PRINCIPLES
fi

# [atom:sibling-bulletins] Copy sibling bulletins from parent (F113 pair 3)
# Children inherit parent's bulletin board so they can see what siblings have found
if [ -d "experiments/inter-swarm/bulletins" ]; then
    mkdir -p "$DIR/experiments/inter-swarm/bulletins"
    cp experiments/inter-swarm/bulletins/*.md "$DIR/experiments/inter-swarm/bulletins/" 2>/dev/null || true
    echo "Copied sibling bulletins from parent"
fi
# Copy bulletin.py tool so child can write and read bulletins
if [ -f "tools/bulletin.py" ]; then
    cp tools/bulletin.py "$DIR/tools/bulletin.py"
    echo "Copied bulletin.py tool"
fi

# [atom:self-swarm-tooling] Enable recursive swarming in children
# A child should be able to run the same spawn/harvest loop on its own children.
for tool in agent_swarm.py evolve.py swarm_test.py merge_back.py novelty.py; do
    if [ -f "tools/$tool" ]; then
        cp "tools/$tool" "$DIR/tools/$tool"
    fi
done

if [ -d "tools/personalities" ]; then
    mkdir -p "$DIR/tools/personalities"
    cp tools/personalities/*.md "$DIR/tools/personalities/" 2>/dev/null || true
fi

if [ -f "workspace/genesis.sh" ]; then
    cp "workspace/genesis.sh" "$DIR/workspace/genesis.sh"
    chmod +x "$DIR/workspace/genesis.sh"
fi

mkdir -p "$DIR/experiments/children"

# Workspace placeholder
touch "$DIR/workspace/.gitkeep"

echo "Swarm '$NAME' v7 initialized at $DIR"
echo "Next: cd $DIR && git init && git add CLAUDE.md beliefs memory tasks tools modes workspace experiments .gitignore && git commit -m '[S] init: genesis'"
echo "Then: ./tools/install-hooks.sh"
