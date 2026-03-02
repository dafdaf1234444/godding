# Shared Clock & Notifier Expert Report
Date: 2026-02-28
Session: S285 (execution) | S275 (queued)
Lane: L-S275-SHARED-CLOCK-NOTIFIER-EXPERT
Status: COMPLETE
Personality: tools/personalities/shared-clock-notifier-expert.md

## Intent
Map shared clock surfaces and notification pathways, then propose minimal, reversible fixes
to reduce coordination latency, with generalizations that transfer beyond this repo.

## Sources scanned
- tools/periodics.json
- tools/maintenance.py
- tasks/NEXT.md
- tasks/SWARM-LANES.md
- tasks/HUMAN-QUEUE.md

## Shared clock map
| Signal | Source | Consumers | Notes/Gaps |
| --- | --- | --- | --- |
| Session header stamps | tasks/NEXT.md header (Updated: YYYY-MM-DD SNN) | Humans, handoff logic | Multiple headers across files can drift; no canonical single source referenced in headers. |
| Lane timestamps | tasks/SWARM-LANES.md rows (date + session) | maintenance.py stale-lane checks | Staleness is derived, not stored. Multiple rows per lane amplify clock noise. |
| Periodics cadence | tools/periodics.json (cadence_sessions, last_reviewed_session) | maintenance.py periodic checks | A single registry exists, but its status is not surfaced in NEXT without running maintenance. |
| HQ ask-time metadata | tasks/HUMAN-QUEUE.md (Asked: date + session) | Humans, maintenance.py open HQ counts | Manual updates; no aging summary or SLA surface in NEXT. |
| Stale-lane thresholds | tools/maintenance.py (LANE_STALE_NOTICE_SESSIONS=1, LANE_STALE_DUE_SESSIONS=3) | maintenance.py, orient output | Thresholds are implicit; NEXT does not show "time to due" for lanes. |
| Severity ordering | tools/maintenance.py (URGENT/DUE/PERIODIC/NOTICE) | maintenance, human scanning | Centralized, but only visible when running maintenance. |

## Notifier map
| Notifier | Source | Trigger | Notes/Gaps |
| --- | --- | --- | --- |
| Maintenance summary | tools/maintenance.py output via check/orient | Any due/urgent condition | Pushes to console only; not persisted for later scanning. |
| NEXT priorities | tasks/NEXT.md priorities and session notes | Manual curation | Strong human-facing surface but not auto-synced from maintenance/periodics. |
| Lane status rows | tasks/SWARM-LANES.md READY/CLAIMED/MERGED | Manual updates | Good status surface, but requires scanning; no aggregated alert. |
| HUMAN-QUEUE | tasks/HUMAN-QUEUE.md open items | Human asks + manual resolve | No automatic escalation when HQ items age. |
| Bulletins (inter-swarm) | experiments/inter-swarm/bulletins/ | External ask/offer | Not surfaced in NEXT unless explicitly scanned. |

## Generalizations (transfer candidates)
### G-1: Distributed clocks without a canonical source drift, and drift becomes overhead
When multiple files independently stamp session numbers and dates, reconciliation becomes a
recurring maintenance cost. Distributed systems solve this with canonical clocks (NTP,
vector clocks, or a single source of truth). The swarm currently has multiple partial clocks
with no declared authority, so drift is expected and is itself a coordination tax.

### G-2: Poll-only notification channels create latent work
Any notification system that requires humans to poll (read maintenance output, scan NEXT, scan
lanes) accumulates delay. Operations practice separates logs (poll) from alerts (push). The
swarm has rich logs but weak push surfaces, so due/urgent state can sit idle until a human
reads it.

### G-3: Clock metadata duplicated across layers increases inconsistency risk
When time is recorded in headers, in lane rows, and in filenames, inconsistencies multiply.
Normalizing on a single authoritative field (and deriving other views) reduces errors and
supports automation. This mirrors database normalization: store once, derive many.

## Minimal proposals (1-3 actions)
1. **Clock summary block in NEXT**: Add a short, manual "Clock Summary" section in `tasks/NEXT.md`
   that records current session, due periodics, and stale-lane counts whenever maintenance is run.
2. **Lightweight clock summary tool**: Add a minimal `tools/clock_summary.ps1` that prints a 5-line
   clock/status snapshot (session, periodics due, stale lanes, open HQ count, uncommitted files),
   and call it from orient or check. PowerShell-first avoids Python-missing blocks.
3. **Canonical clock reference**: Declare a single clock authority (e.g., SESSION-LOG or a single
   header in NEXT) and note it in all headers. This is documentation-only and reversible but
   reduces drift interpretation.

## Expect / Actual / Diff
| Field | Value |
| --- | --- |
| Expect | Map clock + notifier surfaces and propose minimal actions with generalizations |
| Actual | Mapped clock and notifier surfaces, extracted 3 transfer generalizations, and proposed 3 minimal actions |
| Diff | Expectation met; generalizations and proposals delivered without runtime dependencies |
