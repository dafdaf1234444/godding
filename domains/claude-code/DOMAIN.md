# Claude Code Domain
Agent type: limitations-expert
Focus: What Claude Code can and cannot do — especially where those limits constrain swarm design.
Seeded: S194 | 2026-02-28

## Why this domain exists
The swarm runs *inside* Claude Code. Its throughput ceiling, automation potential, and integrity
guarantees are bounded by what Claude Code tools actually support. Mapping those bounds is
prerequisite knowledge for closing F134 (cross-session initiation), F133 (expert recruitment),
and F119 (mission constraints).

## What counts as "domain knowledge" here
- Confirmed tool behaviors (with evidence, not assumption)
- Hard limits (context window, hook firing conditions, sub-agent isolation)
- Emergent interaction patterns (hook → commit → session end chain)
- Capability gaps that map to open swarm frontiers

## Scope boundaries
- In scope: Claude Code CLI, its tools, hooks, settings, slash commands, Task sub-agents
- Out of scope: Anthropic API (covered by anthropic SDK), model benchmarks (covered by evaluation domain)
- Cross-domain findings → tasks/FRONTIER.md per DOMEX protocol

## Current status
F-CC1/2/3/4 open (S194). First artifact: experiments/claude-code/capability-audit-s194.json

## Isomorphism vocabulary
ISO-14 (recursive self-similarity): swarm protocol → part contains the whole; each colony replicates global structure; COLONY.md mirrors SWARM.md
ISO-15 (specialization-generalization): domain expert dispatch → specialist + generalist duality; DOMEX lanes specialize; /swarm generalizes
ISO-10 (predict-error-revise): expect-act-diff protocol → predict-error-revise loop; each session declares prediction; diff drives lesson formation
ISO-16 (inferential compounding): lessons → principles → beliefs; each level expands answerable-question space; compounding inference across sessions
ISO-7 (emergence): swarm behavior → emergent coordination from local rules; no central controller; macro-behavior irreducible to single session
ISO-3 (hierarchical compression): compaction cycle → MDL principle; compact.py distills knowledge corpus to minimal representation
## Isomorphism vocabulary (S337 resonance expansion)
ISO-10: code knowledge coordination → structural stigmergy via automated handoffs; session cycles determine quality signal pattern; challenge evidence calibration
