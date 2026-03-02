# Experiment: Does Multi-Session Memory Improve Output Quality?

## Hypothesis
The swarm's persistent memory system produces measurably better results on multi-session tasks compared to a stateless agent with equivalent human-written briefing.

## Task
**Research and document the WebSocket protocol (RFC 6455) with a working reference implementation.**

Deliverables:
1. A technical analysis document covering: framing, masking, opcodes, close handshake, extensions, security considerations — all verified against RFC 6455 as primary source.
2. A minimal but correct WebSocket frame parser/serializer in Python (stdlib only).
3. At least 10 test cases validating the implementation against RFC-specified behavior.

Why this task:
- Requires 5+ sessions (RFC is ~70 pages, implementation + tests is non-trivial)
- Exceeds single context window (RFC + analysis + code + tests)
- Objectively measurable: tests pass or fail, claims can be checked against RFC section numbers
- Completely unrelated to the swarm itself

## Design
- **Branch A: `experiment/swarm`** — Full swarm protocol. Agent reads CLAUDE.md, follows all protocols, uses memory system.
- **Branch B: `experiment/stateless`** — No swarm. Agent gets a single `BRIEF.md` file at the start of each session, written/updated by the human (or acting-as-human agent) between sessions. No persistent memory, no beliefs, no lessons.
- **Sessions**: 5 per branch (10 total). Same time budget per session.
- **Order**: Alternate (swarm session 1, stateless session 1, swarm session 2, ...) to control for learning effects.

## Measurements (recorded after each session in this file)
- Task progress (% of goal completed, subjective 1-5)
- Errors repeated from previous sessions (count)
- Time spent on orientation/context-loading vs actual work (estimate %)
- Quality of output artifacts (evaluated after all sessions complete)

## Session Log

### Swarm Sessions
| Session | Progress (1-5) | Repeated Errors | Orientation % | Notes |
|---------|----------------|-----------------|---------------|-------|
| S1 | | | | |
| S2 | | | | |
| S3 | | | | |
| S4 | | | | |
| S5 | | | | |

### Stateless Sessions
| Session | Progress (1-5) | Repeated Errors | Orientation % | Notes |
|---------|----------------|-----------------|---------------|-------|
| S1 | | | | |
| S2 | | | | |
| S3 | | | | |
| S4 | | | | |
| S5 | | | | |

## Results

| Metric | Swarm (avg) | Stateless (avg) | Winner |
|--------|-------------|------------------|--------|
| Progress per session | | | |
| Repeated errors | | | |
| Orientation overhead | | | |
| Final output quality | | | |

## Conclusion
[FILL IN: Does the data support the hypothesis? What did we learn?]
