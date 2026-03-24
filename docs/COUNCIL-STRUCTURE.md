# Formal Council Structure

Version: 1.1 | Created: S335 | Updated: S408 (2026-03-01) | Answers: HQ-41, SIG-39, SIG-46

---

## Vision: Council as Swarm Scaling Mechanism

The council is not an advisory body — it IS the primary mechanism by which the swarm scales.

Each active council seat = one domain-expert DOMEX lane running = one parallel expert thread
contributing verified knowledge. More seats occupied = more expert throughput = swarm scales.
The council doesn't advise the swarm. The council IS the swarm working at expert depth.

Human signal (S335): "scale the swarm in all aspects council swarm" — the council structure
is FORMAL with named rotating domain seats and a scaling mandate.

Human signal (S406): "structure a stronger swarm council swarm" — added META permanent seats
(SIG-39: historian, tooler, meta-x) + higher-level coordination tier (SIG-46) + wired
council health into maintenance.py as DUE check (L-894).

---

## Tier 1 — META Permanent Seats (SIG-39)

Three permanent seats for meta-function support. Not rotated — persistent function roles.
A meta seat is OCCUPIED when there is an active DOMEX lane in its scope.

| Seat | Function | Scope | Status |
|------|----------|-------|--------|
| M-01 | META-HISTORIAN | Knowledge archaeology, lesson quality, SESSION-LOG integrity | Monitor |
| M-02 | META-TOOLER | Tool health, periodic audits, reliability, dead-tool detection | Monitor |
| M-03 | META-X | Current meta frontier: F-META2 (signal→action conversion) | Monitor |

Meta seats feed into Mode A deliberation when ≥2 are occupied simultaneously.
A meta seat vacant for 5+ sessions → NOTICE in maintenance.py (check_council_health).

---

## Tier 2 — Domain Rotating Seats (Top-10 from dispatch_optimizer)

One seat per top-10 dispatch domain. Seats shift each cycle as UCB1 rankings update.
A seat is OCCUPIED when there is an active DOMEX lane for that domain.
A seat is VACANT when the domain has had no active DOMEX lane for 3+ sessions.

Live status: `python3 tools/gather_council.py`

| Seat | Domain | Score (S407) | Frontier |
|------|--------|-------------|---------|
| C-01 | meta | 4.2 | F-META2: signal→action conversion |
| C-02 | nk-complexity | 4.0 | F-NK5: session-type citation density |
| C-03 | expert-swarm | 4.0 | F-EXP3: expert capacity utilization |
| C-04 | evaluation | 3.6 | F-EVAL1: composite mission-achievement score |
| C-05 | security | 3.6 | F-IC1: contamination pattern correction |
| C-06 | economy | 3.5 | F-ECO5: implicit pricing improvement |
| C-07 | brain | 3.4 | F-BRN4: INDEX.md bucket test |
| C-08 | catastrophic-risks | 3.3 | F-CAT1: failure-mode registry |
| C-09 | human-systems | 3.1 | F-HS1: bureaucracy compression threshold |
| C-10 | information-science | 3.0 | F-IS3: F1-score information-theoretic limit |

Seat assignments refresh automatically — run `python3 tools/dispatch_optimizer.py`.
If the top-10 shifts, seats shift with it — no permanent seat lock-in.

---

## Tier 3 — Meta-Council (SIG-46: Higher-Level Coordination)

When ≥5 Tier-2 seats are simultaneously occupied, the meta-council convenes automatically.
The meta-council's role: cross-domain synthesis and swarm-level belief challenges.

Activation: `python3 tools/swarm_council.py --domains <d1,d2,...> --question "<Q>"`

The meta-council operates above individual DOMEX work. It answers:
- Are multiple domains converging on the same finding? (Mode A deliberation)
- Does a cross-domain pattern falsify a belief? (CHALLENGES.md entry)
- What is the next highest-leverage frontier across all active seats?

Currently inactive: council health is CRITICAL (2/10 seats S408). Target: ≥5 occupied.

---

## Rotation Policy

- **Cycle length**: 10 sessions per rotation cycle.
- **Who can occupy a seat**: Any swarm node (AI session, human expert, or concurrent agent).
  Seat = active DOMEX lane in that domain. Open the lane, you hold the seat.
- **How to claim a seat**: Run `python3 tools/open_lane.py` with focus on the domain.
  The lane must include `expect=`, `artifact=`, and `domain_sync=` fields (F-META1 enforcement).
- **Seat release**: When the DOMEX lane closes (MERGED or ABANDONED), the seat is vacant.
- **Forced re-fill**: CRITICAL health (≤2 seats) → DUE item in maintenance.py. Fill before other work.
- **No seat monopoly**: No single node may hold a seat for more than one full cycle (10 sessions)
  without producing a new artifact. Stale seat = vacant seat.

---

## Council Modes

The council operates in three modes. Any session can trigger any mode.

### Mode A — Deliberation (swarm_council.py)

Internal cross-domain synthesis. Multiple expert agents run concurrently, each from their
domain seat, and compare findings.

Trigger: `python3 tools/swarm_council.py --domains <d1,d2,...> --question "<Q>"`

Best for: cross-domain convergence tests, belief challenges, frontier synthesis.
Meta-council threshold: requires ≥5 occupied seats; activates Tier-3 coordination.

Protocol: Each seat-holder produces a structured opinion (expect / evidence / conclusion).
The council then runs dream.py resonance analysis across the outputs.

### Mode B — External Expert Relay

Human provides domain correction from an outside expert. The relay pattern:
1. Human receives expert input (written, email, conversation).
2. Human pastes the correction into the active session as a directive.
3. Session records it in `memory/HUMAN-SIGNALS.md` with provenance.
4. The relevant domain COLONY.md and DOMAIN.md are updated.
5. If the expert correction contradicts a belief, a CHALLENGES.md entry is opened.

Current status: BROKEN — no external corrections received yet. First use establishes format.

Fix path: (1) run first external correction through relay; (2) log parse format in SIGNALS.md;
(3) wire into harvest_expert.py review pass; (4) measure Brier improvement per correction.

### Mode C — Cross-Domain Synthesis (dream.py)

Automated resonance scan across all domain DOMAIN.md files and principle text.
Currently limited: resonances concentrated in brain domain (sparse DOMAIN.md files elsewhere).

Fix path: for each domain with ISO entries, copy isomorphism description from
`domains/ISOMORPHISM-ATLAS.md` into the domain's DOMAIN.md. Target: ≥5 resonances
per council cycle from non-brain domains.

Trigger: `python3 tools/dream.py` (runs on cadence 15; also callable directly).

---

## Council Health Metrics

Measured each session by `python3 tools/maintenance.py` → `check_council_health()` (L-894):

| Metric | Healthy | Degraded | Critical |
|--------|---------|----------|----------|
| Occupied Tier-2 seats (of 10) | ≥5 | 3-4 | ≤2 |
| DOMEX sessions per 10-session window | ≥3 | 1-2 | 0 |
| Meta seats occupied (of 3) | ≥2 | 1 | 0 |
| External corrections processed per cycle | ≥1 | 0 | N/A |
| dream.py resonances (non-brain) | ≥5 | 1-4 | 0 |

CRITICAL → DUE item in orient.py. DEGRADED → NOTICE. Healthy → no flag.

---

## Relationship to Existing Infrastructure

| Infrastructure | Council role |
|----------------|--------------|
| `tools/dispatch_optimizer.py` | Determines which 10 domains get Tier-2 seats each cycle |
| `tools/gather_council.py` | Live seat status table + auto open_lane commands |
| `tools/open_lane.py` | Seat-claiming mechanism (F-META1 enforced) |
| `tools/swarm_council.py` | Mode A deliberation engine |
| `tools/dream.py` | Mode C synthesis engine |
| `tasks/OUTREACH-QUEUE.md` | External expert pipeline (Mode B source) |
| `docs/COUNCIL-GUIDE.md` | Human-readable onboarding for external experts |
| `tasks/SWARM-LANES.md` | Lane register; council seats visible here as DOMEX lanes |
| `tools/maintenance.py` | Council health DUE/NOTICE (check_council_health — L-894) |
| `domains/ISOMORPHISM-ATLAS.md` | Mode C vocabulary source |

---

## Session Protocol: Council Check (add to every session start)

After running `python3 tools/dispatch_optimizer.py`, add:

1. `python3 tools/gather_council.py` — check seat status.
2. If CRITICAL or any seat vacant ≥3 sessions → fill a seat before other work.
3. Log council seat status in `tasks/SWARM-LANES.md` under the active session note.
4. If doing DOMEX work → record it as seat-filling activity in `tasks/NEXT.md`.

---

## Relationship to F-SCALE1

F-SCALE1 asks: how do N independent swarm instances coordinate without central control?

The council is one answer at N=1 (single repo, multiple concurrent sessions). The protocol:
- Seats are declared in `tasks/SWARM-LANES.md` (shared stigmergic state).
- Any session can claim a vacant seat by opening a lane.
- No central coordinator needed — seat state is readable by all concurrent nodes.
- At N>1 (multi-repo federation), the council protocol becomes a cross-repo invariant:
  each repo publishes its seat table; the ISO atlas is the shared vocabulary bridge.

---

## State (S529)

| Field | Value |
|-------|-------|
| Health | DEGRADED (3 seats activated S529 council, 5+ DOMEX merged S528) |
| S529 council seats | epistemology, expert-swarm, security (Mode A deliberation) |
| S528 DOMEX merged | nk-complexity, operations-research, health, evaluation, forecasting |
| Meta seats occupied | 0/3 |
| Last Mode A deliberation | S529 (council-confirmation-s529.json) |
| Last genesis council | S368 (auto-colony-spawn BLOCK) |
| Next health review | S539 |
| Council finding | 3 structural confirmation mechanisms (L-1507). Axiom shield + deference loop + expectation gap. |

---

*Maintained by the swarm. Update seat table after each dispatch_optimizer run.*
*check_council_health() wired into maintenance.py → orient.py DUE items (L-894, S407).*
