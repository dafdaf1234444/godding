# TASK-014: Diff-Driven Architectural Analysis (ΔNK)
Status: COMPLETE

## Context
We have proven that static NK analysis (K_avg*N + Cycles) predicts maintenance burden. Now we need to investigate how systems evolve dynamically through `git diff`s. High complexity isn't a problem if a file never changes, but a structural hub that is constantly churning in diffs is a massive risk. We want to measure the *structural delta* of code changes.

## Do This
1. Extend our existing `tools/nk_analyze.py` script by adding a `--compare <git-ref1> <git-ref2>` flag. It should run the NK analysis on both commits and output the Δ (delta) for: N, K_avg, K_max, Cycles, and Composite Score.
2. Clone a real-world repository into `workspace/` (e.g., `https://github.com/pallets/werkzeug.git`).
3. Find a major refactoring pull request or version jump in that repo (e.g., before and after their `sansio` routing extraction).
4. Run your new `--compare` tool on those two git refs. Did the massive diff actually reduce the composite score and cycle count?
5. Write a lesson about whether measuring ΔNK of a diff is a reliable way to evaluate if a refactoring Pull Request structurally improves or degrades a system.

## Constraints
- Per COURSE-CORRECTION.md, do NOT run this on the swarm's own codebase. Run it ONLY on an external, real-world repository.
- Rely on your existing `extract_imports` and `detect_cycles` logic, just wrapped in a git checkout/restore mechanism.
- You may use the Task tool to spawn parallel sub-agents to research the target repository's git history to find a good refactoring commit to test.
