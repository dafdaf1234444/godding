# F103: Swarm vs Single Claude — Causal Emergence EWS Analysis
**Session**: 52 | **Date**: 2026-02-27 | **Status**: PARTIAL — first test run, evidence gathered

## Task
Analyze the user's `complexity_ising_idea` project (causal emergence early warning signals for phase transitions) using parallel swarm agents. Compare coverage to what single Claude would produce.

## Setup

**Target**: `<your-repos>/complexity_ising_idea/`
**State at analysis**: v5 + P1 complete (5 iterations; EI ratio = artifact, Excess E(k=1) = recommended)
**Agents spawned**: 3 parallel sub-agents (wall time: ~120s)

| Agent | Task | Key Tool |
|-------|------|---------|
| A1 | NK complexity analysis of src/ | nk_analyze.py |
| A2 | Scientific results + open questions | Deep reading of SUMMARY.md, results/ |
| A3 | Implementation correctness review | Code audit of ei_compute.py, phase1_p1_comparison.py |

## Agent Findings

### A1: NK Structural Analysis
- **N=8 modules**, K_avg=0.0, cycles=0, composite=0.0, burden=0.8
- Architecture: **perfectly decoupled** — zero inter-module imports
- All modules depend only on external libs (numpy, scipy, matplotlib)
- 13 tests in 2 test files; moderate coverage
- **Verdict**: EXCELLENT for research code. Safe to extend without coupling risk.
- Connection to swarm knowledge: P-063 (stigmergy → clean NK); P-035 (count N, K, hubs)

### A2: Scientific Results + Open Questions
1. **Strongest caveat on E(k=1)**: plug-in entropy bias at finite N; NSB estimator not tested. Peak location uncertainty ±0.05K.
2. **Highest impact-per-effort experiment**: Analytical EI from exact TPM (1-2 days, resolves physical vs. artifact definitively).
3. **Falsification test**: Compute E(k=1) under Wolff dynamics. If peak collapses → signal is autocorrelation artifact (same as what killed EI ratio in v4).
4. **Publishable negative result**: needs analytical EI + Wolff E(k=1) + finite-size scaling (3-4 experiments, ~2 weeks).
5. **E(k=1) vs autocorrelation**: ~70% overlap but 0.05K peak offset and nonlinear content. Not identical, but not independent.

### A3: Implementation Review
1. **Excess Entropy formula**: CORRECT mathematically. I(X_{0:k}; X_{k:2k}).
2. **EI computation**: CORRECT. Scaled Laplace (alpha=1/n_states), min_obs filter, subsampling.
3. **Critical gap**: NO shuffle/null test for E(k=1) specifically. Artifacts possible.
4. **Error bars underestimated 2-3×**: SE calculation ignores within-seed autocorrelation. True SE ≈ reported × sqrt(τ_acf).
5. Total Correlation results unreliable (drop them from any publication).

## Cross-Agent Synthesis (Parent Only)

**Convergent finding** (A2+A3 independently, stronger than either alone):
- A2: "Wolff test of E(k=1) is the critical falsification"
- A3: "E(k=1) has no shuffle baseline"
- **Synthesis**: Both agents identified the same gap from different angles. The E(k=1) recommendation in SUMMARY.md is currently unvalidated by the same falsification rigor that killed EI.

**Most actionable recommendation**: Write `phase1_v6_wolff_e1.py` — a single script that:
1. Runs both Metropolis and Wolff sampling on same seeds, same temperatures
2. Computes E(k=1) + shuffle baseline under both dynamics
3. Corrects error bars for autocorrelation (τ_acf from lag-1 of time series)
4. Reports: does E(k=1) survive Wolff? Does it survive shuffle control?

If it PASSES: E(k=1) is a genuine, dynamics-independent EWS. Ready for publication with stronger claims.
If it FAILS: The "recommended alternative" is also an artifact. Project is cleanly negative. Still publishable.

**NK insight** (A1 only, swarm-specific):
The zero-coupling architecture is directly relevant to how experiments are added. Researchers can safely add `phase1_v6_wolff_e1.py` without touching any src/ module — the clean DAG ensures no cascading issues.

## Swarm vs Single Claude: Assessment

**Single Claude would produce:**
- Read SUMMARY.md → suggest "analytical EI" (CLAUDE.md Tier 1 item)
- Possibly notice error bar issues if reading code carefully
- Unlikely to run NK analysis (requires knowing nk_analyze.py exists)

**Swarm added:**
1. **Breadth**: NK structural analysis + scientific review + implementation audit simultaneously
2. **Cross-validation**: Two independent agents reached the same "Wolff test for E(k=1)" conclusion
3. **NK expertise**: Swarm's 26 NK lessons applied directly to codebase → zero-coupling insight + safe-extension verdict
4. **Novel synthesis**: "Error bars underestimated 2-3×" + "no shuffle baseline" together = E(k=1) recommendation is unvalidated by the project's own rigor standards

**Honest verdict**: Single strong Claude would likely suggest the same experiments. The swarm's primary advantages were:
- Speed (parallel: 120s vs ~263s sequential)
- NK structural analysis (would require explicit instruction to single Claude)
- Cross-agent convergence as confidence signal (two independent agents → one finding = stronger than one)

**Score**: Swarm was FASTER and MORE COMPREHENSIVE, but not qualitatively different. The value is ADDITIVE (breadth + confidence), not TRANSFORMATIVE (insight single Claude couldn't find). This is honest: for a mature well-documented project, single Claude is nearly as good. Swarm advantage likely larger for:
- Less well-documented projects (no SUMMARY.md to read)
- Projects requiring multiple domain expertise simultaneously
- Tasks where parallelism is structural (not just speedup)

## Next Steps for This Project

Priority order (based on F103 synthesis):
1. `phase1_v6_wolff_e1.py` — Wolff + shuffle control for E(k=1) (resolves whether recommendation is valid)
2. Correct error bars in P1 results (4 hours, high confidence gain)
3. Analytical EI from exact TPM (1-2 days, definitively resolves EI physics vs artifact)
4. Finite-size scaling L=16,24,32,48 (3-5 days, needed for publication)

## Lesson for F103

**Finding**: Swarm demonstrated parallel analysis advantage. Not qualitatively superior to single Claude on well-documented projects, but meaningfully faster and more comprehensive. The "cross-agent convergence = stronger confidence" effect is real and valuable.

**Refined F103 question**: For future tests, choose tasks where:
- Multiple domains needed simultaneously (NK + distributed systems + code quality)
- Documentation is sparse (swarm memory fills gaps single Claude can't)
- Synthesis across independent agents produces genuinely novel insight

See L-105 for extracted lesson.
