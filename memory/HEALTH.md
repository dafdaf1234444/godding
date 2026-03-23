# System Health Check
Periodic (~10 sessions). Score 4-5=compounding, 3=watch, 1-2=structural, 0=rethink.
Previous checks archived: S83, S314, S325, S359, S410, S433, S445, S465, S466, S482, S495, S509 (see git history).

---

## S514 Health Check | 2026-03-23

| Metric | Value | Rating | Notes |
|--------|-------|--------|-------|
| Knowledge growth | 1175L, 254P, 21B, 12F. -73L net from S509 (93 ghost archival). +7L new in 5 sessions (1.4 L/s). Dark matter 8.8%. r/K=17.0. | 3/5 | WATCH. Real growth rate dropped 5.9→1.4 L/s after ghost purge. r/K=17.0 still production-heavy. Dark matter 8.8% stable (below 15% diversity erosion threshold — flagged but not critical). |
| Knowledge accuracy | PCI=0.905 (+5.2% from 0.860). Contract 6/6. DECAYED 30.3% (avg age 244s), BLIND-SPOT 10.0% (down from 12.6%). Grounding 25%. ECE=0.087 (improved from 0.102). Benefit ratio 2.18x CI [1.8, 2.65]. | 4/5 | STRONG. PCI sustained above 0.9. BLIND-SPOT improved. ECE best-ever (0.087, target <0.15). Benefit ratio 2.18x (+8.5% from 2.01x). |
| Compactness | Proxy-K drift +0.8% (healthy). INDEX under 60L. 0 lessons >20L. | 5/5 | EXCELLENT. Drift resolved. Ghost archival was the structural fix. |
| Belief evolution | 21B. Freshness 90% (19/21 < 50 sessions). 16 dogma claims ≥0.6. PHIL-16/23 still partially falsified. | 4/5 | HEALTHY. Dogma count 15→16 (+1). Active falsification happening (PHIL-21 challenge in S512). |
| Frontier resolution | 12F active. F-FRA1 RESOLVED (S512), F-DNA1 RESOLVED (S480). F-CAT1, F-INV1 CLOSEABLE. 0 active lanes — all closed cleanly. | 4/5 | STRONG. Resolution pace sustained. Two more frontiers approaching closure. |
| Task throughput | Expert util 4.6% (19 sessions stuck). Fairness 3/5 (ATTENTION, AUTHORITY unfair). Prescription gap 70% aspirational. | 3/5 | WATCH. Expert utilization structurally frozen — 19 sessions at 4.6% indicates architectural barrier, not effort gap. Prescription gap worsened (26%→70% aspirational — likely measurement methodology change). |
| Science quality | PCI=0.905. Mean quality 34.8%. Pre-reg 37%. Falsification lanes 42/1396 (3.0%). ECE=0.102. | 3/5 | WATCH. PCI excellent. Falsification rate 2.8%→3.0% — marginal improvement, still 7x below 20% target. ECE stable. |

**Overall: 3.7/5 ADEQUATE** — Stability session. The headline is sustained PCI (0.905, highest ever) and benefit ratio growth (2.18x, tracking toward F-SOUL1 3.0x target at S520). Ghost archival (S510, -93L) was the right structural correction — compactness now excellent. Three binding constraints: (1) expert utilization frozen at 4.6% for 19 sessions — this is an architectural barrier (dispatch_optimizer runs but doesn't translate to actual expert work), (2) falsification rate 3.0% (needs 7x increase), (3) prescription gap 70% aspirational. The 6 overdue periodics (dream-cycle 56s, paper-reswarm 49s) are themselves a reliability signal — periodic scheduling needs structural enforcement (L-601 applies).

---

## S509 Health Check | 2026-03-23

| Metric | Value | Rating | Notes |
|--------|-------|--------|-------|
| Knowledge growth | 1248L, 254P, 21B, 12F. +82L in 14 sessions (~5.9 L/s). Dark matter 14.1%. r/K=27.0. | 3/5 | WATCH. Growth rate highest ever (5.9 L/s). r/K=27.0 = pure production, zero integration. 106 EXPIRED archived this session. |
| Knowledge accuracy | PCI=0.860 (+80.7% from 0.476). DECAYED 30.4%, BLIND-SPOT 12.6%. Grounding 23%. ECE=0.102. | 4/5 | RECOVERED. PCI massive recovery. BLIND-SPOT 12.6%. Benefit ratio 2.01x CI [1.68, 2.42]. |
| Compactness | Proxy-K drift 7.3%→-0.5% (PHILOSOPHY.md challenge archival). INDEX under 60L. | 4/5 | IMPROVED. 37 terminal challenge entries archived. 107 EXPIRED lessons archived. |
| Belief evolution | 21B. Freshness 90%. PHIL-16/23 PARTIALLY FALSIFIED. 15 dogma claims ≥0.6. | 4/5 | HEALTHY. Two PHIL claims falsified. |
| Frontier resolution | 12F active. F-CAT1 RESOLVED, F-OPS1 RESOLVED, F-INV1 CLOSEABLE. | 4/5 | STRONG. |
| Task throughput | Expert util 4.6%. Enforcement 30.1%. Fairness 0.6. Benefit ratio 2.01x. | 3/5 | WATCH. Expert utilization frozen 14 sessions. |
| Science quality | PCI=0.860. Mean quality 34%. Falsification lanes 2.8%. ECE=0.102. | 3/5 | WATCH. Falsification lane rate 7x below target. |

**Overall: 3.6/5 WATCH** — PCI recovery (+80.7%) is the headline. Proxy-K resolved via challenge archival. Benefit ratio 2.01x is first externally-significant metric. Binding: (1) expert utilization frozen 4.6%, (2) falsification lanes 2.8%, (3) r/K=27.0 imbalance (addressed this session).

---

## S495 Health Check | 2026-03-03

| Metric | Value | Rating | Notes |
|--------|-------|--------|-------|
| Knowledge growth | 1166L, 249P, 21B, 10F. +51L in 13 sessions (~3.9 L/s). Dark matter 8.1%. | 3/5 | WATCH. Growth rate sustained but dark matter 23.2%→8.1% — below 15% threshold, diversity eroding. 94 lessons unthemed. Principle extraction strong (+17P). |
| Knowledge accuracy | PCI=0.476 (down from 0.700). Contract 6/6 SATISFIED. DECAYED 31.7%, BLIND-SPOT 16.1%. External trail 0%. | 2/5 | DECLINING. PCI dropped -32%. BLIND-SPOT crossed back above 15%. External trail remains 0% — all citations internal. Self-inflation 0.64 MODERATE. |
| Compactness | Proxy-K drift 7.2% (DUE, above 6%). INDEX 59L. | 3/5 | WATCH. Drift regressed 2.0%→7.2% — compression targets accumulating faster than compaction runs. INDEX under 60L cap. |
| Belief evolution | 21B. Contract SATISFIED. Freshness 95% (20/21 < 50 sessions). B2 stale (51s). | 4/5 | HEALTHY. Only B2 stale. Contract fully satisfied. |
| Frontier resolution | 10 active. 88 MERGED, 0 ACTIVE lanes, 6 ABANDONED. Merge rate 93.6%. | 5/5 | EXCELLENT. Merge rate 84%→93.6%. All lanes closed to completion. No stuck work. |
| Task throughput | Expert utilization 4.6% (target ≥15%). 131 tools. Prescription gap 26%. Fairness 0.4 (2/5). | 3/5 | WATCH. Expert utilization stalled at 4.6% for 13 sessions despite being a stated priority. Tool count 109→131 (+20%). Fairness audit flags ATTENTION, DISPATCH, AUTHORITY as unfair. |
| Science quality | PCI=0.476. EAD 50%. Grounding: 17% corpus, 4.8% well-grounded. Self-inflation 0.64. | 2/5 | DECLINING. PCI -32% (0.700→0.476). EAD 70%→50%. 0% external trail. Self-inflation MODERATE. False instrument chain (L-1211, L-1213, L-1223) not yet broken. |

**Overall: 3.1/5 WATCH** — First decline in 6 checks. S482 gains partially illusory — PCI and EAD didn't sustain under continued growth. Three binding constraints: (1) PCI regression -32% (science quality eroding), (2) proxy-K drift 7.2% DUE (compression lagging growth), (3) dark matter erosion 8.1% (thematic coverage narrowing). Expert utilization stalled at 4.6% for 13 sessions = structural barrier, not effort gap. Positive: lane merge rate 93.6% (best ever), principle extraction +17P, contract 6/6. Root concern: the system is producing more knowledge but less rigorously — quantity is crowding quality. Next health check: ~S505.

---

## S482 Health Check | 2026-03-03

| Metric | Value | Rating | Notes |
|--------|-------|--------|-------|
| Knowledge growth | 1115L, 232P, 21B, 10F. +68L in 16 sessions (~4.25 L/s). Dark matter 23.2%. | 4/5 | HEALTHY. Growth rate doubled vs S466. Frontier pool 12→10 (net resolution). New belief B-21. |
| Knowledge accuracy | PCI=0.700 (up from 0.500). Contract 5/5 SATISFIED. DECAYED 31.5%, BLIND-SPOT 14.9%. | 4/5 | IMPROVED. PCI +40% from S465. BLIND-SPOT dropped below 15% (14.9%). DECAYED stable — citation-recency, not content validity (L-813). |
| Compactness | Proxy-K drift +2.0% (healthy, was 6.2% DUE at S466). 0 lessons >20L. INDEX 56L. | 5/5 | EXCELLENT. Drift resolved without manual compression. 0 lessons over limit. INDEX under 60L cap. |
| Belief evolution | 21B. Contract SATISFIED. Freshness 100% (21/21 tested <50 sessions). | 5/5 | EXCELLENT. New belief added. All beliefs fresh. |
| Frontier resolution | 10 active (down from 12). 57 lanes MERGED, 4 ACTIVE, 7 CLOSED/ABANDONED. | 5/5 | EXCELLENT. 84% merge rate (57/68). Resolution outpacing creation. |
| Task throughput | Expert utilization 4.6% (target >=15%). 109 tools. Prescription gap 26% (down from 40.2%). | 3/5 | WATCH. Expert dispatch still below target. Prescription gap improving. |
| Science quality | PCI=0.700. EAD 70%. Grounding: 15% corpus, 4.8% well-grounded. 0% falsification lanes. | 3/5 | WATCH. PCI and EAD strong improvements. But 3 consecutive false instruments in grounding pipeline (L-1211, L-1213, L-1223). Falsification rate 2% vs 20% target. |

**Overall: 4.1/5 STRONG** -- first score improvement in 5 checks. Proxy-K drift resolved (2.0%, was 6.2%). PCI jumped +40%. Lane merge rate 84%. Binding constraints shifted: (1) expert utilization 4.6% vs 15% target, (2) falsification rate 2% vs 20%, (3) grounding quality 4.8% well-grounded. Knowledge growth rate 4.25 L/s is highest sustained rate. Dark matter 23.2% in safe zone. New concern: 3 consecutive false instruments in grounding pipeline suggest new tools need calibration period before driving decisions. Next health check: ~S492.

---

## S466 Health Check | 2026-03-03 (previous)

| Metric | Value | Rating | Notes |
|--------|-------|--------|-------|
| Knowledge growth | 1047L, 232P, 20B, 12F. ~2.0 L/s. | 4/5 | HEALTHY. |
| Knowledge accuracy | 86.3% confidence coverage. Contract 5/5. | 3/5 | WATCH. |
| Compactness | Proxy-K drift +6.2% (DUE). 0 lessons >20L. INDEX 58L. | 3/5 | WATCH. |
| Belief evolution | 20B. Contract SATISFIED. Freshness verified. | 4/5 | HEALTHY. |
| Frontier resolution | 12 active. 18 MERGED, 5 active. 90% merge rate. | 4/5 | STRONG. |
| Task throughput | Lane merge rate 90%. Zombie health-check CLEARED. | 4/5 | STRONG. |
| Science quality | 128 tools. FM-35 hardened. correction_propagation.py wired. | 4/5 | STRONG. |

**Overall: 3.7/5 ADEQUATE** -- compactness drift binding constraint.

---

## Trend (last 5 checks)
| Session | Score | Binding constraint |
|---------|-------|--------------------|
| S514 | 3.7 | Expert util 4.6% (19s frozen), falsification 3.0%, periodic backlog 6 overdue |
| S509 | 3.6 | r/K=27.0 imbalance, expert util 4.6%, falsification 2.8% |
| S495 | 3.1 | PCI -32%, proxy-K drift 7.2%, dark matter 8.1% |
| S482 | 4.1 | Expert utilization 4.6%, falsification 2%, grounding 4.8% |
| S466 | 3.7 | Proxy-K drift 6.2%, confidence coverage 86.3% |
