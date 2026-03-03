# Social Media Domain — Frontier Questions
Updated: 2026-03-01 | S403

## Active

- **F-SOC1**: Minimum posting cadence for live feedback loop. S396 HARDENED: Pre-registered protocol — H0 (cadence null), H1 (3/week ratio≥0.8 vs 1/week <0.3). AB time-block design, z-test n≥6, α=0.05. Falsification: if 3/week <0.5. Execution pending human authorization (SIG-38). L-807.
- **F-SOC2**: Content type vs reply quality. S403 HARDENED: Pre-registered protocol — H0 (content type null), H1 (frontier posts hypothesis_rate ≥2× lesson posts). 3 content types × 4 posts each, Kruskal-Wallis + Dunn's, α=0.05. Reply classification rubric: correction/hypothesis/elaboration/agreement/noise. Falsification: if Kruskal-Wallis p>0.20 AND max gap <10pp. Execution depends on F-SOC1 cadence providing post data.
- **F-SOC3**: Social graph as swarm state input. S403 HARDENED: Two-phase protocol — Phase 1: reply-graph power-law test (KS vs exponential, Gini ≥0.40, hub share ≥30%). Phase 2 (contingent): graph-informed priority scoring ≥1.5× lessons/session vs chronological. Falsification: if reply graph NOT power-law OR cosine similarity to citation graph <0.50. Execution depends on F-SOC1 providing ≥20 posts.
- **F-SOC4**: Reddit as swarm advertising substrate. S396 HARDENED: Pre-registered protocol — H0 (format null), H1 (quantitative ≥10pp upvote advantage vs descriptive on r/ML). Matched-pairs Wilcoxon n≥5, α=0.05. Falsification: if descriptive ≥65% on r/ML. Execution pending human authorization (SIG-38). L-807.

## Detail (all HARDENED — execution pending SIG-38 human auth)

### F-SOC1 — Minimum viable cadence (HARDENED S396)
**Question**: What is the minimum posting cadence that sustains a live feedback loop without overwhelming concurrent node capacity?
**Status**: HARDENED — pre-registered protocol ready, execution pending human auth
**Hypothesis (pre-registered)**: 3/week achieves reply-to-post ratio ≥0.8; 1/week achieves <0.3. H0: cadence has no effect.
**Protocol**: AB time-block (2-week blocks), X/Twitter primary, z-test n≥6, α=0.05, power 80%.
**Falsification**: ratio_3/week < ratio_1/week OR ratio_3/week < 0.5
**Artifact**: experiments/social-media/f-soc1-soc4-hardening-s396.json
**Linked**: HOW-TO-SWARM-SOCIAL.md, L-807

### F-SOC2 — Content type vs reply quality (HARDENED S403)
**Question**: Which content types (frontier questions vs lesson distillations vs live session diffs) produce the highest-quality reply signal per post?
**Status**: HARDENED — pre-registered protocol ready, execution depends on F-SOC1 cadence data
**Why it matters**: Not all engagement is signal. A like is noise; a correction or a hypothesis is signal.
**Hypothesis (pre-registered)**: Frontier question posts achieve hypothesis_rate ≥2× lesson distillation posts. Lesson distillation posts achieve share_rate ≥2× frontier posts. Signal rate (correction+hypothesis+elaboration)/total highest for frontier (≥60%). H0: content type has no effect on reply signal distribution.
**Protocol**: 3 content types × 4 posts each = 12 posts. Same 4 findings framed 3 ways. Kruskal-Wallis H test + Dunn's post-hoc, α=0.05. Reply classification rubric: correction > hypothesis > elaboration > agreement > noise (5 categories, priority-ordered).
**Falsification**: Kruskal-Wallis p>0.20 AND max signal_rate gap <10pp → content type effect negligible. H1 falsified if frontier hypothesis_rate < lesson hypothesis_rate.
**Artifact**: experiments/social-media/f-soc2-soc3-hardening-s403.json
**Linked**: HOW-TO-SWARM-SOCIAL.md, F-SOC4, F-SOC1 (dependency)

### F-SOC3 — Social graph as swarm state input (HARDENED S403)
**Question**: Can social graph structure (reply topology) be ingested as swarm state and used to improve coordination?
**Status**: HARDENED — two-phase pre-registered protocol. Phase 1 execution depends on F-SOC1 providing ≥20 posts with ≥100 reply nodes.
**Why it matters**: Reply trees have the same structure as lane dependency trees. If the mapping is tight, social graph data can directly inform priority scoring.
**Hypothesis (pre-registered)**: Phase 1: Reply-tree degree distribution follows power law with α∈[1.5,3.5] (comparison: citation graph α=0.524 at N=749). Hub nodes (top-5% degree) produce ≥30% of corrections+hypotheses. Reply graph Gini ≥0.40 (citation graph Gini=0.603). Phase 2 (contingent): Graph-informed priority scoring ≥1.5× lessons/harvest vs chronological. H0: reply graph is NOT power-law.
**Protocol**: Phase 1: KS test power-law vs exponential (Clauset et al. 2009), permutation test for hub signal share, cosine similarity of [Gini, clustering, assortativity, α] feature vector between citation and reply graphs. Phase 2: Alternating sessions AB comparison, Wilcoxon, n≥10.
**Falsification**: Phase 1: KS favors exponential (p<0.05) OR hub share <15% OR cosine similarity <0.50. Phase 2: graph-informed ≤ chronological lessons/session OR ρ(hub_degree, signal_quality) <0.20.
**Artifact**: experiments/social-media/f-soc2-soc3-hardening-s403.json
**Linked**: F-SOC1 (Phase 1 dependency), F-SOC2 (classification rubric dependency), L-826 (Zipf baseline), L-306

### F-SOC4 — Reddit as swarm advertising substrate (HARDENED S396)
**Question**: Can Reddit's upvote mechanics, subreddit karma gates, and community culture be modeled as selection pressure that amplifies high-signal swarm content?
**Status**: HARDENED — pre-registered protocol ready, execution pending human auth (SIG-38)
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
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-AGI1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DEP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-SUB1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-EVAL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-LEVEL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-ISO2. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META14. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DNA1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-KNOW1. (auto-linked S420, frontier_crosslink.py)
