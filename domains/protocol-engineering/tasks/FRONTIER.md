# Protocol Engineering Domain — Frontier Questions
Domain agent: write here for protocol-engineering-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-02-27 S186 | Active: 3

## Active

- **F-PRO1**: Which protocol contracts are actually adopted in active lanes and intake surfaces? Design: combine lane-history and template checks to track strict contract adoption, regression hotspots, dispatchability impact, and automability coverage (active rows routable without manual interpretation). (S186) **S391 HARDENING**: n=65 lanes. Bimodal adoption: tool-enforced fields avg 91.8% (intent 100%, frontier 92%, expect 89%), specification-only fields avg 2.5% (next_step 0%, available 3%, blocked 3%). Regression total: early 100% → recent 0% for 5 fields. EAD 84% full compliance. Dispatchability 89%. Mode adoption 6% (just introduced S390). Confirms B12 at lane-contract scale. L-775.

- **F-PRO2**: What protocol mutation cadence maximizes reliability without freezing adaptation? Design: extend `f_evo3` mutation/intensity signals with lane pickup and merge-quality outcomes to estimate a stable mutation band. (S186)

- **F-PRO3**: How complete is cross-tool protocol parity? Design: audit bridge entry files against `SWARM.md` canonical requirements and measure parity drift over session windows. (S186)
## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| None | - | - | - |
