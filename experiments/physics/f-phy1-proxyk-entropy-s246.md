# F-PHY1 Baseline - Proxy-K Entropy / Phase Transition Scan (S246)
Date: 2026-02-28
Domain: physics/thermodynamics
Check mode: verification
Data: `experiments/proxy-k-log.json` (per-session max totals)

## Expect
Proxy-K totals should show punctuated jumps/drops (phase-transition-like) rather than smooth drift. Median |delta| should be much smaller than max |delta|, with occasional large drops (compaction-like).

## Method
1. Load proxy-k log JSON.
2. Group by session, take max total per session.
3. Compute deltas between consecutive sessions.
4. Summarize median/p90 of |delta| and top 5 increases/drops.

Commands (PowerShell):
```powershell
# stats
$data = Get-Content experiments/proxy-k-log.json | ConvertFrom-Json
$bySession = $data | Group-Object session | ForEach-Object {
  $max = ($_.Group.total | Measure-Object -Maximum).Maximum
  [pscustomobject]@{session=[int]$_.Name; max=$max}
} | Sort-Object session
$deltas = for ($i=1; $i -lt $bySession.Count; $i++) {
  $prev = $bySession[$i-1]; $cur = $bySession[$i]
  [pscustomobject]@{from=$prev.session; to=$cur.session; delta=$cur.max - $prev.max}
}
```

## Actual
- Sessions: 48; transitions: 47
- Median |delta|: 692 tokens
- p90 |delta|: 1995 tokens
- Max increase: +12554 (S181->S182)
- Max drop: -5072 (S126->S127)

Top increases (delta in tokens):
| From | To | Delta |
| --- | --- | --- |
| 181 | 182 | +12554 |
| 188 | 191 | +4526 |
| 154 | 157 | +3697 |
| 127 | 129 | +3632 |
| 151 | 152 | +1988 |

Top drops:
| From | To | Delta |
| --- | --- | --- |
| 126 | 127 | -5072 |
| 182 | 186 | -1995 |
| 169 | 171 | -1984 |
| 165 | 167 | -1660 |
| 75 | 77 | -1637 |

## Diff
Expectation met. The max jump (+12554) and max drop (-5072) are far above the median |delta| (692), indicating punctuated changes rather than smooth drift.

## Implication
Supports ISO-4 (phase transition) + ISO-6 (entropy) mapping for swarm: proxy-K exhibits bursty jumps and discrete drops consistent with compaction events.

## Meta-swarm reflection
Proxy-k log lacks precomputed per-session deltas, forcing ad-hoc parsing. Consider a `tools/proxy_k.py --summary` mode to emit max/min and delta stats for faster entropy/phase-transition checks.
