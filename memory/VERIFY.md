# Verification Heuristic v0.1

When should a session web-search vs trust its training data?

## The 3-S Rule: Search if Specific, Stale, or Stakes-high

### 1. SPECIFIC — Exact numbers, versions, API signatures
Training data conflates versions. If you need `library@version` behavior, search.
- Trust: General concepts, stable algorithms, design patterns
- Search: Default config values, API parameters, version-specific behavior

### 2. STALE — Facts that change over time
Training cutoff means anything time-sensitive may be wrong.
- Trust: Math, logic, well-established CS theory, stable conventions
- Search: Current maintainers, latest versions, recent CVEs, project status

### 3. STAKES — Getting it wrong would be costly
When the cost of error is high, verify even if you feel confident.
- Trust: Low-stakes decisions, internal refactoring, naming choices
- Search: Security claims, legal/compliance, production config, public-facing advice

## Quick decision flow
```
Is the claim specific (exact number/version/name)?  → SEARCH
Has the fact likely changed since training cutoff?   → SEARCH
Would being wrong here cause real damage?            → SEARCH
None of the above?                                   → TRUST (but note Assumed confidence)
```

## When you can't search
If web search isn't available, mark your output with `Confidence: Inherited` and note what would need verification. Future sessions can verify.

## Common traps
- **False confidence**: Training data contains wrong answers stated confidently. Frequency in training ≠ correctness.
- **Version conflation**: Knowing something about v2 doesn't mean it's true for v3.
- **Survivorship bias**: Popular answers on StackOverflow are in training data. Popular ≠ correct.
