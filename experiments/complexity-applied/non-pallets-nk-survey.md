# Non-Pallets NK Survey (F74)
Date: 2026-02-26 | Session: 41

## Question
Can a project escape "tangled" classification? 0/3 Pallets recovered.

## Method
Analyzed 8 additional popular Python packages via NK analysis.

## Results

| Package | N | K_avg | Cycles | Composite | Classification |
|---------|---|-------|--------|-----------|---------------|
| requests | 21 | 1.43 | 0 | 30.0 | distributed |
| **black** | 25 | 2.40 | **0** | 60.0 | framework |
| click | 14 | 3.43 | 5 | 53.0 | tangled |
| httpx | 23 | 3.78 | 11 | 98.0 | tangled |
| flask | 24 | 2.67 | 34 | 98.0 | tangled |
| fastapi | 47 | 2.51 | 7 | 125.0 | tangled |
| werkzeug | 52 | 4.00 | 43 | 251.0 | tangled |
| aiohttp | 55 | 5.69 | 69 | 382.0 | tangled |
| _pytest | 71 | 5.27 | 62 | 436.0 | tangled |
| rich | 78 | 4.94 | 81 | 466.0 | tangled |
| pydantic | 105 | 4.50 | 123 | 596.0 | tangled |

## Key Findings

1. **No escape observed**: 0/9 tangled packages escaped. Tangled remains absorbing.
2. **Two zero-cycle packages**: requests and black — both maintain DAG discipline over years.
3. **Black trajectory**: 21.7b0→26.1.0, zero cycles throughout, K_avg actually decreased.
4. **Size doesn't predict tangles**: httpx (N=23, 11 cycles) vs black (N=25, 0 cycles).
5. **Framework design correlates with cycles**: web frameworks (flask, fastapi, aiohttp) all tangled.
   Libraries/tools (requests, black) can stay clean.
6. **"Good API" ≠ clean internals**: pydantic and rich have great APIs but deeply tangled guts.

## Answer to F74
**NO** — no project has escaped tangled. But the distinction is preventive, not curative:
some projects (requests, black) never enter tangled by maintaining DAG discipline from day one.
The ratchet cannot be reversed; it can only be avoided.
