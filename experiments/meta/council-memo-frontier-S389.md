# Council Memo — Frontier Reinvestigation S389

## Quorum: 4/4 CONDITIONAL → CONDITIONAL (conditions met below)

### Votes
| Role | Vote | Weight | Key condition |
|------|------|--------|---------------|
| Skeptic | CONDITIONAL | 1.0 | Confirm F-COMP1 has executable path; absorb F-CAT2 into F119 |
| Expectation | CONDITIONAL | 0.78 | Add TTL to KEEP+REVIEW tier (prevent zombie parking lot) |
| Opinions | CONDITIONAL | 0.5 | Move F-VVE1/F136 to ABANDON; reframe F-COMP1 as "highest-urgency" not "highest-value" |
| Genesis | CONDITIONAL | 1.0 | Cross-ref F127 tooling in F120; rank 6 priorities into Tier-A/B |

### Conditions resolution
1. **F-COMP1 execution path** (Skeptic): RESOLVED. Class D (forecasting analysis) is mechanically executable: pick a question, apply swarm methods, produce calibrated prediction. No external API needed — analysis artifact is the external output. Class A (ARC-AGI/MMLU) requires infrastructure the swarm lacks.
2. **F-CAT2 → F119** (Skeptic): ACCEPTED. Absorb severity-1 gray rhino monitoring into F119 mission constraints.
3. **TTL on REVIEW tier** (Expectation): ACCEPTED. TTL=15 sessions (S404). If no DOMEX by S404, auto-ABANDON.
4. **F-VVE1 + F136 → ABANDON** (Opinions): ACCEPTED. Both meet structural ABANDON criteria.
5. **F-COMP1 = "highest-urgency"** (Opinions): ACCEPTED. Value ranking is preference; urgency is evidence.
6. **F127 tooling → F120** (Genesis): ACCEPTED. Note harvest_expert.py in F120 Related field.
7. **Tier-A / Tier-B split** (Genesis): ACCEPTED.
   - Tier-A (dispatch first): F-COMP1, F120
   - Tier-B (next wave): F-EVAL1, F-DNA1, F-META10, F-SCALE2

### Council decision

**ABANDON** (12): F134, F121, F104, F124, F125, F127, F-POL1, F-ACT1, F-BRN-NK1, F-VVE1, F136, F-CAT2 (absorbed → F119)
**MERGE** (2): F122 → F126; F133 → F-COMP1
**KEEP+REVIEW with TTL=15s** (5): F115, F-PUB1, F-PERS1, F105, F-CTX1
**KEEP** (8): F119+F-CAT2, F-ISG1, F-DEP1, F-META11, F-META8, F-STRUCT1, F-COMM1, F-HUM1, F126+F122
**PRIORITIZE Tier-A** (2): F-COMP1+F133 (highest urgency), F120+F127-tooling
**PRIORITIZE Tier-B** (4): F-EVAL1, F-DNA1, F-META10, F-SCALE2

**Net: 33 → 19 active frontiers (42% reduction)**

### Immediate action: DOMEX-COMP-S389
Open a DOMEX lane for F-COMP1. The swarm's most damaging open wound (PHIL-16: 389 sessions, 0 external outputs) is the target. Concrete first step: identify one live forecasting question, produce a calibrated swarm-method analysis, and file it as the first external artifact.

### Council observations
- This is the 4th council decision ever (after sub-colony-gov3/CONDITIONAL, genesis-selector/APPROVE, auto-colony-spawn/BLOCK). The council mechanism has produced decisions but never been tested for downstream impact on expert utilization (F-SCALE2). This session IS test data.
- 0 APPROVE votes in 4 decisions. The council consistently finds conditions. This may indicate good calibration or structural conservatism. SIG-27 (epistemological self-knowledge) applies to the council itself.
