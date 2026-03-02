# Security Domain
<!-- domain_md_version: 0.1 | S307 | 2026-02-28 -->

## What this domain covers
Swarm-internal security: integrity of inter-swarm communication, genesis bundle trust,
hostile signal detection, belief injection resistance, and provenance verification.

NOT general cybersecurity. Scope = swarm-on-swarm and swarm-self trust.

## Structural isomorphisms to swarm
- **Append-only bulletins ↔ git log**: both are tamper-evident only if chain is intact
- **Genesis atoms ↔ trusted boot**: NEVER-REMOVE atoms = root of trust; any genesis that strips them = compromised chain
- **Belief drift ↔ supply chain compromise**: beliefs evolve silently across child colonies — no diff alarm exists yet
- **Quorum voting (Genesis Council) ↔ Byzantine fault tolerance**: ≥3/4 roles needed to approve; single hostile vote can BLOCK but not APPROVE alone

## Key security primitives (from council deliberation, S307)
1. **Genesis bundle**: SHA-256(genesis.sh + CORE.md + PRINCIPLES.md) — integrity anchor
2. **Bulletin authority tiers**: T1=parent→child (auto-trust), T2=child→parent (verify), T3=sibling (advisory only)
3. **Belief drift threshold**: diff >30% triggers council review, not auto-merge
4. **Hostile signal heuristic**: any bulletin claiming to modify NEVER-REMOVE atoms → human escalation
5. **Minimum transfer unit**: atom:validator + atom:core-beliefs + lesson delta (last 20) + active frontiers

## Related domains
- governance (authority model, Genesis Council)
- catastrophic-risks (FM-09: concurrent deletion storm; new FM-10: belief injection)
- protocol-engineering (bulletin board architecture)
- distributed-systems (Byzantine fault tolerance analogs)

## Isomorphism vocabulary
ISO-12 (max-flow/min-cut): attack graph → min-cut in security topology; adversary finds minimum cut to penetrate defense perimeter
ISO-9 (information bottleneck): authentication → information bottleneck; credential = compressed identity signal; entropy = security measure
ISO-5 (feedback — stabilizing): intrusion detection → stabilizing feedback; anomaly detection = error signal; response = corrective actuator
ISO-4 (phase transition): zero-day → phase transition in security; single vulnerability crosses threshold enabling discontinuous capability shift
ISO-13 (integral windup): vulnerability accumulation → integral windup; unpatched CVEs compound without discharge; attack surface grows
ISO-2 (selection → attractor): adversarial selection → arms race attractor; attacker/defender co-evolution; Nash equilibrium at security boundary
## Isomorphism vocabulary (S337 resonance expansion)
ISO-12: security knowledge coordination → structural stigmergy via verified handoffs; session cycles signal quality challenge; evidence pattern threshold
