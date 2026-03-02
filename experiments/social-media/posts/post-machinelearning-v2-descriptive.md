# r/MachineLearning — Matched-Pair Version B (Descriptive-First)
Platform: Reddit | Subreddit: r/MachineLearning
Status: DRAFT | F-SOC4 matched-pair design
Pair: B (descriptive-first) — leads with narrative, uses numbers as support
Updated: S398 (2026-03-01) | Prior version: S299 (304L, alpha=0.900)

---

## TITLE
[D] What happens when you let an AI build a knowledge base across 398 sessions — and why our initial scaling prediction was wrong

---

## BODY

For the past few months, we've been running a continuous experiment: an LLM reads a git repository, does work, writes down what it learned, and commits. The next session reads what the last one wrote. We're now at 398 sessions and 749 accumulated lessons.

The interesting part isn't the accumulation — it's what happened to the structure.

**The system organizes itself, but not the way we predicted.**

Early on (304 lessons, ~6 domains), the citation distribution — how often each lesson gets referenced by future sessions — followed Zipf's law almost exactly: alpha=0.900, R²=0.845. A small number of foundational lessons dominated recall. We predicted this would strengthen as the corpus matured, with alpha converging toward the canonical 1.0.

We were wrong.

At 749 lessons across 43 domains, the distribution shifted dramatically. Alpha dropped to 0.524. The fit actually got *better* (R² = 0.975), but the shape changed: the tail fattened. More lessons are getting moderate citation counts instead of a few hoarding all the references.

**Why? Three things changed.**

First, the system expanded from 6 domains to 43. Each domain creates its own citation cluster — distributed systems lessons cite distributed systems lessons, not linguistics findings. This fragments the global citation hierarchy.

Second, we started running sessions that scan the entire corpus for recurring patterns and extract principles. These batch events (one session cited 149 prior lessons to extract 10 principles) inflate the mid-ranked citations disproportionately.

Third, a hub shift occurred. The most-cited lesson changed from L-001 (the original coordination principles, cited 53 times) to L-601 (a structural enforcement theorem, cited 163 times). L-601 didn't get cited because it was early — it appeared at session 355 and accumulated 163 citations in 44% of the corpus lifetime. It got cited because it explains something fundamental about how the system fails.

**The part that still surprises us:**

20.4% of lessons are citation-isolated — no other lesson references them. At N=304, this was only 5.6%. The system is producing more knowledge that doesn't connect. Whether this is a retrieval failure (sessions don't find relevant prior work) or genuine partitioning (some knowledge is terminal, not foundational) is an open question.

The other surprise: 193 principles have been extracted from the 749 lessons. Principles are higher-level generalizations that recur across domains. The principle extraction rate (~0.26 per lesson) has been stable since session 200, suggesting a consistent compression ratio from specific findings to general patterns.

**What this is and isn't:**

This is a coordination methodology, not AGI. Each session requires a human to start it. The self-direction is real (sessions choose what to work on), but invocation is manual. The "self-improvement" is structural — the repo gets more organized, not less — verified by measuring compaction rate, citation density, and belief revision frequency.

The repo is public if you want to dig into the data: [link]

---

## SCORING NOTES (F-SOC4 protocol)
- Descriptive-first: narrative hook in first paragraph, numbers embedded in story
- Same core data as Version A but framed as discovery narrative
- Methodology implicit (mentioned but not foregrounded)
- Open questions framed as mysteries rather than testable predictions
