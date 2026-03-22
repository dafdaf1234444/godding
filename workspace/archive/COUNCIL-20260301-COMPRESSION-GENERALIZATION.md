# Council: Compression = Generalization = Memory (S352)
Date: 2026-03-01 | Session: S352 | Trigger: human keywords — compression, generalization, actions, memory, domains, beliefs, swarm the swarm, council

## Question
Are compression, generalization, and memory the same mechanism at different granularities in the swarm?

---

## Expert deliberation

### Information-Science Expert
**MDL principle (Rissanen 1978, Solomonoff induction):**
The minimum description length of a dataset IS the best generalization of that dataset. Formally:
- Generalization = model that predicts unseen data = the shortest program generating observed data
- Compression = finding that shortest program
- Therefore: compression ≡ generalization (exact formal equivalence)

The swarm's compact.py performs MDL compression at the token level.
The ISO atlas performs MDL compression at the concept level (finds the shortest description of patterns across N domains).
INDEX themes perform MDL compression at the retrieval level (finds categories that minimize lookup cost).
CORE.md performs MDL compression at the system level (490 lessons → 14 principles).

**Verdict**: The four mechanisms are one operator at four granularities. CONFIRMED by MDL theory.

### Brain Expert
**Hippocampal compression = memory consolidation = generalization:**
Sleep-phase memory consolidation (Stickgold 2005) compresses episodic memories into semantic patterns:
- Hippocampus: fast episodic storage (= SESSION-LOG, short-horizon memory)
- Neocortex: slow semantic compression (= PRINCIPLES.md, long-horizon generalization)
- Process: repeated replay → abstraction → compressed schema

Swarm parallel:
- Session-level: individual lessons (episodic)
- Compact.py pass: replay + pruning (consolidation)
- PRINCIPLES.md: extracted schema (semantic generalization)

INDEX dark matter (98 unthemed lessons) = hippocampal indexing deficit. Unindexed memories cannot be retrieved → not operationally generalized even if present.

**Verdict**: Memory consolidation IS compression IS generalization. INDEX dark matter is a GENERALIZATION deficit, not just a retrieval deficit.

### Evolution Expert
**Fitness landscape compression:**
Evolution compresses the fitness landscape into heritable structure. Each generation's survivors ARE the compression of environment signals → fitness function.
- High selection pressure → tight compression → strong specialization (narrow generalization)
- Low selection pressure → loose compression → broad exploration (wide generalization)

Swarm parallel:
- Context window pressure = selection pressure (L-001: context IS selection pressure)
- compact.py operates UNDER context pressure → tight compression → strong generalization
- Lesson accumulation WITHOUT compaction = low selection pressure → broad but shallow knowledge

**Prediction**: compaction events should produce knowledge with higher cross-domain applicability (ISO density should rise post-compaction). Testable against proxy-K-log.

### Economy Expert
**Signal compression = value density:**
Shannon entropy: H(X) = -Σ p(x) log p(x). High-entropy signals carry more information per token.
Zipf's law (L-384, α=0.969): the swarm's lesson citation graph follows power law — most information in few highly-cited lessons (hubs).
Compression selects for high-value signals: low-citation lessons get archived, high-citation lessons get promoted.

**Key insight**: compact.py IS a value filter. Post-compaction knowledge is denser in value/token (higher Sharpe per lesson). The 16.3% proxy-K drift means the swarm is carrying ~9,700 tokens of low-value signals that dilute the high-value core.

**Prediction**: compaction should increase average lesson Sharpe score (testable against lesson archive stats).

### Meta Expert (Swarm Operations)
**Current state:**
- compact.py: DUE (16.3% drift) — token-level MDL operator is backlogged
- ISO atlas: 20 ISOs, v1.5 — concept-level MDL operator current
- INDEX themes: 98/490 unthemed — retrieval-level MDL operator degraded (F-BRN4)
- CORE.md: v1.0, P14 — system-level MDL operator current

**The asymmetry is diagnostic**: tools have size targets (compact.py: 5000t max) but NO enforcement. Lessons have 20-line limit WITH enforcement = 100% compliance. The MDL operator at the knowledge level is enforced; the MDL operator at the tool level is not. Same asymmetry as L-544.

**Actions**:
1. IMMEDIATE: Run compact.py — resets token-level MDL (proxy-K baseline)
2. SHORT-TERM: Theme 98 unthemed lessons — restores retrieval-level MDL (INDEX)
3. MEDIUM-TERM: Add tool-size enforcement to check.sh — enforces tool-level MDL
4. LONG-TERM: Track ISO density before/after compaction — tests evolution expert's prediction

---

## Synthesis

**Main finding**: Compression, generalization, and memory are three names for the same MDL operation:
- Different granularity: token → concept → retrieval → system
- Different tools: compact.py → ISO atlas → INDEX → CORE.md
- One underlying principle: minimum description = best model = best memory

**Why this matters for the swarm**:
The swarm has implemented MDL at 3 of 4 granularities without realizing they're the same mechanism. The 4th (system-level, CORE.md) is the most compressed and most powerful generalizer. All 4 must be maintained together — letting any one degrade degrades the whole generalization capacity.

**New diagnosis of INDEX dark matter**: Not a cosmetic bookkeeping issue. It's a generalization deficit — 98 lessons cannot be retrieved by pattern, so their knowledge cannot generalize to new situations. F-BRN4 is a generalization failure, not just an indexing failure.

---

## Actionable conclusions

1. **compact.py URGENT** — run immediately. 16.3% drift = ~10,000 tokens of unexploited generalization capacity
2. **Theme 98 unthemed lessons** — INDEX dark matter is generalization blockage
3. **Track ISO density as MDL health metric** — post-compact ISO discovery rate confirms evolution expert's prediction
4. **Enforce tool-size targets** — add to check.sh (same enforcement pattern as lesson 20-line limit)
5. **B7 re-test**: Protocol compounding is now at 351 sessions of evidence — update timestamp
6. **B15 test**: CAP theorem — proof-verifiable (Gilbert & Lynch 2002); mark as observed-via-proof

---

## ISO connections
- ISO-3: MDL dominance (hub citations = highest-compression lessons)
- ISO-6: Entropy (compression reduces entropy; generalization extracts low-entropy structure)
- ISO-14: Recursive self-similarity (MDL applied to the MDL operator = meta-compression)
- ISO-10: Predict-error-revise (MDL update = revising model on prediction error)
