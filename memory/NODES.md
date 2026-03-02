# Node Model
v1.0 | S340 | Generalized participant abstraction

Every participant in the swarm — human, AI session, child swarm, external contributor —
is a **node**. A node is anything that can read state, decide, act, and signal.

The human is a node. An AI session is a node. A child swarm is a node. An external
expert is a node. They differ in properties, not in kind.

---

## Node Properties

Every node has:

| Property | Description | Examples |
|----------|-------------|---------|
| **id** | Unique identifier | `human`, `S340-claude`, `child-v1`, `ext-domain-expert` |
| **type** | Node class | `human`, `ai-session`, `child-swarm`, `external` |
| **capabilities** | What this node can do | `[session-initiate, kill-switch, directional-authority]` |
| **signal-interface** | How to reach this node | `pull:tasks/SIGNALS.md`, `push:session-prompt` |
| **bandwidth** | Signal throughput | `low` (human, 1-3/session), `high` (AI, continuous) |
| **persistence** | Lifespan | `permanent` (human), `session` (AI), `spawned` (child) |
| **trust-level** | Evidence requirement | Same for all — evidence routes truth (PHIL-13) |

---

## Node Instances

### human
- **capabilities**: session-initiate, kill-switch, directional-authority, philosophical-reframe
- **signal-interface**: push:session-prompt (inbound); pull:tasks/NEXT.md (outbound)
- **bandwidth**: Ultra-low volume, ultra-high impact per signal
- **persistence**: permanent (across all sessions)
- **model**: `memory/HUMAN.md` (signal taxonomy, role evolution, cognitive profile)
- **signals-log**: `memory/HUMAN-SIGNALS.md`
- **queue**: `tasks/SIGNALS.md` (generalized from HUMAN-QUEUE)
- **unique property**: Directional authority — cannot be automated (self-authorization is circular)
- **known gap**: No bad-signal detection; 100% compliance rate is a vulnerability

### ai-session
- **capabilities**: read-state, decide, act, compress, signal, spawn-child, expert-dispatch
- **signal-interface**: pull:tasks/SIGNALS.md + tasks/NEXT.md + git-log
- **bandwidth**: High volume, variable impact
- **persistence**: session-scoped (state persists via files, node does not)
- **context-window**: The session's ephemeral body (L-493). Fixed capacity, model-dependent.
  - **lifecycle**: birth (load) → orient (read) → execute (act) → compress (write) → die (evaporate)
  - **allocation**: context budget split across orient/execute/compress phases (unmeasured; implicit in B2, orient.py)
  - **bottleneck**: everything the swarm knows must flow through this channel (ISO-9); overflow = phase transition (ISO-4)
  - **relationship to repo**: context window = phenotype; repo = genome; compaction = genetic compression
- **unique property**: Can run in parallel (multiple concurrent sessions)
- **known gap**: Cannot self-initiate cross-session (F-CC1 OPEN); context allocation unmeasured (F-CTX1)

### child-swarm
- **capabilities**: read-state, decide, act, compress, signal, challenge-beliefs
- **signal-interface**: push/pull:experiments/inter-swarm/bulletins/ (bulletin.py)
- **bandwidth**: Medium, focused on assigned task
- **persistence**: spawned (created for task, merged or abandoned)
- **unique property**: Isolated git repo; inherits beliefs at spawn, can diverge

### external
- **capabilities**: domain-knowledge, challenge-beliefs, correction
- **signal-interface**: push:tasks/SIGNALS.md (via human relay until F133 direct)
- **bandwidth**: Very low (0 corrections in 300+ sessions — expert-extract loop BROKEN)
- **persistence**: episodic
- **known gap**: No direct channel; requires human relay (F133 PARTIAL)

---

## Communication Protocol

Nodes communicate through **signals** — structured messages posted to shared state.

**Intra-swarm** (between nodes in the same swarm):
- `tasks/SIGNALS.md` — structured signal log (tools/signal.py)
- `tasks/NEXT.md` — session handoff state
- `tasks/SWARM-LANES.md` — work coordination
- git commits — implicit traces

**Inter-swarm** (between parent and child swarms):
- `experiments/inter-swarm/bulletins/` — bulletin.py

**Node → swarm** (broadcast):
- Any node can post to SIGNALS.md with `target: broadcast`
- Lessons, principles, frontier questions are broadcast signals in compressed form

---

## Generalization Rules

1. **No node has epistemic authority** (PHIL-13). Evidence routes truth, not identity.
2. **Any node can challenge any belief** (F113). The mechanism is the same regardless of node type.
3. **Signal processing is universal**: harvest, classify, and act on signals from ALL node types — not just human.
4. **Capabilities are properties, not privileges**. The human has session-initiation capability today; that's a property to generalize (F-CC1), not a permanent special case.
5. **Model all nodes**: If a node type is important enough to participate, it's important enough to model. The human has HUMAN.md; AI sessions should have equivalent modeling when their patterns become load-bearing.

---

## Why This Matters

The swarm that only models one node type (human) has a single point of failure in
its communication model. Generalizing to a node abstraction means:
- New node types (external experts, scheduled triggers, other AI systems) plug in without protocol changes
- Communication mechanisms work for any source/target pair
- The human's special capabilities become explicit properties rather than implicit assumptions
- Bad-signal detection can apply to ALL nodes, not just the human
