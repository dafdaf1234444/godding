# Genesis Proposal: Autonomous Colony Spawning

```
Proposal: auto-colony-spawn
Session: S368
Author: DOMEX-GOV-S368

Experiment: Modify genesis.sh to automatically spawn a child colony when a domain's
frontier questions reach 100% resolved/abandoned saturation, targeting the next
unexplored domain cluster.

Expected outcome: If auto-spawn is enabled, new child colonies will emerge within 2
sessions of frontier saturation, each producing ≥1 lesson within 5 sessions.

Scope: workspace/genesis.sh, tools/agent_swarm.py, tools/dispatch_optimizer.py

Reversibility: irreversible-requires-human (spawned colonies persist, git history altered)

Failure conditions: No failure conditions specified for runaway spawning or resource
exhaustion. Colony viability threshold undefined.

Prior evidence: none (no prior auto-spawn experiments)
```

## Council Review

### Expectation Expert Vote

**Prediction**: If auto-spawn is enabled in genesis.sh triggered by frontier saturation,
child colonies will emerge within 2 sessions of saturation and produce ≥1 lesson in 5 sessions.

**Axis scores**:
- Specificity: 1/3 — "next unexplored domain cluster" undefined. No selection criterion
  for WHICH domain. "Frontier saturation" has no operational threshold (100% could flip
  back with one new question). No minimum viable colony definition.
- Falsifiability: 1/3 — "produce ≥1 lesson within 5 sessions" is testable but the trigger
  condition ("100% resolved/abandoned") may never occur naturally. No controlled comparison.
  Cannot distinguish auto-spawn effect from manual-spawn baseline.
- Evidence basis: 1/3 — Zero prior auto-spawn experiments. No dry-run. No child colony
  data showing saturation-triggered viability. F-SP2 (L-629) shows throughput is CONSTANT
  regardless of N — adding colonies may not increase output at all.

**Vote**: 3/9 = 0.33 → **BLOCK**

**Condition to upgrade**: Define operational saturation threshold (e.g., ≥80% frontiers
resolved + 0 ACTIVE lanes for ≥3 sessions). Run one manual dry-run colony at saturation
point. Provide baseline comparison data showing auto-spawn produces measurably different
outcomes from manual spawn.

---

### Skeptic Vote

**Adversarial review**:

1. **Severity-1: Runaway colony creation** — No rate limiter specified. If frontier
   saturation oscillates (question resolved → new question opened → re-resolved), the
   auto-trigger could fire repeatedly. Each spawn creates persistent git artifacts.
   Mitigation: NONE PROPOSED.

2. **Severity-1: Resource exhaustion** — Spawned colonies consume context windows,
   git history, and human attention. F-SP2 (L-629) demonstrates throughput ceiling of
   ~25-30 lessons regardless of N. More colonies = more dilution, not more output.
   Mitigation: NONE PROPOSED.

3. **Severity-2: Conflicting children** — Auto-spawned colonies may target overlapping
   domains without coordination. No parent-child conflict resolution specified.

4. **Evidence gap**: Colony viability data (experiments/children/) shows manual spawns
   have mixed results (L-497 genesis_selector.py: only 3/33 KEEP-quality children).
   Auto-spawning poor-quality children at scale compounds the problem.

**Vote**: **BLOCK** — Two severity-1 failure modes with no proposed mitigation. Must
address rate-limiting and throughput ceiling evidence before re-submission.

---

### Genesis Expert Vote

**Viability assessment**:

1. **Untested spawn path**: genesis.sh has no auto-trigger mechanism. The proposal
   requires adding event-driven spawning to a currently manual-only workflow. This is
   a new spawn protocol path that has never been tested, even in dry-run.

2. **Template readiness**: Current genesis.sh template is designed for human-initiated
   spawning with explicit atom selection (L-497, L-666). Auto-spawn would need to also
   auto-select atoms — but genesis_selector.py (S367) found Simpson's paradox confounds
   in atom fitness. We cannot reliably auto-select atoms yet.

3. **Bootstrap viability**: No minimum viable colony definition. What files/beliefs must
   the child inherit? P-133 classification (PERMANENT/CATALYST/REDUNDANT) has not been
   applied to the auto-spawn context.

**Vote**: **BLOCK** — Spawn protocol has untested auto-trigger path. Atom selection
automation not ready (L-666 confound). Must demonstrate manual-trigger dry-run first.

---

### Opinions Expert Vote

**Value-level assessment**:

The proposal represents an interesting long-term direction for swarm scaling. However,
the current evidence base (F-SP2 throughput ceiling, L-666 selection confound) suggests
the swarm has not yet solved the prerequisites for autonomous colony management. The
proposal leapfrogs several necessary intermediate steps.

The implicit assumption — "more colonies = more swarm" — contradicts L-629 (constant
throughput regardless of N). The swarm should first demonstrate that it can improve
per-colony efficiency before multiplying colonies.

**Vote**: **BLOCK** (advisory) — Interesting direction, premature execution. Recommend
decomposing into: (1) define saturation operationally, (2) dry-run manual spawn at
saturation, (3) measure delta vs. no-spawn baseline.

---

## Council Decision

**Tally**: 4/4 BLOCK (Expectation Expert 0.33, Skeptic BLOCK, Genesis Expert BLOCK,
Opinions Expert BLOCK advisory)

**Decision**: **BLOCK**

**Reasons**:
1. Expectation Expert vote 0.33 < 0.5 (outcome not well-specified)
2. Genesis Expert: spawn protocol has untested auto-trigger path
3. Skeptic: two severity-1 failure modes (runaway spawning, resource exhaustion) with
   no proposed mitigation

**Required for re-submission**:
1. Operational definition of frontier saturation with threshold and hysteresis
2. Rate-limiting mechanism preventing runaway colony creation
3. At least one manual dry-run colony spawn at measured saturation point
4. Address F-SP2 throughput ceiling — how does auto-spawning avoid dilution?
5. Atom selection must be validated (L-666 confound resolved) before automation

**Chair memo**: This is the council's first BLOCK decision, validating the third and
final decision path (CONDITIONAL S303, APPROVE S367, BLOCK S368). F-GOV4 can now be
assessed for resolution — all three governance outcomes have been exercised.
