# F92 Benchmark S109

- Generated: 2026-02-27 16:02 UTC
- Method: fixed workload, N=1/2/3/4 workers, 3 repeats, median wall time.

## Workload A: wiki_swarm (3 independent topics)
Commands: `tools/wiki_swarm.py` for `Distributed systems`, `Stigmergy`, `Error handling` (depth=1, fanout=5).

| N | Samples (s) | Median (s) | Speedup | Efficiency |
|---|---|---:|---:|---:|
| 1 | 3.270, 3.457, 3.398 | 3.398 | 1.000x | 1.000 |
| 2 | 2.167, 2.097, 2.174 | 2.167 | 1.568x | 0.784 |
| 3 | 1.218, 1.239, 1.616 | 1.239 | 2.742x | 0.914 |
| 4 | 1.294, 1.133, 1.295 | 1.294 | 2.625x | 0.656 |

## Workload B: nk_analyze batch (4 independent local analysis jobs)
Commands: 4 `tools/nk_analyze.py batch` variants (including `--api-shape`).

| N | Samples (s) | Median (s) | Speedup | Efficiency |
|---|---|---:|---:|---:|
| 1 | 1.518, 1.583, 1.651 | 1.583 | 1.000x | 1.000 |
| 2 | 0.799, 0.844, 0.855 | 0.844 | 1.875x | 0.938 |
| 3 | 0.629, 0.634, 0.786 | 0.634 | 2.498x | 0.833 |
| 4 | 0.684, 0.586, 0.594 | 0.594 | 2.666x | 0.666 |

## Quick read
- Wiki workload knee at N=3: N=3 median 1.239s vs N=4 1.294s.
- Compute workload still improves at N=4: N=3 median 0.634s vs N=4 0.594s.
- Interpretation: optimal N is workload-shaped (fanout, task weight, contention), not globally fixed.
