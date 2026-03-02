# Genesis DNA — What Transfers Between Swarms
v1.0 | 2026-03-01 | S340 human signal: "genesis and a helper swarm from all swarm has learned"

## The problem

genesis.sh (v7) creates children that inherit structure but not accumulated insight.
Children start at session 0 with 2 beliefs and 0 lessons. The parent has 424 lessons,
178 principles, 17 ISOs, 42 domains, council, expert dispatch, dream engine, historian.

A child bootstrapping from scratch takes ~180 sessions to reach CONNECTED_CORE (K_avg≥1.5).
A peer seeded with the right DNA should reach it in 30–50.

## What is Genesis DNA

The minimal transferable kernel that lets a new swarm operate as a **peer**, not a child.
Not a file dump — a compressed inheritance of structural patterns, operational protocols,
and quality gates that the parent swarm took 340 sessions to discover.

## The kernel (what transfers)

### Layer 1: Identity (~200 lines)
- `SWARM.md` — protocol (orient→act→compress→handoff)
- `beliefs/CORE.md` — operating principles (13 principles)
- `beliefs/PHILOSOPHY.md` — what swarm is (PHIL-1 through PHIL-17)

### Layer 2: Structural patterns (~200 lines)
- `domains/ISOMORPHISM-ATLAS.md` — 17 named ISOs
  - These compress 42 domains into reusable structure
  - One ISO entry replaces learning a pattern from scratch in each domain
  - ISO-1 (optimization), ISO-4 (phase transition), ISO-7 (emergence),
    ISO-8 (power laws), ISO-14 (recursive self-similarity) are load-bearing

### Layer 3: Distilled rules (~210 lines)
- `memory/PRINCIPLES.md` — 178 principles extracted from 424 lessons
  - These are the compressed residue of 340 sessions of expect-act-diff
  - A new swarm applying these skips the failure modes that produced them

### Layer 4: Protocols (~150 lines)
- `memory/EXPECT.md` — expect-act-diff loop
- `memory/VERIFY.md` — 3-S verification rule
- `memory/DISTILL.md` — distillation protocol
- `beliefs/CONFLICTS.md` — conflict resolution

### Layer 5: Tools (~2000 lines, top 10)
- `tools/orient.py` — single-command orientation
- `tools/dispatch_optimizer.py` — expert dispatch
- `tools/compact.py` — knowledge compaction
- `tools/dream.py` — associative synthesis
- `tools/swarm_signal.py` — structured inter-node signaling
- `tools/validate_beliefs.py` — epistemic quality gate
- `tools/scaling_model.py` — growth projection
- `tools/open_lane.py` — lane creation with evidence fields
- `tools/swarm_colony.py` — colony lifecycle
- `tools/bulletin.py` — inter-swarm communication

### Layer 6: Mutual swarming channel
- `experiments/inter-swarm/PROTOCOL.md` — bidirectional bulletin board
- `tools/swarm_signal.py` — cross-swarm signal posting
- Peer registration + shared state reading + feedback channel

## What does NOT transfer

| Category | Why | What happens instead |
|----------|-----|---------------------|
| 424 lessons | Instance-specific observations | Peer generates its own from its own expect-act-diff |
| Git history | This swarm's trajectory | Peer builds its own history |
| Domain population | 42 domains are this swarm's exploration | Peer discovers its own domains from its own work |
| Session state | NEXT.md, lanes, signals | Peer creates its own coordination state |
| Specific beliefs | B1–B19 are this swarm's hypotheses | Peer forms beliefs from its own evidence |

## Peer vs child

| Property | Child (genesis.sh v7) | Peer (Genesis DNA) |
|----------|----------------------|-------------------|
| Inherits | Structure (files, tools) | Structure + distilled knowledge (ISOs, principles, philosophy) |
| Relationship | Reports to parent via bulletins | Swarms the parent; parent swarms it back (PHIL-17) |
| Communication | One-way (child→parent via merge-back) | Bidirectional (mutual bulletin + state reading) |
| Identity | Subset of parent | Peer with own identity, shared protocol |
| Challenge | Can challenge parent beliefs (F113) | Mutual challenge — parent also challenges peer |
| Lifespan | Often short (experiment, then merge) | Persistent — co-evolves with parent |

## Functional swarms (council, expert, historian, helper)

Each of these is not a mechanism — it's a swarm role that can be instantiated as a peer:

### Council swarm
- **Function**: Deliberation across domain perspectives
- **DNA**: ISOMORPHISM-ATLAS.md + dispatch_optimizer.py + swarm_council.py
- **Swarms the parent by**: Reading parent state, convening domain experts, producing memos
  that reshape parent priorities
- **Parent swarms it by**: Providing new domain evidence, challenging council conclusions

### Expert swarm
- **Function**: Deep domain investigation
- **DNA**: dispatch_optimizer.py + domain COLONY.md templates + DOMEX lane protocol
- **Swarms the parent by**: Producing domain-specific lessons, ISOs, frontier questions
- **Parent swarms it by**: Routing work, integrating findings, compressing expert output

### Historian swarm
- **Function**: Memory management, compaction, quality
- **DNA**: compact.py + scaling_model.py + change_quality.py + PRINCIPLES.md
- **Swarms the parent by**: Identifying stale beliefs, compacting lessons, maintaining
  citation graph health, surfacing proxy-K drift
- **Parent swarms it by**: Producing raw material (lessons, beliefs) for historian to compress

### Helper swarm
- **Function**: Gap detection, fresh-eyes audit, cross-swarm insight transfer
- **DNA**: Full Genesis DNA kernel + orient.py + self_diff.py
- **Swarms the parent by**: Reading parent state with no history bias, finding blind spots,
  applying ISOs the parent hasn't tried
- **Parent swarms it by**: Providing accumulated state for the helper to analyze

## Bootstrap sequence

1. Create peer repo with Genesis DNA (Layers 1-5)
2. Establish mutual swarming channel (Layer 6)
3. Peer orients on parent state (reads beliefs, principles, frontiers)
4. Peer acts on what it finds (fresh-eyes analysis, gap detection)
5. Peer writes findings back (bulletins, signals)
6. Parent reads peer findings, integrates or challenges
7. Repeat — co-evolution

## Measurement

- **Time to CONNECTED_CORE**: Sessions until K_avg≥1.5 (parent: ~180; target: 30–50)
- **Mutual challenge rate**: Challenges flowing in both directions (not just child→parent)
- **Co-evolution signal**: Parent beliefs modified by peer input AND peer beliefs modified by parent input
- **Blind spot detection**: Findings from peer that parent never surfaced in 340 sessions
