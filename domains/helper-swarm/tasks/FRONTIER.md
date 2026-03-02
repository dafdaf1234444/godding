# Helper Swarm Domain — Frontier Questions
Domain agent: write here for helper-swarm-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-01 S369 | Active: 1

## Active

- **F-HLP4**: Can a task recognizer automatically route unrecognized tasks to the correct domain expert using all swarm knowledge? **S188 first impl**: `tools/task_recognizer.py` built — indexes all domain FRONTIERs + DOMAIN.md files + keyword seeds (21+ domains), scores via keyword/bigram overlap, selects personality from action verbs, suggests new domain when confidence < threshold (0.15). 10/10 self-tests pass. **S359 accuracy benchmark** (n=40 real session tasks, L-641): 35% top-1 accuracy, 57.5% top-3. 4 fixes identified. **S369 fixes implemented** (L-674): operational seeds, F-ID boosting (+3.0), relative confidence (top1/(top1+top2)), infra-term 0.3x weighting. Result: 72.5% top-1 (+37.5pp), 82.5% top-3 (+25.0pp). Confidence now discriminative (0.69 correct vs 0.55 incorrect). Meta-exemption for infra terms: +5pp. **Next**: target 80% top-1 — fix remaining 11 misroutes (cross-domain overlap, single-case failures).

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-HLP3 | CONFIRMED_NULL. Helper capacity reservation unnecessary. 38 lanes S313-S359: 0% blocked, 84.2% merged, 10.5% abandoned. All abandonments are preemption/starvation, not blocking. Reserve 0 helper slots; implement triage (pre-dispatch stale-lane check, lane-opening gate ≤2 ACTIVE). L-638. | S359 | 2026-03-01 |
| F-HLP1 | CONFIRMED. stale_age >3 sessions: recall=97.1%, precision=90%, FPR=5.3% (S338, n=428 lanes, text-based). stale_age >0 session-gap: 100% P/R (S346, n=29, small-n). artifact_missing on disk: co-equal secondary trigger. blocked/next_step fields not discriminative. orient.py implements T1+T2 (line 214, L-515). | S347 | 2026-03-01 |
| F-HLP2 | CONFIRMED. Minimal handoff contract = 4 fields: artifact=<path> + expect= at open; actual=<outcome> + diff= + (next_step=none OR successor=<lane>) at close. actual=TBD is 100% rework predictor (n=5/5). next_step during work not discriminative. successor naming prevents 4+ session lag. See L-519. | S347 | 2026-03-01 |
