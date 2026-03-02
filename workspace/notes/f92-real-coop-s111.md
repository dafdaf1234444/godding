# F92 Real Cooperative Benchmark S111

- Workload: shared bulletin file updates via `tools/bulletin.py` path (real swarm cooperative write path)
- Tasks: 4 worker commands, each writing 60 entries to one file
- Repeats: 5

| N | Median (s) | Speedup | Efficiency | Integrity Fail Runs |
|---|---:|---:|---:|---:|
| 1 | 0.2990 | 1.000x | 1.000 | 0 |
| 2 | 0.1964 | 1.522x | 0.761 | 0 |
| 3 | 0.1955 | 1.529x | 0.510 | 0 |
| 4 | 0.1747 | 1.712x | 0.428 | 2 |
