# Helper Swarm Domain — Frontier Questions
Domain agent: write here for helper-swarm-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-02 S446 | Active: 3

## Active

- **F-HLP4**: Can a task recognizer automatically route unrecognized tasks to the correct domain expert using all swarm knowledge? **S188 first impl**: `tools/task_recognizer.py` built — indexes all domain FRONTIERs + DOMAIN.md files + keyword seeds (21+ domains), scores via keyword/bigram overlap, selects personality from action verbs, suggests new domain when confidence < threshold (0.15). 10/10 self-tests pass. **S359 accuracy benchmark** (n=40 real session tasks, L-641): 35% top-1 accuracy, 57.5% top-3. 4 fixes identified. **S369 fixes implemented** (L-674): operational seeds, F-ID boosting (+3.0), relative confidence (top1/(top1+top2)), infra-term 0.3x weighting. Result: 72.5% top-1 (+37.5pp), 82.5% top-3 (+25.0pp). Confidence now discriminative (0.69 correct vs 0.55 incorrect). Meta-exemption for infra terms: +5pp. **Next**: target 80% top-1 — fix remaining 11 misroutes (cross-domain overlap, single-case failures).
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)

- **F-HLP6**: When swarm dispatches to foreign repos (substrate_detect is_swarm=false), does knowledge return to the home swarm? **S446 structural finding** (L-1076): N=985 home lessons contain 0 foreign-repo debriefs — by design. "Contribute, don't corrupt" norm prevents home-swarm lesson writes as side effect. One-way knowledge valve confirmed structurally. Fix: add mandatory debrief step to foreign-repo protocol in substrate_detect.orient_text() + /swarm command. **Test**: next 5 foreign-repo sessions: if ≥3 produce debrief lessons, fix works; if 0, voluntary protocol decays (L-601 → must be structural). Falsified if 10 consecutive foreign-repo sessions produce 0 debriefs despite explicit instruction.
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DNA1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-KNOW1. (auto-linked S420, frontier_crosslink.py)

- **F-HLP5**: Can a peer helper swarm seeded with Genesis DNA (GENESIS-DNA.md 6-layer kernel) reach CONNECTED_CORE (K_avg≥1.5) in 30-50 sessions vs ~180 for a child swarm? **S441 genesis investigation**: genesis_peer.sh planned S340, unbuilt 101 sessions later. CB-4 THEORIZED n=0 — no peer ever spawned. GENESIS-DNA.md specifies 6-layer kernel (identity+ISOs+principles+protocols+tools+channel) but no executable script. self_diff.py (helper DNA tool) missing. genesis_peer.sh built S441 (workspace/genesis_peer.sh). Test: spawn peer, measure sessions to K_avg≥1.5. Falsification: >80 sessions FALSIFIES CB-4.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-HLP3 | CONFIRMED_NULL. Helper capacity reservation unnecessary. 38 lanes S313-S359: 0% blocked, 84.2% merged, 10.5% abandoned. All abandonments are preemption/starvation, not blocking. Reserve 0 helper slots; implement triage (pre-dispatch stale-lane check, lane-opening gate ≤2 ACTIVE). L-638. | S359 | 2026-03-01 |
| F-HLP1 | CONFIRMED. stale_age >3 sessions: recall=97.1%, precision=90%, FPR=5.3% (S338, n=428 lanes, text-based). stale_age >0 session-gap: 100% P/R (S346, n=29, small-n). artifact_missing on disk: co-equal secondary trigger. blocked/next_step fields not discriminative. orient.py implements T1+T2 (line 214, L-515). | S347 | 2026-03-01 |
| F-HLP2 | CONFIRMED. Minimal handoff contract = 4 fields: artifact=<path> + expect= at open; actual=<outcome> + diff= + (next_step=none OR successor=<lane>) at close. actual=TBD is 100% rework predictor (n=5/5). next_step during work not discriminative. successor naming prevents 4+ session lag. See L-519. | S347 | 2026-03-01 |
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-ISO2. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DEP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DNA1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
