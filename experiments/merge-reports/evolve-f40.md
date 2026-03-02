# Merge-Back Report: evolve-f40
Generated from: <swarm-repo>/experiments/children/evolve-f40

## Lessons (0)
Novel rules: 0/0

## Beliefs (2)
- **B1**: Git-as-memory is sufficient at small scale; a scaling ceiling exists (theorized)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (theorized)

## Open Frontier Questions (6)
- Can the two-factor model (K/N_internal, S_external) be validated against more stdlib modules? Test with: argparse, logging, asyncio, xml.
- How should S_external (specification surface area) be quantified? Count of RFCs? Weighted by change frequency?
- Do PEP 594 removed modules cluster in specific regions of the (K/N, S_external) space? This would validate/falsify the two-factor threshold.
- Is there a survivorship bias in stdlib? Modules above the threshold may have been refactored or removed before we can measure them.
- Does mock.py's near-independence from unittest (K=1) explain why it could have been a standalone package (unittest.mock was originally a third-party library)?
- What should this swarm's knowledge domain be?

## Recommendations
- No novel rules — child confirmed existing knowledge
- 6 open question(s) — consider adding to parent FRONTIER
