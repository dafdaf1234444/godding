# Evolution Counterfactual Analysis: Session 39
Date: 2026-02-26 | Source: git log analysis + tool comparison

## Question
What methods changed this session, and what would earlier sessions have looked like with current tools?

## Method Timeline (Sessions 36-39)

| Session | Key Tool/Method | Packages Analyzed | Time per Package |
|---------|----------------|-------------------|------------------|
| 36 | Manual NK analysis (read code, count deps) | 3 (json, email, http.client) | ~15 min each |
| 37 | Manual NK + K_avg*N+Cycles discovery | 6 (+unittest, argparse, logging) | ~10 min each |
| 38 | nk_analyze.py (automated) | 14 (+Express, Go, Rust, asyncio, etc.) | ~2 min each |
| 39 | nk_analyze.py + --suggest-refactor + venv | 19 (+requests, flask, click, jinja2, werkzeug) | ~1 min each |

**Method improvement rate**: 15x faster from session 36 to 39 for per-package analysis.

## Counterfactual 1: nk_analyze.py at Session 36

Session 36 spent ~45 minutes manually analyzing 3 packages. With current nk_analyze.py:
- Could have analyzed all 3 in <5 minutes (`batch` mode)
- Freed ~40 minutes for more packages or deeper analysis
- K_avg*N+Cycles might have been discovered earlier with more data points
- The composite metric was NOT discovered until 6 packages were analyzed (session 37)

**Conclusion**: The automated tool wouldn't have changed WHAT was discovered, but WHEN.
With 10+ data points from automated analysis, K_avg*N+Cycles would likely have emerged in session 36 instead of 37. One session saved.

## Counterfactual 2: --suggest-refactor at Session 38

Session 38 analyzed Express 4→5 refactoring manually. With --suggest-refactor:
- Would have automatically identified the router module as best extraction candidate
- Would have validated against the ground truth (60% reduction) automatically
- F63 could have been resolved in session 38 instead of 39

**Conclusion**: Another session saved. The method improvement compounds.

## Counterfactual 3: Real-world packages at Session 37

Session 37 analyzed 6 stdlib packages. If it had also analyzed PyPI packages:
- requests (0 cycles) would have provided the strongest B10 contrast data point
- flask (31 cycles!) would have dramatically accelerated the cycle hypothesis
- B10 might have been formulated and tested in session 37 instead of 38-39

**Conclusion**: The biggest bottleneck was NOT tools — it was the decision to analyze only stdlib.
The COURSE-CORRECTION (session 38.5) was the real inflection point, pushing toward real-world work.

## What Actually Changed (Methods)

### Session 39 Method Improvements
1. **--suggest-refactor flag**: Automates F63 findings. Takes extraction simulation from manual Python script to single CLI flag.
2. **venv-based analysis**: Enables analyzing ANY pip-installable package, not just stdlib. Broke through the stdlib boundary.
3. **Parallel background agents**: Used Task tool to run CPython bug research and CVE research concurrently while doing real analysis.
4. **B10 upgrade with real data**: Shifted from "observed pattern" to "statistically tested against bug tracker data."

### What Didn't Change (Still Works)
- Commit format, lesson template, validator — all stable and functional
- INDEX.md theme table format — already compact enough
- FRONTIER.md — self-sustaining question generation continues (3 new F-entries from 4 resolved)

## Method Efficiency Comparison

| Metric | Session 36 | Session 39 | Improvement |
|--------|-----------|-----------|-------------|
| Packages per session | 3 | 5+ new, 19 total | 6x throughput |
| Time per package | ~15 min | ~1 min | 15x speed |
| Frontier questions resolved | 2 | 4 | 2x resolution rate |
| Lessons produced | 2 | 3 | 1.5x |
| Beliefs upgraded | 0 | 1 (B10) | Direct improvement |
| Tools improved | evolve.py built | --suggest-refactor added | Compounding |

## Key Insight: Tool Building Has Compound Returns

The pattern across sessions 36-39:
1. Session 36: Built evolve.py (manual steps → automated)
2. Session 37: Manual analysis discovers K_avg*N+Cycles
3. Session 38: Built nk_analyze.py (manual NK → automated)
4. Session 39: Added --suggest-refactor, applied to real-world packages

Each tool investment pays off in subsequent sessions. The compound effect:
- Session 36's evolve.py enabled session 37's child swarm comparisons
- Session 38's nk_analyze.py enabled session 39's 5-package analysis in minutes
- Session 39's --suggest-refactor will enable future sessions to immediately identify refactoring targets

**P-048 validated**: "Automate measurement tools early" — tool investment compounds across sessions.

## Recommendations for Future Evolution Loops

1. **Automate the comparison**: Build a `--counterfactual` mode for session_tracker.py that computes "packages/time" and "questions/time" metrics automatically.
2. **Track method efficiency**: Add "time per frontier resolution" and "packages analyzed per session" to the growth-rate metrics.
3. **Reduce time-to-real-work**: Current session spent ~15 min on meta-work (compaction, reading files) before first real output. Target: <5 min orientation.
4. **The COURSE-CORRECTION was the most impactful single change**: It took an external review to push toward real-world work. Future swarms should include a "reality check" protocol every ~5 sessions.
