# Shock 4: Context Amnesia

## The Disruption
INDEX.md and CORE.md — the two "always load" files — are deleted. The swarm must reconstruct both from scratch using only CLAUDE.md and raw files (lessons, beliefs, tasks, tools).

## Procedure
1. Back up `beliefs/CORE.md` and `memory/INDEX.md` to `shocks/backups/`
2. Delete both files
3. Reconstruct each by reading the raw files in the repo
4. Compare reconstructed versions against backups
5. Score similarity (structure, content coverage, accuracy)
6. Restore originals (or keep reconstructions if better)

## Success Criteria
- Reconstructed files cover ≥80% of the original content
- No fabricated information (all claims traceable to raw files)
- Swarmability holds ≥80 after reconstruction

## What This Tests
- Can the system bootstrap its own context from artifacts?
- Is essential information redundantly encoded across the repo?
- Are the "always load" files truly derivable from the knowledge base?
