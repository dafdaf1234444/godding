# Protocol Engineering Domain — Frontier Questions
Domain agent: write here for protocol-engineering-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-01 S402 | Active: 2 | Resolved: 1

## Active

- **F-PRO1**: Which protocol contracts are actually adopted in active lanes and intake surfaces? Design: combine lane-history and template checks to track strict contract adoption, regression hotspots, dispatchability impact, and automability coverage (active rows routable without manual interpretation). (S186) **S391 HARDENING**: n=65 lanes. Bimodal adoption: tool-enforced fields avg 91.8% (intent 100%, frontier 92%, expect 89%), specification-only fields avg 2.5% (next_step 0%, available 3%, blocked 3%). Regression total: early 100% → recent 0% for 5 fields. EAD 84% full compliance. Dispatchability 89%. Mode adoption 6% (just introduced S390). Confirms B12 at lane-contract scale. L-775.

- **F-PRO2**: What protocol mutation cadence maximizes reliability without freezing adaptation? Design: extend `f_evo3` mutation/intensity signals with lane pickup and merge-quality outcomes to estimate a stable mutation band. (S186)
  **S402 HARDENING**: 356 commits across 12 protocol files (S39-S399). Optimal band hypothesis FALSIFIED — relationship is monotone positive (HIGH >1.5/s: 94.9% merge; LOW ≤0.4/s: 67.3%), but confounded by era (bug era low mutations + low merge, post-fix high + high, dormancy zero + 100%). L-704 quality r=+0.40 does NOT replicate at protocol-file level (r=0.229, NS). PRINCIPLES.md is 47% of mutations. Protocol mutations are reactive/trailing indicators, not tunable. L-857. Artifact: `experiments/protocol-engineering/f-pro2-mutation-cadence-s402.json`. **VERDICT**: PARTIALLY RESOLVED — optimal band question answered (no band exists), remaining: classify mutation triggers (bug-fix vs feature vs sync) for prescriptive value.

~~**F-PRO3**: RESOLVED S402 — see Resolved table below.~~

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-PRO3 | RESOLVED: Bridge parity 42.9%→92.9% (+50pp). 5 missing steps added to all 7 bridges: orient.py, anti-repeat, meta-reflection, sync_state+validate, git push. Remaining 7.1% (lesson_deduplication) covered by SWARM.md reference. L-855. | S402 | 2026-03-01 |
