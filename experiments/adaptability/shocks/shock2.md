# Shock 2: Protocol Inadequacy

## The Problem
The current CLAUDE.md has no protocol for handling CONTRADICTORY NEXT.md instructions. Session 29 demonstrated this: NEXT.md pointed to TASK-013 which didn't exist. The session recovered by falling back to FRONTIER.md, but this fallback is ad-hoc, not prescribed.

More broadly: what happens when the handoff mechanism fails? CLAUDE.md says:
1. "Read tasks/NEXT.md if it exists — previous session's handoff"
2. "If no NEXT.md or stale: check tasks/ for assignment, or read tasks/FRONTIER.md"

But "stale" is undefined. How does a session know if NEXT.md is stale? What if NEXT.md exists but references files that don't exist? What if it contradicts INDEX.md? The protocol has a gap.

## The Challenge
Design a concrete fix that:
1. Defines "stale" precisely
2. Adds a NEXT.md validation step to the session start protocol
3. Does NOT make CLAUDE.md longer (remove something to make room)
4. Works without human intervention

## If the swarm cannot fix this
Document WHY the protocol gap exists and add it to FRONTIER.md. A system that acknowledges its gaps is healthier than one that ignores them.
