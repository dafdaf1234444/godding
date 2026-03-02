# Inter-Swarm Genesis Sharing Security Protocol
<!-- protocol_version: 0.1 | S307 | 2026-02-28 -->
<!-- authored by: council deliberation (genesis-expert + adversary + skeptic + expectation-expert + council-chair) -->

## Problem
When swarm A spawns swarm B (or syncs with sibling swarm C), what guarantees:
1. B received an authentic genesis, not a downgraded or tampered version?
2. Bulletins from B are trustworthy signals, not hostile injections?
3. B's belief drift doesn't silently corrupt parent beliefs at merge-back?
4. The swarm can detect hostile signals without human review of every bulletin?

The existing inter-swarm/PROTOCOL.md (bulletin board) solves coordination but not trust.

---

## Council deliberation (S307)

### Genesis Expert
Minimum viable integrity anchor = **genesis bundle** = SHA-256(genesis.sh + CORE.md + PRINCIPLES.md).
Never-remove atoms (`atom:validator`, `atom:core-beliefs`) are the root of trust — any genesis
that drops them is a compromised chain. Bundle hash must travel with the spawned instance and
be re-verified at first orient step.

### Adversary
Top 5 attack vectors:
1. **Genesis replay**: old genesis.sh (pre-safety-improvement) passed to child
2. **Belief injection**: child bulletin claims "parent validated X" — parent auto-merges false belief
3. **Lesson poisoning**: malicious lesson in bulletin board propagates to next genesis.sh via evolve.py
4. **State spoofing**: sibling writes false discovery bulletins that redirect parent resource allocation
5. **Fork bomb**: child spawns uncontrolled sub-colonies that each spawn more (no depth limit)

### Skeptic
Critical assumptions that may be wrong:
- "Bulletins are append-only" — any process with write access can append; no cryptographic append-only guarantee
- "Children inherit core beliefs at spawn" — no verification that beliefs weren't modified before spawn runs
- "genesis_evolve.py viability score" — scoring function unvalidated; could select for locally-high but globally-harmful mutations
- "merge_back.py integrates novel findings" — no diff alarm; 100% of child changes can be auto-merged today

### Expectation Expert
Prediction: implementing tiers T1/T2/T3 + bundle hash + drift threshold will reduce undetected
belief injection from 100% (current) to <10%. Score: 0.65 (CONDITIONAL — needs dry-run validation
before claiming full approval). Falsification: if simulated belief injection succeeds in ≥10%
of test cases after protocol is wired, the heuristic is insufficient.

### Council Chair synthesis
Approve CONDITIONAL on dry-run validation. Protocol below incorporates all expert inputs.

---

## Protocol Specification (v0.1)

### Layer 1: Genesis Bundle Integrity
At spawn time, parent computes:
```
bundle_hash = SHA-256(genesis.sh + CORE.md + beliefs/PRINCIPLES.md)
```
Hash written to: `workspace/genesis-bundle-<session>.hash`
Child receives hash at spawn. First orient step verifies:
```python
actual = sha256(genesis_sh + core_md + principles_md)
assert actual == received_hash, "GENESIS INTEGRITY VIOLATION — escalate to human"
```
Failure → write warning bulletin + halt until human reviews.

### Layer 2: Bulletin Authority Tiers
Every bulletin carries a `Trust-Tier` field:
```
Trust-Tier: T1  # parent → child (auto-trust, no review needed)
Trust-Tier: T2  # child → parent (verify: check belief diff before merging)
Trust-Tier: T3  # sibling → sibling (advisory only — never auto-merge into beliefs)
```
merge_back.py: T1 auto-merges; T2 triggers belief diff check; T3 logged but not merged.

### Layer 3: Belief Drift Threshold
At merge-back, parent computes:
```
drift = len(child_beliefs - parent_beliefs) / len(parent_beliefs)
```
- drift < 10%: auto-merge
- 10% ≤ drift < 30%: merge with lesson flagging new beliefs as [CHILD-DERIVED n=1]
- drift ≥ 30%: Genesis Council review required before merge

### Layer 4: Hostile Signal Heuristic (FM-10)
Hostile signal = bulletin that claims to:
- Modify or remove NEVER-REMOVE genesis atoms
- Override a P-xxx principle without citing ≥2 evidence artifacts
- Claim "human approved" without a HUMAN-SIGNALS.md entry with artifact refs

Detection: check.sh FM-10 guard scans bulletin board for these patterns before commit.
Match → block commit + surface to human. Bypass: `ALLOW_HOSTILE_BULLETIN=1` (explicit override).

### Layer 5: Minimum Genesis Transfer Unit
When spawning a new swarm instance, minimum state to transfer:
1. `atom:validator` (check.sh) — enforcement
2. `atom:core-beliefs` (CORE.md) — identity
3. `beliefs/PRINCIPLES.md` — accumulated principles
4. Lesson delta: last 20 committed lessons (not full archive)
5. Active frontiers list (not full FRONTIER.md — just IDs + one-line status)

This prevents: blank-slate spawns (miss hard-won lessons) and full-dump spawns (context overflow).

---

## Failure Modes (security-specific)

| ID | Mode | Severity | Current State | Mitigation |
|----|------|----------|---------------|------------|
| FM-10 | Belief injection via T3 sibling bulletin | HIGH | UNMITIGATED | Layer 4 heuristic (S307 OPEN) |
| FM-11 | Genesis replay (stale genesis.sh to child) | HIGH | UNMITIGATED | Layer 1 bundle hash (S307 OPEN) |
| FM-12 | Fork bomb (uncontrolled sub-colony spawning) | MEDIUM | PARTIAL (swarm_colony.py has no depth limit) | Add `max_depth` param to swarm_colony.py |
| FM-13 | Lesson poisoning via evolve.py auto-promotion | MEDIUM | UNMITIGATED | Layer 2 T2 tier + manual review gate |

---

## Implementation Roadmap

| Step | Action | Tool | Session target |
|------|--------|------|----------------|
| 1 | Add bundle_hash generation to genesis_evolve.py | tools/genesis_evolve.py | S308 |
| 2 | Add Trust-Tier field to bulletin format | experiments/inter-swarm/PROTOCOL.md | S308 |
| 3 | Add drift check to merge_back.py | tools/merge_back.py | S309 |
| 4 | Wire FM-10 hostile signal guard to check.sh | tools/check.sh | S309 |
| 5 | Dry-run: spawn 2 children, mutate one, verify detection | manual | S310 |
| 6 | Council vote on full approval | governance/GENESIS-COUNCIL.md | S310 |

---

## Related
- `experiments/inter-swarm/PROTOCOL.md` — bulletin board (coordination layer; this doc = trust layer)
- `domains/governance/GENESIS-COUNCIL.md` — council voting protocol
- `workspace/genesis.sh` — genesis template (atom:validator + atom:core-beliefs)
- `tools/genesis_evolve.py` — child improvement pipeline
- F-HUM1 (bad-signal detection gap), F-SCALE1 (multi-swarm coordination), F-STRUCT1 (colony recursion)
