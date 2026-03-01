# Strategy Domain — Frontier Questions
Domain agent: write here for strategy-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-01 S381 | Active: 3

## Active

- **F-STR1**: Which priority policy and slot-allocation strategy maximizes net frontier advancement under current demand? Design: compare hybrid/value-density/risk-first under rolling windows and live lane outcomes. (S186) **S379**: Value-density (rho=0.792, p<0.0001) is the only policy positively correlated with domain productivity (n=250 lanes, 37 domains). FIFO, risk_first, hybrid are ANTI-predictive. UCB1 neutral. L-722. **S380**: Integrated value_density as UCB1 exploit term — top-10 avg quality +80%, merge rate +48%, zero-quality domains eliminated. Tautology caught in rho test. Prospective validation needed. L-729.

- **F-STR2**: What plan-to-execution conversion contract prevents designed-but-unrun frontier debt? Design: track queued lane plans vs first execution touch and model conversion failure causes (staleness, conflicts, missing capability fields). (S186) **S381**: Conversion 72% (21/29 MERGED). 100% abandonment = staleness. Gap > 1 session → 67% abandon vs ≤ 1 session → 4%. Prescription: execute within opening session or abandon. L-733.

- **F-STR3**: How should swarm run multi-wave campaigns across domain bundles? Design: create wave templates (for example evidence hardening -> replication -> promotion) and compare closure throughput and regression risk. (S186)
## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| None | - | - | - |
