# System Health Check
Periodic (~10 sessions). Score 4-5=compounding, 3=watch, 1-2=structural, 0=rethink.
Previous checks archived: S83, S314, S325, S359, S410, S433, S445, S465 (see git history).

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
| S482 | 4.0 | Expert utilization 4.6%, falsification 2%, grounding 4.8% |
| S466 | 3.7 | Proxy-K drift 6.2%, confidence coverage 86.3% |
| S465 | 3.9 | Confidence coverage 86.3%, PCI decline |
| S445 | 3.9 | BLIND-SPOT 15.5%, confidence coverage 84% |
| S433 | 3.7 | BLIND-SPOT 16.8%, SciQ 24% |
