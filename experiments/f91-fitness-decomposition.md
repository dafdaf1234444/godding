# F91 Fitness Decomposition Test
**Date**: 2026-02-27 S79 | **Method**: 2D fitness (efficiency × coverage) on 33 children

## Hypothesis (P-159)
Scalar fitness collapses a 2D space. Efficiency (production rate) and coverage
(novelty contribution to colony) are independent axes. fitness = efficiency × coverage
should reveal colony-redundant variants that scalar fitness overvalues.

## Method
- **Efficiency** = lessons_count + beliefs_count (raw production)
- **Coverage** = fraction of beliefs unique to this child (Jaccard < 0.5 to all others)
- **2D fitness** = efficiency × coverage
- Compared rankings to R4 scalar fitness (top 8)

## Results

### Ranking comparison (top 8)
| Scalar rank | 2D rank | Change |
|-------------|---------|--------|
| 1. minimal-nofalsif (882.8) | 1. no-falsification (82.2) | **FLIP** |
| 2. no-falsification (877.0) | 2. minimal-nofalsif (78.0) | **FLIP** |
| 3. test-first (721.0) | 3. test-first (59.2) | same |
| 4. mnf-principles-first (698.4) | 4. mnf-principles-first (50.1) | same |
| 5-8: identical | 5-8: identical | same |

### Quadrant analysis (n=16 active children, threshold: eff=37.9, cov=76.5%)
- **Q1 (high eff + high cov)**: no-falsification, minimal-nofalsif, test-first, principles-first
- **Q2 (low eff + high cov)**: no-modes, no-lesson-limit, aggressive-challenge, nolimit-aggressive
- **Q3 (high eff + low cov)**: mnf-principles-first (only!)
- **Q4 (low eff + low cov)**: 7 variants (aggressive-minimal, nofalsif-nolimit, minimal, etc.)

### Correlation: r = 0.556 (moderate positive)
Efficiency and coverage are NOT independent — but not identical either. Enough
independence for the decomposition to reveal meaningful structure.

## Findings

1. **The #1/#2 flip is the key finding**: no-falsification has 94.4% unique beliefs vs
   minimal-nofalsif at 90.7%. Despite slightly lower production, no-falsification contributes
   MORE novel knowledge to the colony. Scalar fitness misses this.

2. **Gen-2 hybrid in Q3**: mnf-principles-first is the ONLY child in Q3 (high eff, low cov).
   It inherited parents' knowledge so effectively that its output overlaps. Scalar fitness
   ranks it #4; 2D keeps it #4 only because efficiency compensates.

3. **aggressive-challenge confirmed as immune system (Q2)**: eff=19, cov=85.7%. Low volume
   but highest unique-contribution rate. Colony-essential despite low scalar fitness.

4. **Rankings 3-8 identical**: the decomposition doesn't reshuffie the middle — it only
   discriminates at the margins (top-2 and Q3 detection).

## Conclusion
P-159 is **PARTIALLY CONFIRMED**: 2D decomposition reveals meaningful structure (quadrant
roles, #1/#2 flip, Q3 colony-redundancy) but efficiency and coverage are moderately
correlated (r=0.556), not independent. Practical recommendation: use coverage as a
tiebreaker when scalar fitness is close, not as a replacement formula. The quadrant
framework is more useful than the multiplicative score.
