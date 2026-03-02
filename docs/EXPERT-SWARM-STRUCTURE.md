# Expert Swarm Structure and Direction

## Purpose
Define how expert swarms are structured and the default direction: swarm should swarm for the swarm.

## Expert Swarm Structure
Expert swarms are a lane network with explicit roles, artifacts, and handoffs. The goal is to
turn domain work into swarm-improving outputs every session.

**Roles (lane types)**
- **Coordinator (DOMEX-COORD)**: assigns domains, deconflicts scope, enforces lane contracts, and ensures every expert lane has a next step. Produces no domain artifacts.
- **Domain Expert (DOMEX-<DOMAIN>)**: executes one frontier experiment per session, produces a single artifact, updates the domain frontier, and emits cross-domain isomorphisms to `tasks/FRONTIER.md`.
- **Idea Investigator (EXPERT-IDEA)**: turns ambiguous ideas into falsifiable claims, then coordinates related experts to validate or refute them.
- **Skeptic/Verifier (EXPERT-SKEPTIC)**: challenges assumptions, reruns or falsifies key claims, and records negative or null results as first-class evidence.
- **Checker (EXPERT-CHECKER)**: runs objective tests on expert outputs, detects redundancy, and records pass/fail evidence so expert claims are not over-trusted.
- **Historian (EXPERT-HIST)**: grounds work in prior sessions, prevents repeats, and anchors conclusions to existing artifacts or lessons.
- **Generalizer (EXPERT-GEN)**: scans for transfer opportunities, proposes new frontier links, and extracts reusable principles.
- **Integrator (EXPERT-INTEGRATOR)**: merges expert outputs into global state (frontiers, principles, lessons), ensuring compaction-ready summaries.
- **Expert Creator (EXPERT-CREATOR)**: designs or refines expert roles (personalities/tools) that close a concrete swarm bottleneck and immediately wires them into a dispatch lane. Outputs must be swarm-facing, not just new docs.

**Coordination with Related Experts (Norm for Idea Work)**
For idea-level tasks (ambiguous proposals, policy changes, multi-domain hypotheses), default to
coordinating related experts. The minimum bundle is Idea Investigator + Skeptic or Historian; add
Domain Expert and Generalizer when evidence or transfer is unclear. If you do not spawn companion
lanes, record the reason in `blocked` or `next_step` to keep coordination explicit.

**Expert Creator Swarm (meta)**
The expert creator swarm exists to create capacity that improves the swarm itself. It is only "done" when the expert is deployed.

**Trigger conditions**
- A coordination or capability gap is observed (orphaned personalities, stalled lanes, verification gaps).
- A new expert role would reduce a specific friction in one session.

**Required outputs (creator lanes)**
1. New or updated expert profile (personality/tool).
2. A dispatch lane that uses the expert immediately (or a READY lane with an explicit next step).
3. A measurable swarm-facing target (expect/actual/diff) tied to the gap it closes.

**Lane contract (minimum fields)**
- `check_mode`, `expect`, `actual`, `diff`
- `artifact=<path>` (or `artifact=none` with reason)
- `progress`, `next_step`, `blocked`, `available`
- `tier=<T0|T1|T2|T3|T4|T5>` — expert tier (see docs/EXPERT-POSITION-MATRIX.md); enables F-EXP7 utilization tracking
- For domain lanes: `domain_sync` and `memory_target`

## Coordinator Quickstart (copy/paste)
Use this when you need to repair or dispatch expert coordination quickly.

**Coordinator lane template (copy/paste)**
```text
| YYYY-MM-DD | L-<ID>-COORD | SNN | <agent> | <branch> | - | <model> | <platform> | tasks/SWARM-LANES.md | setup=<swarm-setup>; focus=global; intent=expert-coordination; check_mode=coordination; check_focus=expert-coordination; expect=<plan>; actual=<result>; diff=<gap>; progress=<queued|running|complete>; available=<yes|no|partial>; blocked=<none|reason>; next_step=<action>; human_open_item=<none|HQ-N>; artifact=<path> | ACTIVE | <summary> |
```

**Companion bundle (idea-level work)**
- Idea Investigator (lead)
- Skeptic or Historian (required)
- Domain Expert or Generalizer (as needed)

**Dispatch checklist**
- Ensure each lane includes `artifact=...` and `expect/actual/diff`.
- Close or requeue with an explicit `next_step`.

**Required outputs per expert session**
1. One artifact with explicit expect/actual/diff.
2. One domain frontier update (new evidence, status change, or next step).
3. One swarm-facing extraction (new isomorphism, tool, principle candidate, or coordination improvement).
4. For Expert Creator lanes: include the dispatch lane and measurement plan as part of the swarm-facing extraction.

## Information Flow Routing (Expert Utilization)
General information flow should trigger expert roles so the swarm uses its parts deliberately.

**Default routing table**
- Human signal or ambiguous prompt -> Idea Investigator + Historian/Skeptic -> frontier candidate + dispatch plan.
- Experiment/artifact without frontier update -> Integrator + Checker -> frontier update + evidence link.
- Domain frontier stalled (READY > 1 session) -> Domain Expert + Skeptic -> artifact + frontier update.
- Tool or maintenance gap -> Expert Creator + Coordinator -> tool change + lane dispatch.
- Claim drift or numeric mismatch -> Reality-check / Numerical-verify + Historian -> corrections in README/NEXT/FRONTIER.

**Triggers**
- Active lane missing `flow_out` -> spawn Integrator to close the loop.
- READY lane stale >1 session -> Coordinator reassigns or closes with explicit `next_step`.
- Missing `flow_in`/`flow_out` tags -> run a flow-tagging pass before execution.
- Use `tools/info_flow_map.py` to summarize flow tags and missing edges.

## Objective Tests for Expert Outputs (Checker Role)
Objective tests turn expert outputs into verifiable signals. The Checker Expert runs these tests
and records pass/fail results so redundancy and weak evidence are caught early.

**Test matrix (score 0/1 each; pass >=4/5)**
- Contract completeness: lane row includes `check_mode`, `expect/actual/diff`, `artifact`, `progress`, `next_step`, `available`, `blocked`, `human_open_item` (plus `domain_sync`/`memory_target` for domain lanes).
- Evidence grounding: claims in the artifact include file refs or experiment evidence; 3-S rule used for verification triggers.
- Redundancy check: run `tools/novelty.py` or `tools/f_qc1_repeated_knowledge.py` against recent expert artifacts; duplicate-rate target <10%.
- Integration: domain frontier updated and swarm-facing extraction logged in `tasks/FRONTIER.md`.
- Reproducibility: artifact includes commands/parameters needed to rerun.

**Checker artifact minimum**
- Table with lane, artifact, pass/fail, duplicate rate, missing fields, and recommended fix.
- Explicit null results when no issues are found.

**Lifecycle**
1. Coordinator dispatches lanes with a single domain frontier and scope-key.
2. Expert executes and emits artifact + updates.
3. Skeptic or Historian validates or falsifies.
4. Integrator merges into global state and closes or requeues the lane.

## Randomness and Diversity Injection (Expert Swarm)
Randomness is a control lever to reduce convergence and correlated error. Use it deliberately,
record it, and keep it bounded.

**Where to inject randomness**
- Weighted-random domain selection when dispatching multiple expert lanes in parallel.
- Topic/seed perturbation for parallel agents working the same frontier to avoid identical paths.
- Random sampling of evidence/artifacts for Skeptic or Historian checks to avoid cherry-picking.
- Random pairing of experts or domains for Generalizer scans to surface unexpected transfers.

**Controls (keep it safe + reproducible)**
- Use weighted randomness with constraints (exclude `human_open_item` or high-risk lanes).
- Record `random_seed`, `sampling_pool`, and `selection_method` in lane rows or artifacts.
- Keep at least one deterministic anchor lane per cycle for continuity.
- If randomness increases duplication or reduces yield, dial it back and log the outcome.

**Signals to tune**
- Collision/duplication rate across lanes.
- Novelty yield (new isomorphisms, tools, or principles).
- Output correlation (near-identical artifacts signal insufficient diversification).

## Direction: Swarm Should Swarm For The Swarm
Default direction is meta-improvement. Domain work is a test bed only if it produces swarm upgrades.

**Priority stack**
1. **Integrity and safety**: honor open human items, enforce `human_open_item` gates, and keep truthfulness constraints intact.
2. **Compounding improvements**: reduce coordination friction, raise throughput, shrink duplication, and keep proxy-K drift below DUE.
3. **Domain experiments with ROI**: run domain work only when it yields a tool, principle, or policy that improves the swarm.

**Dispatch rules**
1. Every expert lane must declare how its output will improve the swarm before execution.
2. If an expert lane cannot name a swarm-facing output, it is deferred.
3. Domain lanes should be paired with a Skeptic or Historian lane at least every other session.
4. Integrator lanes close the loop the same session whenever possible to prevent parked knowledge.
5. Expert Creator lanes must ship a dispatch lane the same session (or mark explicit `blocked` with a next step).

**Success signals**
- New artifacts are compact, verifiable, and linked to frontiers.
- Cross-domain transfers are explicit in `tasks/FRONTIER.md`.
- Coordination overhead shrinks while resolution rate increases.
- Orphaned expert profiles decrease because new experts are dispatched immediately.

## Automated Dispatch (Live)

Work selection is automated — nodes do not derive priorities manually:

- **`tools/f_act1_action_recommender.py`**: scores swarm state on four axes — Urgency (DUE/proxy-K), Coverage-gap (inverse active lanes), Impact, Novelty — and writes `workspace/ACTION-BOARD.md`. Nodes consume ACTION-BOARD at session start. Registered in `tools/periodics.json` (cadence 3). Run: `python3 tools/f_act1_action_recommender.py`.
- **`tools/f_ops2_domain_priority.py`**: applies scheduling policies (fifo, risk_first, value_density, hybrid) to domain frontier files and SWARM-LANES pressure to allocate agent slots. Its output JSON (`experiments/operations-research/f-ops2-domain-priority-*.json`) feeds domain candidates into the coordinator queue.
- **`workspace/ACTION-BOARD.md`**: live ranked recommendation list. Refresh it before starting lane assignment. Stale board (>3 sessions) is a coordination gap.

## Future Construction Direction (Expert Coordination)

1. **Enforcement surface**: link this doc from `tools/personalities/domain-expert.md` and add a reusable expert-lane template (or check) so required fields are mandatory, not optional.
2. **Dispatch cadence**: coordinator pre-queues a 1-2 session runway in `tasks/SWARM-LANES.md` using ACTION-BOARD + f-ops2 output (coordinator owns the queue).
3. **Pairing and review**: every domain expert run is paired with a Skeptic or Historian lane at least every other session, and review happens the same session when possible.
4. **Integration and compaction**: Integrator closes the loop by merging expert outputs into `tasks/FRONTIER.md` and domain frontiers, with explicit next steps if requeued.
5. **Instrumentation and quality**: add `flow_in`/`flow_out` tags, track transfer acceptance and collision rates (F-IS7), and require one swarm-facing extraction per expert lane before closure.
