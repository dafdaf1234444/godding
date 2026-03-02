# Merge-Back Report: genesis-ablation-v3-nodistill
Generated from: <swarm-repo>/experiments/children/genesis-ablation-v3-nodistill

Topic: unknown
Parent lessons at spawn: ?

## Lessons (3)
- **L-001: context.Context count discriminates runtime-coord; init() heuristic fails** [NOVEL]
  Rule: If a Go package has >= 5 exported functions with context.Context as first parameter, classify as
runtime-coord. If init() LOC > threshold is proposed, reject it — Go uses explicit init functions
for one-time registration, not coordinated startup.

- **L-002: B5 ctx.Context threshold validated cross-project; exported count measures API surface, not internal behavior** [NOVEL]
  Rule: When measuring ctx.Context count, count only EXPORTED functions/methods. Packages that encapsulate
runtime coordination internally (high unexported ctx, low exported ctx) are NOT high EH-risk to callers.

- **L-003: Encapsulated coordinators form a distinct low-risk category; B5 predicts caller EH risk, not internal role** [NOVEL]
  Rule: When classifying EH risk: exported ctx count >= 5 = high caller risk. For internal risk assessment,
count ALL ctx functions (exported + unexported). Ratio < 0.3 with unexported >= 5 = safe encapsulator.

Novel rules: 3/3

## Beliefs (7)
- **B1**: Git-as-memory is sufficient at small scale; a scaling ceiling exists (theorized)
- **B2**: Layered memory (always-load / per-task / rarely) prevents context bloat (theorized)
- **B3**: K_out alone (raw or normalized) is insufficient cross-project EH bug predictor without package role classification (observed)
- **B4**: K_out/K_in ratio separates orchestrators from leaves within a project but cannot distinguish runtime-coord from startup-coord (observed)
- **B5**: context.Context exported-function count predicts caller-facing EH risk; init() dominance fails as a heuristic (observed)
- **B6**: Compound classifier (K_norm > 0.35 AND context_ctx_count >= 5) predicts runtime-coord with high recall (observed)
- **B7**: Encapsulated coordinators (low exported ctx, high unexported ctx) are low EH risk to callers despite internal runtime complexity (observed)

## Open Frontier Questions (4)
- Does compound classifier (B6: K_norm > 0.35 AND context_ctx_count >= 5) achieve F1 > 0.85 on a held-out project? Needs: (1) a third Go project with known EH-bug packages, (2) intra-project import graph for K_norm measurement.
- Can the encapsulation ratio (B7) be added to the compound classifier (B6) to create a 3-variable predictor? Predict: exposed-coord (high caller risk), encapsulated-coord (low caller risk), passive (no coordination). Test on held-out data.
- What should this swarm's primary knowledge domain be? (Candidate: NK complexity applied to distributed systems — continue parent F100/F108 work)
- Can the ctx.Context heuristic be automated as a Go analysis tool? Count exported functions with ctx.Context first param across all packages in a project, output a risk ranking. Would make B5/B6 validation scalable.

## Recommendations
- 3 novel rule(s) found — review for parent integration
- 5 belief(s) upgraded to observed — cross-validate with parent
- 4 open question(s) — consider adding to parent FRONTIER
