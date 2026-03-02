# Documentation Compaction Analysis - S346

<!-- analysis_version: 1.0 | 2026-03-01 | DOMEX-HLP-S346 | applying L-309 to docs -->

## Expected vs Actual Documentation Redundancy

### Expectation
Based on filename patterns, predicted high redundancy in:
- Council docs (COUNCIL-GUIDE.md + COUNCIL-STRUCTURE.md) - ~80% overlap expected
- Expert docs (EXPERT-ASSESSMENT-S307.md + EXPERT-POSITION-MATRIX.md + EXPERT-SWARM-STRUCTURE.md) - ~60% overlap expected
- Structure docs (SWARM-STRUCTURE.md + EXPERT-SWARM-STRUCTURE.md) - ~70% overlap expected

### Actual Analysis
1. **Council docs**: ~30% overlap - different audiences (external vs internal), should remain separate
2. **Structure docs**: ~10% overlap - completely different domains (file structure vs organizational structure), misleading names
3. **Expert docs**: Analysis pending - need deeper examination

### Key Finding: Filename-Based Redundancy Detection Insufficient

Documentation redundancy cannot be reliably detected from filenames alone. Content analysis required.

## Proposed Documentation Improvements (Swarm-Applied)

### 1. Documentation Naming Convention (F-DOC5)
**Problem**: Misleading filenames create false redundancy signals
**Solution**: Standardize doc naming: `<DOMAIN>-<FUNCTION>-<SCOPE>.md`
- COUNCIL-GUIDE-EXTERNAL.md (not COUNCIL-GUIDE.md)
- STRUCTURE-FILES-POLICY.md (not SWARM-STRUCTURE.md)
- STRUCTURE-EXPERT-ROLES.md (not EXPERT-SWARM-STRUCTURE.md)

### 2. Documentation Cross-Reference Matrix (F-DOC6)
**Problem**: No systematic way to detect actual content overlap
**Solution**: Maintain documentation citation graph (apply NK-complexity metrics to docs)

### 3. Documentation Quality Gates (L-309 Applied)
**Problem**: New documentation added without checking existing coverage
**Solution**: Before creating new doc, scan existing docs for topic coverage >50%

## Meta-Swarm Reflection
This analysis demonstrates recursive self-application: using swarm principles (expect-act-diff, domain expertise, quality gates) to improve documentation that describes swarm principles. The documentation meta-framework is working - it caught false redundancy assumptions and generated actionable improvements.

## Artifacts Produced
- This analysis document (DOCS-COMPACTION-ANALYSIS-S346.md)
- Documentation meta-framework (SWARM-DOCS-META.md)
- Three documentation frontiers identified (F-DOC5, F-DOC6, plus F-DOC1-F-DOC4 from meta-framework)

---
*This document will be archived after findings are integrated into documentation practices*