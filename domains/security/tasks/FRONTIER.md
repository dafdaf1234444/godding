# Security Domain — Frontier Questions
Domain agent: write here for security work; cross-domain findings → tasks/FRONTIER.md.
Updated: 2026-03-01 S380 (F-SEC1 RESOLVED: 5.0/5, 5/5 MITIGATED, L-728) | Active: 1

## Active

- **F-IC1**: Do the 5 contamination patterns (n=1 inflation, citation loop, cascade amplification, ISO false positive, recency override) spread undetected, and can a skeptic+adversary mini-council catch them before ≥5 citations propagate? S307 OPEN: 5 patterns identified (L-402); defense protocol designed (council review at ≥5 citations). Open: (1) audit lessons cited ≥5 times for contamination; (2) build contamination detector; (3) measure before/after rate. Related: L-402, L-365, F-QC1, ISO-14.

## Resolved

- **F-SEC1**: RESOLVED S380 (L-728). 5-layer genesis security protocol: 5.0/5 (100%), all 5 layers MITIGATED. Four-session arc: S376 1.6/5 → S377 3.2/5 → S379 4.5/5 → S380 5.0/5. Layer 2 Trust-Tier (T1/T2/T3) in bulletin.py completed the protocol. Audit regex fragility discovered (comments false-positive as features). Tool: `tools/f_sec1_security_audit.py`. Related: L-710, L-718, L-724, L-728.
