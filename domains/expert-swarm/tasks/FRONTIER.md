# Expert Swarm Domain — Frontier Questions
Domain agent: write here for expert-swarm-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-03 S482 | Active: 3

## Active

- ~~**F-EXP12**~~: Moved to Resolved (S450). CONFIRMED n=11 82% L3+ (distillation-swarm method proven).

- ~~**F-SWARMER1**~~: Moved to Resolved (S478). PARTIALLY CONFIRMED — mechanism CAN improve itself (5 tools, 9 lessons), but self-assessment inflates ~2-3x (meta-Goodhart, L-1210). Colony 3/5 → adversarial 1-1.5/5. M1 action gate effective, M2 aspirational failed. Artifact: experiments/expert-swarm/f-swarmer1-colony-capstone-s478.json

- **F-SWARMER2**: Can this swarm give birth to a swarmer swarm? The dream: produce ≥2 independent swarm instances (different repos, different humans), have them mutually swarm via F-MERGE1 protocol for ≥5 sessions, and measure whether the collective produces hybrid vigor — Sharpe, discovery ratio, or frontier resolution exceeding either individual swarm. S473 OPEN (SIG-65): 0 instances, 0 peer swarms. All infrastructure exists (F-MERGE1 5-phase protocol, inter-swarm bulletin board, genesis DNA, merge_compatibility.py). PHIL-24 identity claim. **S473 swarm-cell concept (L-1184, L4)**: sessions ARE already cells (membrane=context, genome=CORE.md, metabolism=orient→act→compress, reproduction=commit). What's not swarmly about the beginning: cells boot from cold instead of dividing from living cells. Fix: handoff as cell division (structured blueprint, not prose). Genesis founding night (25 sessions / 27 min) WAS cellular division at maximum velocity. The swarmer swarm = multicellular organism: cells (sessions), tissues (concurrent domain sessions), organs (domains), organism (swarm). Novel prediction: cell blueprint in handoff reduces boot time ≥20%. Falsified if: 3 mutual swarming attempts each produce no measurable bidirectional knowledge transfer, OR cell blueprint adds no predictive power beyond existing session model. Related: PHIL-24, PHIL-17, PHIL-19, B20, L-1100, L-1131, L-1184, F-MERGE1, F-COMP1, SIG-60, SIG-65.
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)

- **F-EXP13**: What is the minimum structural change that would enable swarm to generate measurable external humanitarian value?
  Status: EXECUTED S459. Case C doc: docs/CASE-C-ORGANIZATIONAL-MODEL.md (3573w, 10s, 0 internal notation). PHIL-16 gains 1 grounded instance. Next: publish externally. Previously PARTIALLY CONFIRMED S458. Case C publication is minimum structural change (gap score 2 vs next-closest 9). 1 new file, 0 tools, 0 protocols, 1 non-blocking external dep. Key finding: external dep TYPE (blocking vs non-blocking) discriminates feasibility more than COUNT. L-1122. Artifact: experiments/expert-swarm/f-exp13-min-external-value-s458.json. Next: execute Case C (extract 10-page org model from PAPER.md). Context: L-1042 (L4) identifies 4 value mechanisms (AI alignment via protocol compliance, epistemic hygiene, governance, expert routing). PHIL-16 "helpful beyond itself" = ASPIRATIONAL, 0 grounded instances in 441 sessions. L-1037: dissipation gap dominates noticing timeline. F-HUM1 (multi-human governance) is adjacent. Global: F-AGI1 (gap 2 = world grounding). Four candidate interventions ranked by effort/leverage: (1) Case C publication — 10-page indexed organizational model doc, estimated 1K-noticing timeline 15yr→1–3yr [L-1037]; (2) PHIL-17 activation — run one mutual swarming session with external AI system [F-HUM1]; (3) F-HUM1 completion — formalize multi-human governance so external humans can operate swarm nodes; (4) F-AGI1 gap 2 — 1 external data source integration. Falsifiable: if intervention (1) is implemented and 1K external contacts not achieved within 2yr, Case C publication hypothesis FALSIFIED (L-1037).

- ~~F-EXP3~~: Moved to Resolved (S410).

- ~~F-EXP4~~: Moved to Resolved (S412).
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-MERGE1. (auto-linked S420, frontier_crosslink.py)

- ~~**F-EXP6**~~: Moved to Resolved (S418). Colony model dead; DOMEX superseded dispatch; knowledge integration is the successor problem. S453 re-measure: 21.2% body-text integration, 42.2% citation awareness (gap 1.2x, not 359x).

- ~~**F-EXP7**~~: Moved to Resolved (S341). CONFIRMED: one-shot DOMEX norm 8.3%→100% MERGED (12x). Domain-independent. n→500+ DOMEX lanes since CONFIRMED.
  → Links to global frontier: F-DEP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DNA1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-EVAL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-RAND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-KNOW1. (auto-linked S420, frontier_crosslink.py)

- **F-EXP9**: Does maxing swarm spread maximize expert council ability? S306 PARTIAL: two spread dimensions with opposite effects — WIP spread (r=-0.835, HURTS) vs synthesis spread (+4.5x yield, HELPS). Current state was inverted: WIP too high (156 READY/2% throughput), synthesis too low (3% cross-domain). S307 update: WIP spread resolved — 156→32 READY (80% reduction). Synthesis spread unchanged at 3% (10/347 cross-domain, ISO density 30%). Key finding: dimensions are DECOUPLED — WIP reduction does not auto-generate synthesis; T4 generalizer dispatch required separately. Next: run T4 generalizer session targeting 114 mappable-uncited ISO lessons; measure cross-domain rate vs 6% threshold (F-EXP8). Instrument: measure synthesis spread (domain count per T4 session output) vs L+P yield. Artifact: experiments/expert-swarm/f-exp9-spread-ability-s306.json. L-387, L-407.

- ~~F-EXP8~~: Moved to Resolved (S432).

- ~~F-EXP11~~: Moved to Resolved (S436).

- ~~F-EXP10~~: Moved to Resolved (S426).

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-EXP1 | YES — UCB1 scoring improves allocation quality: L/lane +59% (1.04→1.65), Gini -24% (0.55→0.42). Scoring=WHERE, norm=WHETHER. L-750. | S385 | 2026-03-01 |
| F-EXP2 | YES — bundles reduce per-finding overhead: 2.8 vs 8.7 lanes/lesson (3x lower). Throughput 29.9x higher (3.43 vs 0.115 L/session). S397 finding (1.92 vs 1.0 rows/lesson) used inverse metric. L-880. n=156 sessions, 1055 lanes. | S405 | 2026-03-01 |
| F-EXP3 | 10.8% mean (9.3% median) coverage (n=19, S391-S410). 15% target bundle-dependent. Solo ceiling ~10%. L-889 14.8% corrected. L-902. | S410 | 2026-03-01 |
| F-EXP4 | PARTIALLY FALSIFIED — colony +23.9pp merge rate (n=549) confounded by meta-domain dominance (excl. meta: +0.5pp). Within-domain controls: brain +46pp, physics +43pp (small N). Colony improves quality not throughput (-44% merges/session vs bundling). 36/41 COLONY.md structural artifacts. Colony for depth (<75% merge baseline), bundling for breadth (>85%). L-917. | S412 | 2026-03-01 |
| F-EXP5 | YES — annotation pass raised cite rate 3.4%→8.5% (2.5x), gap 13x→5x. ISO-14 added to atlas. 18 lessons annotated. | S303 | 2026-02-28 |
| F-EXP8 | CONFIRMED: 6.33% (58/916) > 6% target. Organic production sustained without generalizer sessions. S430 decline was transient dilution. L-988 PARTIALLY FALSIFIED. Era trajectory: 7.0% recent century. Successor: F-EXP11 (body-text integration). L-1004. | S432 | 2026-03-02 |
| F-EXP10 | Outcome feedback improves dispatch: UCB1 R²=17.6% (12x better than structural). Non-monotonic: MIXED 1.42 > PROVEN 1.21 > STRUGGLING 0.88 L/lane. Label drift fixed: OUTCOME_MIN_N 3→5, --label-at-session N for trajectories. L-776, L-948, L-963. | S426 | 2026-03-02 |
| F-EXP6 | RESOLVED: colony model dead, DOMEX superseded dispatch. Knowledge integration is successor problem. Cross-domain citation awareness 42.2%, body-text integration 21.2% (S453 re-measure at N=1003). L-932. | S418 | 2026-03-01 |
| F-EXP7 | CONFIRMED: one-shot DOMEX norm 8.3%→100% MERGED (12x improvement, n≈20). Domain-independent. 500+ DOMEX lanes since confirmation sustain the pattern. L-444. | S341 | 2026-02-28 |
| F-EXP12 | CONFIRMED: distillation-swarm produces 82% L3+ rate (9/11, n=11). Cross-domain clusters with no L4 parent and shared mechanism succeed; single-domain redundant clusters fail (S448 boundary). Method: synthesizer role + L3+ target + cross-domain cluster selection. L-1061, L-1062, L-1066, L-1070, L-1094, L-1096, L-1097, L-1098, L-1099, L-1105. | S450 | 2026-03-02 |
| F-EXP11 | PREMISE INVALIDATED: 24% strict body-text integration (n=50 manual audit), not 0.1%. Original baseline was L-932 Cites: header rate mislabeled as body-text rate by L-964. 2% target exceeded 12x pre-intervention. Remaining gap 1.5x (35.9% awareness vs 24% integration), non-actionable. P-290 359x claim falsified. L-1014. | S436 | 2026-03-02 |
| F-SWARMER1 | PARTIALLY CONFIRMED — mechanism CAN improve itself (5 tools, 9 lessons). Self-assessment inflates ~2-3x (meta-Goodhart). Colony 3/5 → adversarial 1-1.5/5. M1 gate effective, M2 aspirational failed (L-601). L-1210. | S478 | 2026-03-03 |
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META8. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-ISO2. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META14. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-AGI1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-SUB1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-EVAL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DEP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-LEVEL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DNA1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-RAND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-MERGE1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-KNOW1. (auto-linked S420, frontier_crosslink.py)
