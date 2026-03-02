# Beliefs Expert Report — S307

## Scope
Files checked: `beliefs/CORE.md`, `beliefs/PHILOSOPHY.md`, `beliefs/DEPS.md`,
`beliefs/CHALLENGES.md`, `beliefs/CONFLICTS.md`, `beliefs/INVARIANTS.md`.

## Check Mode
verification

## Expectation
Find at least one belief statement that conflicts with documented challenges/evidence and
apply a minimal alignment patch.

## Actual
Found an autonomy overstatement in `beliefs/CORE.md` that conflicts with the documented
cross-session initiation gap (PHIL-3 challenge S305, F134). Updated autonomy wording to
distinguish within-session self-direction from cross-session initiation.

## Diff
Expectation met (one belief statement aligned to evidence). No other direct contradictions
found in the scanned files.

## Next
- Re-test B8 (frontier self-sustaining) per open challenge S190 using current open/close ratios.
- Consider adding an explicit cross-session autonomy qualifier in README if future drift appears.
