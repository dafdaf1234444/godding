# NK as Technical Debt Detector (F81)
Date: 2026-02-26 | Session: 41

## Method
Two-phase spawn (P-059):
- Phase 1: 3 parallel agents (pydantic timeline, aiohttp hotspot validation, black vs httpx comparison)
- Phase 2: 1 sequential agent drilling into why rewrites don't escape the ratchet

## Phase 1 Findings

### Agent A: Pydantic V1→V2
V1 (30 cycles, composite=187) → V2 (91 cycles, composite=562). Rewrite TRIPLED cycles.
New V2 code independently re-created 61 cycles. Compatibility shim adds ~30 more.
NK would have flagged V1 as "tangled" before the rewrite decision.

### Agent B: aiohttp hotspot validation
NK's cycle participation correctly identified 5/6 areas that v4.0 had to surgically refactor:
client_reqrep, web_request/response, web_exceptions, web_app.
`typedefs` (69 LOC, 72% cycle participation) is a "cycle amplifier" — invisible to LOC metrics.

### Agent C: black vs httpx
NK correctly predicted: black (burden=2.5, 0 cycles) is stable; httpx (burden=13.3, 11 cycles)
has breaking changes affecting LangChain, OpenAI SDK, Ollama. 5x burden ratio matches reality.

## Phase 2: The API is the Ratchet
The strongest explanation for why rewrites don't escape: the API's information-flow graph
encodes the cycle topology. API-compatible rewrites must reproduce the same circular references.
requests (0 cycles) isn't simpler domain-wise — it has a different API shape (pipeline vs recursive).
The only escape is API redesign (reimagination), not code rewrite.

## Answer to F81
YES — NK analysis can detect hidden technical debt before bugs manifest.
Evidence: aiohttp's cycle hotspots predicted 5/6 v4.0 refactoring targets.
pydantic's V1 "tangled" classification predicted rewrite pressure.
Deeper finding: the API itself encodes the cycle topology (L-058, P-064).
