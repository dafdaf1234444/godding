# NK Predictive Power Analysis (F65/F79)
Date: 2026-02-26 | Session: 41

## Question
Can NK composite/cycles predict maintenance burden or refactoring need?

## Dataset
11 PyPI packages + 3 stdlib packages analyzed.

## Key Findings

### 1. Cycles dominate composite as predictor (Agent B)
| Metric | Pearson r | Spearman rho | R-squared |
|--------|-----------|--------------|-----------|
| Cycles | 0.856 | 0.917 | 73.2% |
| Composite | 0.816 | 0.858 | 66.6% |
| K_avg | 0.779 | 0.819 | 60.7% |
| N | 0.761 | 0.778 | 57.9% |

Cycle count alone is the best predictor. Composite dilutes the cycle signal.

### 2. Real-world validation (Agent A + Agent B)
- pydantic (composite=596, 123 cycles) → ground-up rewrite (V1→V2)
- aiohttp (composite=382, 69 cycles) → mid-transition, known maintenance pain
- pytest (composite=436, 62 cycles) → ~1000 open issues
- requests (composite=30, 0 cycles) → very stable, minimal burden
- black (composite=60, 0 cycles) → very stable, predictable

Outliers: rich (high composite but single talented author), werkzeug (moderate composite but high refactoring churn).

### 3. Hidden cycles are the sharpest diagnostic (Agent C)
- email: 0 static cycles but 2 runtime cycles (lazy imports masking debt)
- unittest: 0 static cycles but 1 runtime cycle
- Composite correctly orders html (1.0) < unittest (28.0) < email (46.0)

## Answers

**F65**: Composite can't predict deprecation (F55 already showed this). But it CAN
predict refactoring need (r=0.816), and cycles alone do it better (r=0.856).

**F79**: YES — the nk-analyze tool predicts maintenance burden. Cycles are the primary
signal (Spearman rho=0.917). Best used with hidden-cycle analysis for precision.

## Confounds
- Team size/quality (rich has 1 genius, pytest has strong team)
- Package purpose (frameworks inherently more coupled)
- n=11 is small — directional, not definitive
