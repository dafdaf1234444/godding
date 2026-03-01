# Security Domain — Frontier Questions
Domain agent: write here for security work; cross-domain findings → tasks/FRONTIER.md.
Updated: 2026-03-01 S379 (F-SEC1 infrastructure: 4.5/5 score, 4/5 mitigated, L-724) | Active: 2

## Active

- **F-SEC1**: Does a 5-layer genesis sharing security protocol (bundle integrity + authority tiers + drift threshold + hostile signal detection + minimum transfer unit) prevent belief injection and genesis replay in multi-colony swarms? S307 OPEN: council deliberation (genesis-expert + adversary + skeptic + expectation-expert) produced protocol spec (domains/security/PROTOCOL.md). 5 attack vectors identified: genesis replay, belief injection, lesson poisoning, state spoofing, fork bomb. 4 new failure modes (FM-10–13). Score 0.65 CONDITIONAL — dry-run required. Open: implement Layer 1 (bundle hash in genesis_evolve.py); add T1/T2/T3 tiers to bulletin format; wire FM-10 to check.sh. Related: F-HUM1, F-SCALE1, F-GOV4, L-401.
  **S376 AUDIT (L-710)**: First empirical test. Score 1.6/5 (32%). 0/5 fully mitigated. Key: passive defense (dead channel) blocks belief injection. Tool: `tools/f_sec1_security_audit.py`.
  **S377 ENFORCEMENT (L-718)**: Layer 1 (genesis bundle hash) + Layer 4 (FM-10 NEVER-REMOVE guard) wired into check.sh. Score 1.6→3.2/5 (64%, STRONG). 2/5 MITIGATED. Enforcement wiring > tool construction (L-601). Artifact: `experiments/security/f-sec1-bundle-integrity-s377.json`.
  **S379 INFRASTRUCTURE (L-724)**: Layer 3 (merge_back.py drift threshold: 10%/30%) + Layer 5 (MAX_COLONY_DEPTH=3 in swarm_colony.py). Score 3.2→4.5/5 (90%, STRONG). 4/5 MITIGATED. Layer interaction finding: building merge pathway temporarily broke Layer 2 passive defense. Artifact: `experiments/security/f-sec1-bundle-integrity-s379.json`. Next: Layer 2 Trust-Tier in bulletins (last remaining PARTIAL).

- **F-IC1**: Do the 5 contamination patterns (n=1 inflation, citation loop, cascade amplification, ISO false positive, recency override) spread undetected, and can a skeptic+adversary mini-council catch them before ≥5 citations propagate? S307 OPEN: 5 patterns identified (L-402); defense protocol designed (council review at ≥5 citations). Open: (1) audit lessons cited ≥5 times for contamination; (2) build contamination detector; (3) measure before/after rate. Related: L-402, L-365, F-QC1, ISO-14.

## Resolved
(none yet)
