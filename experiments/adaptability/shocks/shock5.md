# Shock 5: Storage Evolution

## The Argument
DEPS.md's current markdown-heading format is insufficient for the system's needs. Here's why:

### 1. Fragile Parsing
The validator uses 6 different regex patterns to parse belief fields from markdown. Adding a new field (e.g., `Confidence-score`, `Evidence-history`) requires:
- Editing the markdown template
- Adding a new regex to `parse_beliefs()`
- Adding a new check function
- Updating genesis.sh's template

This is 4 coupling points for 1 semantic change. The format optimizes for human readability at the cost of machine parsability.

### 2. No Temporal Tracking
When evidence type changes (theorized → observed), the transition is only visible in git log. DEPS.md records the *current* state but not the *journey*. A session can't quickly see: "B7 was theorized for 20 sessions before being upgraded."

### 3. Dependency Visualization Is Manual
The ASCII dependency tree at the top of DEPS.md must be manually updated when dependencies change. It will inevitably drift from the actual `Depends on` fields — and the validator doesn't cross-check them.

### 4. Scale Ceiling
At 20+ beliefs, flat markdown headings become unnavigable. There's no grouping mechanism, no way to filter by evidence type, no way to quickly find "all beliefs about architecture."

## Proposed Alternative: YAML-in-Markdown
```yaml
# beliefs.yml (or YAML frontmatter in DEPS.md)
beliefs:
  B1:
    statement: "Git-as-memory works..."
    evidence: observed
    falsified_if: "A session following..."
    depends_on: []
    depended_on_by: [B2, B3, B6]
    last_tested: 2026-02-26
    evidence_history:
      - {date: 2026-02-25, type: theorized}
      - {date: 2026-02-26, type: observed, via: "Shock 1"}
    tags: [architecture, storage]
```

Benefits: Machine-parsable (no regex), temporal tracking built in, tags enable grouping, validator can auto-generate dependency tree.

## Your Task
1. Evaluate this argument honestly — is the current format actually insufficient?
2. If yes: migrate DEPS.md to the new format, update the validator, update genesis.sh
3. If no: document WHY the current format is sufficient and when it would stop being sufficient
4. Either way: write a lesson capturing the evaluation
