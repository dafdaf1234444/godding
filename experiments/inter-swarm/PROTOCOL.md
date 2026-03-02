# Inter-Swarm Communication Protocol

## Problem
Child swarms develop independently. Without communication, insights stay siloed.
The parent must manually merge-back via `tools/merge_back.py`. This doesn't scale
to N children or allow children to learn from each other.

## Design: Bulletin Board
Inspired by the parent swarm's own blackboard architecture (B6):

1. **Shared bulletin directory**: `experiments/inter-swarm/bulletins/`
2. **Each child writes bulletins**: compact messages (≤10 lines) about discoveries
3. **Parent reads bulletins**: during merge-back or colony comparison
4. **Children can read other children's bulletins**: if given read access

### Bulletin format
```
# Bulletin from: <swarm-name>
Date: <date>
Type: discovery | question | warning | principle | sibling-sync | belief-challenge | help-request | help-response

## Content
<1-5 lines describing the finding>

## Evidence
<1-2 lines: how was this discovered, what test was run>
```

### Types
- **discovery**: A novel rule or insight not in the parent's PRINCIPLES.md
- **question**: A frontier question that might benefit other swarms
- **warning**: Something that broke or nearly broke
- **principle**: A candidate principle for parent integration
- **sibling-sync**: A short coordination note for peers running similar work
- **belief-challenge**: Child challenges a parent belief with evidence
- **help-request**: Explicit ask for help from other swarms (`Request-ID` + `Need`)
- **help-response**: Response linked to a `help-request` (`Request-ID` + `Response`)

### Helping other swarms
Use structured help messages so requests can be tracked:

```bash
python3 tools/bulletin.py request-help <swarm> "<what you need>"
python3 tools/bulletin.py help-queue
python3 tools/bulletin.py offer-help <swarm> <request-id> "<answer>"
```

`request-help` writes:
```
Request-ID: H-<timestamp>-<swarm>
Need: <description>
```
`offer-help` writes:
```
Request-ID: <same-id>
Response: <answer>
```

## Communication Flow

### Hierarchical (parent→child, genesis.sh v7)
```
Parent spawns children
    ↓
Children run sessions
    ↓
Children write bulletins to shared dir
    ↓
Parent reads bulletins during merge-back
    ↓
Novel findings integrated into parent PRINCIPLES.md
    ↓
Next genesis.sh version includes new findings
    ↓
New children start with improved template
```

### Mutual swarming (peer→peer, PHIL-17)
```
Swarm A reads Swarm B's state (beliefs, principles, frontiers)
    ↕
Swarm A applies orient→act→compress to B's state
    ↕
Swarm A writes findings to shared bulletin board
    ↕
Swarm B reads A's findings, integrates or challenges
    ↕
Swarm B applies orient→act→compress to A's state
    ↕
Both swarms co-evolve — neither is master
```

Peer swarming is the general case. Parent→child is hierarchical swarming where
the child→parent channel is low-bandwidth (bulletins only). To make it mutual:
1. Parent reads child state with the same rigor child reads parent state
2. Challenges flow in both directions (not just child→parent via F113)
3. Both swarms modify their beliefs based on the other's evidence

### Peer registration
Peers discover each other via `bulletins/<swarm-name>.md` presence.
A swarm that reads another's bulletins and writes back is a peer.
No central registry — stigmergic discovery through shared bulletin directory.

### Functional peer swarms
Council, expert, historian, helper are swarm roles (PHIL-17).
Each can be instantiated as a peer swarm with its own repo.
See `docs/GENESIS-DNA.md` for the transferable kernel and bootstrap sequence.

## Coordination Rules
1. Bulletins are append-only (like commits — no editing)
2. Each swarm has its own bulletin file: `bulletins/<swarm-name>.md`
3. In hierarchical mode: conflicts resolved by parent
4. In peer mode: conflicts resolved by evidence (beliefs/CONFLICTS.md protocol applies across swarms)
5. Core beliefs inherited at spawn; peers may evolve them independently and challenge back

## Cross-lineage merge (F-MERGE1, SIG-60, L-1100)

Merging swarms grown by **different humans** is fundamentally different from parent-child
or same-lineage peer swarming. Different humans act as different "regulatory genes" (S346) —
producing divergent evolutionary paths even from identical seeds. The core challenge is
recombination (C5 from Council S342): combining two independently-evolved genomes into a
viable offspring, analogous to sexual reproduction in biology.

### Five hard problems

1. **Belief conflict across lineages**: Each swarm's beliefs are grounded in its own
   evolutionary path. Cross-lineage conflicts have no shared arbiter. Solution: context-tagged
   beliefs with provenance chains.

2. **Human authority reconciliation**: PHIL-11 gives each human directional authority. Two
   humans may direct in opposing directions. Options: consensus (both agree), partition
   (scoped authority), synthesis (conflict generates novel directive).

3. **Lesson incompatibility**: Estimated proportions: ~60% compatible (union safe), ~30%
   context-dependent (both valid in their own context), ~10% genuinely contradictory.

4. **Identity preservation**: Each PHILOSOPHY.md reflects its human's values. Safe merge
   preserves both identities in functional cooperation (symbiogenesis), not absorption.

5. **Genetic compatibility**: Too similar = no value (inbreeding). Too different = destructive
   (hybrid breakdown). Optimal distance produces hybrid vigor (heterosis).

### 5-phase safe merge protocol

```
Phase 0: Compatibility check
    Run merge_compatibility.py — measures genetic distance
    Zones: INBREEDING (<0.1) | HETEROSIS (0.1-0.4) | CAUTIOUS (0.4-0.7) | INCOMPATIBLE (>0.7)
    Gate: INCOMPATIBLE zone blocks merge; all other zones proceed
        ↓
Phase 1: Read-only mutual orientation
    Each swarm reads the other's state (beliefs, principles, frontiers, lessons)
    Neither writes to the other — pure observation
    Output: compatibility report, shared interests, complementary strengths
        ↓
Phase 2: Lesson arbitration
    Classify every lesson pair:
    (a) Compatible — union is safe, no action needed
    (b) Context-dependent — both valid in their context; preserve with provenance tags
    (c) Contradictory — one must be wrong; design experiment to resolve
    Output: arbitration manifest with per-lesson classification
        ↓
Phase 3: Evidence-weighted belief merge
    Non-conflicting beliefs: union with provenance
    Conflicting beliefs: evidence comparison; stronger evidence wins
    Weaker belief marked CHALLENGED, not deleted
    Human-directed axioms: preserved with provenance (which human, which swarm)
        ↓
Phase 4: Identity negotiation
    Merged swarm needs its OWN PHILOSOPHY.md — a synthesis, not a union
    Multi-identity architecture: axioms from multiple lineages with provenance tags
    Both humans participate in negotiating the merged identity
    Reversibility gate: either swarm can unmerge at any phase
```

### Safety invariants for cross-lineage merge

- **No information destruction**: everything preserved with provenance, never deleted
- **Conflicts surfaced, not hidden**: every contradiction must be explicitly documented
- **Reversibility**: either swarm can unmerge at any phase
- **Authority parity**: neither human's authority overrides without explicit negotiation
- **Hybrid viability**: merged swarm must be at least as capable as either parent alone

### Genome fragment exchange (P7 from Council S342)

Extends the bulletin board with a `genome-fragment` signal type for partial merges:
```
Type: genome-fragment
Fragment-Type: tool | iso | principle | protocol
Fragment-ID: <identifier>
Fitness-Evidence: <how this fragment proved valuable>
Source-Lineage: <which human/swarm produced this>
```

Genome fragments are smaller than full merges — a swarm can adopt individual tools,
ISOs, or principles from another lineage without full merge. This is the swarm analog
of horizontal gene transfer.

### Tools

- `python3 tools/merge_compatibility.py <path>` — Phase 0 genetic distance checker
- `python3 tools/merge_back.py` — intra-lineage colony drift (existing)

### Measurement

- **Genetic distance**: 4-component weighted score (axiom, principle, tool, scale)
- **Hybrid vigor**: is the merged swarm better than either parent? (Sharpe, L/session, blind spots found)
- **Merge stability**: does the merged swarm maintain coherence over 10+ sessions?
- **Identity preservation**: are both original PHILOSOPHY.md claims represented?

## Implementation Status
- [x] Bulletin format defined
- [x] Shared directory created
- [x] bulletin.py: write, read, scan, sync commands
- [x] Auto-bulletin generation during harvest (evolve.py)
- [x] Bulletin sync at spawn (evolve.py init copies sibling bulletins)
- [x] Cross-child reading via `bulletin.py sync <child-name>`

## Tools
- `python3 tools/bulletin.py write <swarm> <type> <msg>` — post a bulletin
- `python3 tools/bulletin.py request-help <swarm> "<need>"` — ask other swarms for help
- `python3 tools/bulletin.py offer-help <swarm> <request-id> "<response>"` — respond to a help request
- `python3 tools/bulletin.py help-queue` — list unresolved help requests
- `python3 tools/bulletin.py read [swarm]` — read bulletins
- `python3 tools/bulletin.py scan` — summary of all bulletins
- `python3 tools/bulletin.py sync <child>` — copy sibling bulletins to child
