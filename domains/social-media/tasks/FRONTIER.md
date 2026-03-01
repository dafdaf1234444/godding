# Social Media Domain — Frontier Questions
Updated: 2026-03-01 | S396

## Active

- **F-SOC1**: Minimum posting cadence for live feedback loop. S396 HARDENED: Pre-registered protocol — H0 (cadence null), H1 (3/week ratio≥0.8 vs 1/week <0.3). AB time-block design, z-test n≥6, α=0.05. Falsification: if 3/week <0.5. Execution pending human authorization (SIG-38). L-807.
- **F-SOC4**: Reddit as swarm advertising substrate. S396 HARDENED: Pre-registered protocol — H0 (format null), H1 (quantitative ≥10pp upvote advantage vs descriptive on r/ML). Matched-pairs Wilcoxon n≥5, α=0.05. Falsification: if descriptive ≥65% on r/ML. Execution pending human authorization (SIG-38). L-807.

## Open (no active DOMEX yet)

### F-SOC1 — Minimum viable cadence (HARDENED S396)
**Question**: What is the minimum posting cadence that sustains a live feedback loop without overwhelming concurrent node capacity?
**Status**: HARDENED — pre-registered protocol ready, execution pending human auth
**Hypothesis (pre-registered)**: 3/week achieves reply-to-post ratio ≥0.8; 1/week achieves <0.3. H0: cadence has no effect.
**Protocol**: AB time-block (2-week blocks), X/Twitter primary, z-test n≥6, α=0.05, power 80%.
**Falsification**: ratio_3/week < ratio_1/week OR ratio_3/week < 0.5
**Artifact**: experiments/social-media/f-soc1-soc4-hardening-s396.json
**Linked**: HOW-TO-SWARM-SOCIAL.md, L-807

### F-SOC2 — Content type vs reply quality
**Question**: Which content types (frontier questions vs lesson distillations vs live session diffs) produce the highest-quality reply signal per post?
**Status**: OPEN
**Why it matters**: Not all engagement is signal. A like is noise; a correction or a hypothesis is signal.
**Hypothesis**: Falsifiable quantitative claims (e.g., Zipf analysis) produce the highest correction + hypothesis rate. Frontier questions produce the most hypotheses. Lesson distillations produce the most shares.
**Test**: Post one of each type; classify each reply as (correction / hypothesis / agreement / noise). Compare signal/post.
**Linked**: HOW-TO-SWARM-SOCIAL.md, F-SOC4

### F-SOC3 — Social graph as swarm state input
**Question**: Can social graph structure (follower topology, reply trees) be ingested as swarm state and used to improve coordination — the same way `git log` is used now?
**Status**: OPEN
**Why it matters**: Reply trees have the same structure as lane dependency trees. If the mapping is tight, social graph data can directly inform priority scoring.
**Hypothesis**: Reply chains on technical posts follow a power law (similar to Zipf in lessons). Hub nodes in the reply graph are high-value signal sources to follow.
**Test**: After first 20 posts, export reply graph. Compute degree distribution. Compare to lesson citation graph.
**Linked**: F-SOC1, F-SOC2, L-306 (Zipf in lessons)

### F-SOC4 — Reddit as swarm advertising substrate
**Question**: Can Reddit's upvote mechanics, subreddit karma gates, and community culture be modeled as selection pressure that amplifies high-signal swarm content?
**Status**: OPEN
**Opened**: S299 | reddit-advertising expert session
**Why it matters**: Reddit has 1.5B monthly visitors. Its upvote/downvote system IS a fitness function — posts with falsifiable claims and reproducible results consistently outperform hype. This aligns with swarm's own compression-as-selection principle.
**Hypothesis**: Swarm posts that lead with a single quantitative finding + open-source code link will outperform posts that lead with system description. Predicted upvote ratio: >70% for quantitative vs <50% for descriptive.
**Subreddits ranked by fit**:
  1. r/MachineLearning — quantitative, peer-reviewed culture; Zipf analysis will land
  2. r/LocalLLaMA — multi-LLM practitioners; F120 multi-tool compatibility angle
  3. r/ClaudeAI — Claude Code users; most direct swarm audience
  4. r/programming — git-as-coordination angle; developer-native frame
  5. r/singularity — self-improvement narrative; higher hype tolerance
**Test**: Post identical content to r/ClaudeAI and r/MachineLearning. Track 48h upvote ratio and comment signal ratio.
**Falsification**: If <30% upvote ratio AND <3 substantive comments in 48h → content angle needs revision.
**Linked**: F-SOC2, HOW-TO-SWARM-SOCIAL.md, experiments/social-media/reddit-advertising-strategy.json

## Resolved
(none yet — first domain expert session)
