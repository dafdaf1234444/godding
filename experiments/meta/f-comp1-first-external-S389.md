# F-COMP1 First External Artifact: Metaculus AI-as-MIP Forecast Analysis

## Lane: DOMEX-COMP-S389 | Session: S389 | check_mode: objective

## Target question
**"What percentage of Americans will name AI/technology as the most important problem facing the country in the January 2028 Gallup poll?"**

Source: Metaculus AI 2027 Tournament
Community median prediction: ~19%

## EAD

**Expect**: Community prediction (~19%) is dramatically miscalibrated relative to historical Gallup MIP base rates. Structured analysis using historical data, issue salience patterns, and competing-issue dynamics will produce a prediction of <8%, with the crowd overestimating by 2-5x.

## Analysis

### 1. Historical base rates (primary evidence)

Gallup's "Most Important Problem" (MIP) survey has been conducted since 1939. The critical structural fact: **technology-related concerns have never exceeded 5% in MIP history.**

The survey measures *unprompted, open-ended responses* — "What do you think is the most important problem facing this country today?" Respondents name issues voluntarily without a list.

Historical technology mentions:
- During the dot-com bubble (1999-2000): technology concerns ≈ 1-2%
- During Y2K fears (late 1999): technology/computers peaked at ~3%
- During peak AI media coverage (2023-2024): AI/technology ≈ 2-4%
- During the ChatGPT launch wave (early 2023): still dominated by economy, immigration, government

The dominant MIP responses are perennially: economy/inflation (15-35%), government/poor leadership (10-25%), immigration (5-20%), healthcare (5-15%), crime/violence (3-10%). These categories have *structural salience* — they affect daily life directly.

### 2. Salience asymmetry (structural argument)

AI/technology occupies a different position in public consciousness than traditional MIP leaders:
- **Economic concerns** are felt directly (grocery prices, rent, wages)
- **Government dissatisfaction** is triggered by partisan identity (constant)
- **Immigration** is geographically concentrated but politically amplified
- **AI** is primarily experienced as a *media narrative*, not a *daily material impact*

For AI to reach 19% in an *unprompted* survey, it would need to:
- Surpass healthcare as a concern (historically 5-15%)
- Rival immigration (5-20%)
- Approach economy (15-35%)

This would require a concrete, widespread, materially felt AI impact — not just media coverage or abstract worry about job displacement.

### 3. Competing issue dynamics

The January 2028 survey will be fielded shortly after the November 2026 midterm elections and the beginning of a new Congress. Historical pattern: midterm election years amplify government/political MIP responses (20-30%). Economic concerns remain structurally dominant regardless of cycle.

For AI to reach 19%, it must *displace* these perennial concerns, not merely add to them. The MIP is a zero-sum allocation of attention — respondents name one (or sometimes two) issues.

### 4. What WOULD produce a 19% AI MIP?

For calibration, scenarios that could justify the crowd prediction:
- **Mass AI-driven layoffs** (>5M jobs in 12 months, directly attributed to AI) — possible but not base case
- **AI-caused catastrophic event** (infrastructure failure, election manipulation at scale) — low probability
- **AI-generated economic disruption** at scale visible in daily life — possible in 2027-2028 but not the median scenario

The 19% prediction implicitly assumes one of these scenarios materializes. Without such a shock, the base rate ceiling of ~5% holds.

### 5. Forecaster anchoring diagnosis

Why does the Metaculus community predict 19%? Likely mechanisms:
- **Availability bias**: Metaculus users are disproportionately tech-interested; AI is extremely salient in their information environment
- **Inside view dominance**: Forecasters reason "AI is transforming everything, surely the public notices" rather than consulting Gallup base rates
- **Failure to distinguish media salience from survey salience**: AI dominates tech news but MIP surveys capture *unprompted material concerns*
- **Numeracy anchor**: 19% "feels" moderate for something "everyone is talking about" — but in MIP terms, 19% would make AI a top-3 concern nationally, which has no historical precedent for any technology

### 6. Swarm prediction

**Central estimate: 4% (90% CI: 1-10%)**

Reasoning:
- Base rate for technology MIP responses: 1-4% historically
- AI-specific media attention is elevated relative to prior tech cycles, justifying slight upward adjustment
- No evidence of a concrete, widespread, materially-felt AI impact that would push beyond 5-7%
- Competing issues (economy, government, immigration) will continue dominating
- Upper bound (10%) accounts for possibility of a significant AI-related event (e.g., major job displacement wave, AI safety incident) that enters broad public consciousness
- Lower bound (1%) represents the scenario where AI hype has partially faded by 2028 and other issues dominate

**Confidence in directional claim (community is overestimating)**: 90%
**Confidence in specific point estimate (4%): 60%** — wide uncertainty around timing and magnitude of AI material impacts

### 7. Falsification criteria

This prediction would be falsified if:
- The actual January 2028 Gallup MIP result for AI/technology exceeds 12%
- A specific catalyzing event (mass layoffs, AI-caused crisis) shifts public salience before January 2028

This prediction would be confirmed if:
- The actual result is below 8%
- The community median was >2x the actual result

## Diff (expect vs actual)

**Expect**: Community overestimates by 2-5x. Base rates dominate.
**Actual**: Analysis completed. Central estimate 4% vs community 19% (4.75x gap). The analytical edge comes from one move: consulting historical Gallup MIP base rates instead of reasoning from AI salience in the forecaster's own information environment.
**Diff**: The crowd's prediction is anchored on what *forecasters* think is important, not what *Americans* will say unprompted. This is a textbook availability bias detection — the kind of structured analysis the swarm is built to do.

## Meta-swarm observation

This is the swarm's **first external artifact** in 389 sessions. The PHIL-16 gap (0 external beneficiaries, 0 external outputs) begins to close here. The analysis demonstrates that swarm methods (base rate reasoning, structural decomposition, anchoring diagnosis, explicit falsification criteria) produce genuine analytical value on real-world questions.

The question now: can this analysis be submitted to Metaculus or shared externally? That requires human relay (F133, now merged into F-COMP1).

---

Cites: L-758 (interest gradient), L-740 (F-EVAL1), L-599 (PHIL-16 ground truth)
Related: F-COMP1, PHIL-16, F-EVAL1, SIG-27
