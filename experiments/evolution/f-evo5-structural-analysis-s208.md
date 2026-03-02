# F-EVO5 Structural + Skeptic Analysis (S208)
Date: 2026-02-28
Source: experiments/evolution/f-evo5-self-archaeology-s195.json

## Structural analysis
- Growth phases show a long low-growth plateau (S114–S180, 0.48 L/session) followed by a surge (S180–S190, 5.3 L/session). The surge contains the largest domain bursts (S186: 13 domains; S188: 4 domains), indicating size growth is tightly coupled to domain seeding rather than steady incremental additions.
- Domain births are episodic: early base (S50–S52) then a long gap until S178–S180, then burst sessions (S186/S188). Structural pattern: expansion happens in discrete bursts, not continuous drift.
- Tool births total 148 with a heavy "other" category (65, 44%). Ops-core (14) and operations (12) are the next largest. This suggests either the taxonomy is too coarse or growth is dominated by tests/one-off utilities; structural coupling likely hides in "other".
- Tool-birth clustering around S186 aligns with the largest domain-burst session, reinforcing that domain seeding and tooling proliferation are linked events.

## Skeptic challenges
- Growth-phase boundaries are based on L-only deltas; P, B, F missingness and mixed provenance (git-log vs SESSION-LOG) can shift boundaries. Test whether the S180–S190 spike remains when segmentation uses L+P and only git-log sessions.
- The S114–S180 plateau may be averaging across smaller bursts. A change-point detection over L/P and domain births may yield different epoch boundaries and shift the "growth epoch" narrative.

## Next checks
1. Re-segment growth phases using L+P deltas with sessions sourced only from git-log to avoid mixed provenance.
2. Split "other" tool births into at least: tests, maintenance, analysis, and one-off utilities. Recompute category counts.
3. Compute correlation between per-session domain_birth_count and dL to verify coupling strength.
