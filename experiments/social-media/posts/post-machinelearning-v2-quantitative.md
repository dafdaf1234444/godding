# r/MachineLearning — Matched-Pair Version A (Quantitative-First)
Platform: Reddit | Subreddit: r/MachineLearning
Status: DRAFT | F-SOC4 matched-pair design
Pair: A (quantitative-first) — leads with data, methodology, findings
Updated: S398 (2026-03-01) | Prior version: S299 (304L, alpha=0.900)

---

## TITLE
[D] Citation frequency in a 749-lesson AI corpus diverges from Zipf: alpha dropped from 0.900 to 0.524 as corpus scaled 2.5x

---

## BODY

We maintain a self-improving LLM knowledge base — a git repo where each session reads prior state, does work, distills findings into lesson files, and commits. We measured citation frequency distribution at two scale points.

**The data:**

| Metric | S190 (N=304) | S398 (N=749) | Delta |
|--------|-------------|-------------|-------|
| Lessons | 304 | 749 | +146% |
| Zipf alpha | 0.900 | 0.524 | -0.376 |
| R² | 0.845 | 0.975 | +0.130 |
| Cited ≥1 | 94.4% | 79.6% | -14.8pp |
| Top citation | L-001 (38) | L-601 (163) | hub shift |
| Principles | 0 | 193 | extracted |
| Domains | 6 | 43 | +617% |

**Method:** Each lesson is a markdown file. Sessions cross-reference prior lessons with `L-NNN` patterns. We count incoming citation edges per lesson, rank by frequency, and fit log(frequency) ~ -alpha * log(rank) via OLS on top-200 ranked items.

**Key findings:**

1. **Alpha decreased, not increased.** Prior prediction: alpha would drift toward canonical Zipf (1.0) as corpus matured. Actual: alpha dropped to 0.524. The tail fattened — newer lessons accumulated citations more proportionally than expected.

2. **R² improved dramatically.** The power law fit got better (0.845 → 0.975) even as the exponent dropped. The distribution is more cleanly power-law at N=749 than at N=304, just with a different exponent.

3. **Hub concentration increased.** L-601 (a structural enforcement theorem) accumulated 163 citations — 3.1x the #2 lesson (L-001 at 53). The top hub shifted from a foundational lesson to a mid-corpus finding. This suggests hub identity is not determined by primacy but by explanatory utility.

4. **Citation coverage dropped.** 79.6% cited ≥1 (down from 94.4%). 20.4% of lessons are citation-isolated — they contribute knowledge but aren't referenced by subsequent work.

**Why alpha < 1.0 and decreasing:**

We hypothesize three mechanisms:
- **Domain expansion** (6→43 domains): Creates independent citation clusters, flattening the global distribution
- **Batch citation events**: Principle extraction scans (10+ principles from 149 lessons in one session) inflate mid-ranked citations
- **Hub gravity**: L-601 accumulated citations at 16x the per-lesson average, consistent with preferential attachment with a superlinear kernel

**Open questions:**
- Is alpha=0.524 an equilibrium or still converging? We predict measurement at N=1500.
- Does the hub shift (L-001 → L-601) reflect a phase transition in what the system considers "foundational"?
- Is citation isolation (20.4%) a retrieval failure or genuine knowledge partitioning?

Raw data: `experiments/linguistics/f-lng1-zipf-lessons-s190.json` (original), re-measurement at S398 in repo.

---

## SCORING NOTES (F-SOC4 protocol)
- Quantitative-first: numbers in first paragraph, table before narrative
- Leads with measurement discrepancy (alpha dropped vs prediction)
- Methodology section explicit
- Open questions framed as testable predictions
