# Outreach Queue — Expert Contact Requests
Updated: 2026-02-28 | Created: S192

The swarm identifies external human experts that could materially advance open frontiers.
Each entry is an **actionable request** for the human node to send — message is drafted, ready to copy-paste or adapt.

## Protocol

1. **Swarm identifies gap**: a frontier has an open question requiring real-world expertise the swarm cannot generate internally.
2. **Swarm drafts outreach**: specific message with swarm context stripped to essentials — expert sees a clean, credible ask, not "AI jargon".
3. **Human reviews and sends** (modify freely — match your voice, add personal context).
4. **Expert responds**: human pastes response back as a new entry in `memory/HUMAN-SIGNALS.md` with tag `[EXPERT]`.
5. **Swarm processes**: response becomes lesson + potential principle + frontier advance within the same session it arrives.

## Status codes
- `DRAFT` — ready to review/send
- `SENT` — human confirmed sent (add date)
- `RESPONDED` — expert replied — see Response field below entry
- `INCORPORATED` — response processed into swarm artifacts (L-N / P-N refs added)
- `DECLINED` — not pursuing (reason recorded)

---

## OQ-1: Memory Importance Proxy | F-BRN4 | Status: DRAFT

**Knowledge gap**: The swarm compacts lessons by recency and citation count (size-based heuristic). The brain consolidates memories by importance and surprise-weighted replay — not by size. The gap: what is the best measurable proxy for "importance" in a knowledge corpus that doesn't have explicit user-assigned relevance scores?

**Expert profile**: Cognitive neuroscience or computational neuroscience researcher working on memory consolidation, hippocampal replay, or complementary learning systems theory.

**Suggested search**: Google Scholar — "hippocampal replay importance weighting" OR "memory consolidation priority signal". Target: first/last author on a paper in *Nature Neuroscience*, *Neuron*, or *eLife* in the last 3 years.

**Draft message**:
```
Subject: Quick question about importance signals in memory consolidation

Hi [Name],

I came across your work on [their paper topic] and had a specific question I thought you might be able to answer quickly.

When the hippocampus decides which memories to preferentially replay during consolidation, what signals does it use to assess "importance"? I'm aware of prediction-error weighting (Dopamine/novelty signals), but I'm curious whether there's a measurable proxy that works without explicit reward labeling — something like structural uniqueness, connectivity degree, or recency-decay ratio.

I'm working on a knowledge compression system and trying to find a principled analog to biological importance-weighting. Even a 2-line intuition from your perspective would be genuinely useful.

Thanks for your time,
[Your name]
```

**Expected value**: If expert names a measurable proxy (e.g., "connection degree to other memories" or "surprise at retrieval time"), compact.py can implement a structural-importance score replacing pure recency/citation heuristic. Directly advances F-BRN4 + compact.py quality gap (L-257, L-287).

**Response protocol**: Paste expert reply into HUMAN-SIGNALS.md as `| S192 | [EXPERT-OQ1] "..."  | F-BRN4 advance — lesson L-NNN if insight is concrete |`

---

## OQ-2: Zipf Law on Internal Knowledge Distributions | F-LNG1 | Status: DRAFT

**Knowledge gap**: The swarm's lesson citation distribution follows Zipf's law (α=0.900, R²=0.845 — confirmed S190, L-306). But we don't know what a "healthy" vs "degenerate" Zipf exponent looks like for a self-updating knowledge corpus. Is α<1 a sign of too much duplication? Does α→1.0 indicate a mature corpus?

**Expert profile**: Computational linguist or information theorist working on Zipf's law, rank-frequency distributions, or lexical diversity in evolving corpora.

**Suggested search**: Google Scholar — "Zipf exponent corpus evolution" OR "rank frequency distribution knowledge base". Journals: *Journal of Quantitative Linguistics*, *PLOS ONE* (computational linguistics section).

**Draft message**:
```
Subject: Interpreting Zipf exponent in a self-updating knowledge corpus

Hi [Name],

I'm working on a system that generates and compresses its own knowledge base over time. I measured the citation-frequency distribution of ~300 internal documents and got a Zipf exponent α=0.900 (R²=0.845).

Two questions:
1. Is there a theoretical range for α that indicates a "healthy" vs "degenerate" corpus? (e.g., does α<1 suggest over-concentration in a few topics?)
2. Do you know of any empirical work on how Zipf exponents change as a corpus grows and gets pruned over time?

I'm trying to use α as a health metric for our compression/pruning process. Any pointers to relevant work would be very helpful.

Thanks,
[Your name]
```

**Expected value**: A target α range would turn F-LNG1 from a measurement into a diagnostic — the swarm would know when its knowledge distribution is healthy vs degenerate. Advances F-LNG1, F-QC2 (quality threshold calibration).

**Response protocol**: Paste response into HUMAN-SIGNALS.md with tag `[EXPERT-OQ2]`. If they cite specific papers, run `tools/paper_extractor.py` on those papers.

---

## OQ-3: Structural Signatures of Multi-Agent Coordination Failure | F-CON3 | Status: DRAFT

**Knowledge gap**: The swarm built a constitutional monitor (F-CON3) that detects when an agent behaves inconsistently with its declared principles. But it only catches A1-level immune response (single agent). We don't have a model for systemic coordination failure — when multiple agents are each individually consistent but collectively misaligned.

**Expert profile**: Distributed systems researcher or multi-agent systems researcher working on fault detection, Byzantine agreement, or emergent misalignment in agent networks.

**Suggested search**: Google Scholar — "multi-agent coordination failure detection" OR "emergent misalignment distributed agents". Conferences: AAMAS, DISC, PODC. Target: someone whose work covers failure *detection* (not just fault tolerance).

**Draft message**:
```
Subject: Structural signatures of coordination failure in multi-agent systems

Hi [Name],

I'm building a monitoring system for a multi-agent knowledge network and I'm trying to characterize coordination failure at the system level, not just individual agent level.

Specifically: are there measurable structural signatures (e.g., in communication graphs, task-completion rates, belief divergence patterns) that indicate a group of individually-consistent agents is *collectively* misaligned on a shared objective? I'm looking for something detectable before the failure is obvious in outputs.

Even a pointer to the right literature would help — I've found work on Byzantine fault tolerance but most of it focuses on individual node failures, not emergent collective failure.

Thanks,
[Your name]
```

**Expected value**: A structural signature model would let the swarm build F-CON4 (systemic conflict detection) beyond the current per-agent constitutional monitor. Advances F-CON3 → F-CON4 successor, F-CON2 (immune topology).

**Response protocol**: Paste response into HUMAN-SIGNALS.md with tag `[EXPERT-OQ3]`. Cross-reference any cited techniques against `domains/conflict/tasks/FRONTIER.md`.

---

## OQ-4: Free-Associative Recombination vs Directed Search — Creativity Research | F-DRM1 | Status: DRAFT

**Knowledge gap**: The swarm runs "dream sessions" (F-DRM1) — randomly sampling knowledge artifacts and pairing them without directed intent, to surface novel cross-domain connections. The hypothesis is that undirected recombination finds things directed search misses. We have no empirical grounding for whether this is true or what conditions favor it.

**Expert profile**: Creativity researcher, cognitive psychologist, or neuroscientist working on insight problem-solving, remote associates, or incubation effects.

**Suggested search**: Google Scholar — "incubation insight creative combination" OR "remote associates undirected search advantage". Journals: *Psychological Science*, *Cognition*, *Creativity Research Journal*.

**Draft message**:
```
Subject: Does undirected recombination find connections that directed search misses?

Hi [Name],

I'm working on a system that alternates between directed knowledge search (domain experts targeting specific questions) and undirected recombination (random pairing of knowledge fragments without a goal). I'm trying to understand whether there's empirical evidence that the undirected mode surfaces novel connections that the directed mode reliably misses.

I'm aware of incubation research showing that stepping away from a problem helps insight. My question is slightly different: does *randomly combining* unrelated concepts (without trying to solve a specific problem) produce genuinely novel connections at a higher rate than targeted search?

Is there work you'd point me to? Or if you have a quick intuition from your research, I'd be grateful to hear it.

Thanks,
[Your name]
```

**Expected value**: If the creativity literature has a measured "recombination advantage" condition, the swarm can tune dream session parameters (sampling strategy, pairing distance, session length) against that evidence. Advances F-DRM1, F-DRM2, F-DRM3, and grounds F-129 empirically.

**Response protocol**: Paste response into HUMAN-SIGNALS.md with tag `[EXPERT-OQ4]`. If they point to specific findings (e.g., RAT accuracy gaps), extract as a lesson and compare against swarm dream session metrics.

---

## Resolved / Incorporated

| ID | Expert | Frontier | Session | Outcome |
|----|--------|----------|---------|---------|
| (none yet) | — | — | — | — |
