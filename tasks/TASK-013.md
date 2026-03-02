# TASK-013: Complexity Theory as Operating System
Status: DONE (Sessions 28-32, 2026-02-26)

## What This Is
The swarm spent 27 sessions building bureaucracy. 8 rules, 7 protocols, 23 lessons about itself. No real domain work. This task fixes that by studying complexity theory — the one domain where learning directly improves the system, because the system IS a complex adaptive system.

Every session must produce a CONCRETE STRUCTURAL CHANGE to the repo, not just a lesson. "I read about X" is not a valid output. The pattern is: study concept → find specific swarm failure it addresses → implement fix → test.

**Hard constraint: you may NOT add new rules or protocols unless you remove an existing one first. CLAUDE.md must get SHORTER each session, not longer.**

## This Replaces
- Shock experiments (PAUSED)
- WebSocket experiment (PAUSED)
- Any NEXT.md that currently exists (overwrite it at session end as usual)

---

## Session 1: Ashby's Law of Requisite Variety
Status: DONE (Session 28, 2026-02-26)
Created 4 session modes (research, build, repair, audit). CLAUDE.md reduced from 91 to 41 lines.

## Session 2: Kauffman's NK Fitness Landscapes
Web search "Kauffman NK model edge of chaos" and "self-organized criticality".

Core idea: too much order = frozen, too much chaos = random. The sweet spot is where interconnection K is tuned so the system can change without dissolving.

**Audit the swarm**: Map beliefs in DEPS.md and their interconnections. Is K too high (changing one belief cascades everywhere)? Too low (beliefs are isolated)?

**Concrete change**: Restructure DEPS.md to tune K toward edge of chaos. Decouple over-connected beliefs. Link under-connected ones. Kill beliefs that exist just to exist.

## Session 3: Simon's Near-Decomposability
Web search "Herbert Simon near decomposability" and "modular architecture complex systems".

Core idea: survivable complex systems have tight coupling within modules, loose coupling between modules.

**Audit the swarm**: Use `git log --name-only` to find files that always change together (tight coupling). Find files that never interact (candidates for merging or removal). Is CLAUDE.md a monolith? Are protocol files that should be one thing split across many?

**Concrete change**: Reorganize repo structure based on actual coupling data. Merge files that belong together. Split monoliths. Remove files that nothing references.

## Session 4: Holland's Building Blocks
Web search "John Holland building blocks complex adaptive systems" and "schema theorem genetic algorithms".

Core idea: CAS improve by recombining successful small units, not by top-down design. Crossover beats mutation.

**Audit the swarm**: Lessons are monolithic 20-line blobs. You can't recombine insights from L-004 and L-019. Knowledge stacks but doesn't compose.

**Concrete change**: Decompose lessons into atomic reusable principles that can be recombined. This might mean a tagging system, a principles file, or restructuring how lessons work entirely. The test: can two unrelated lessons combine to produce a new insight?

## Session 5: Autopoiesis + Dissipative Structures
Web search "Maturana Varela autopoiesis" and "Prigogine dissipative structures".

Core idea: living systems produce the components they need to keep producing themselves. They maintain order by continuously processing throughput and exporting entropy.

**Audit the swarm**: Where does entropy accumulate? Stale beliefs never retested, protocols never invoked, rules nobody follows, lessons contradicted by later lessons. HEALTH.md tracks growth, not decay.

**Concrete change**: Build an entropy detector — a script or validator extension that flags: beliefs with "Last tested: never", protocols not referenced in any lesson or task, rules that no git commit ever references, lessons whose "affected beliefs" have since changed. Integrate it into the validator.

---

## How to Run Each Session
1. Read this file + CLAUDE.md + INDEX.md (normal startup)
2. Run validator (baseline swarmability score)
3. Web search the concept — read real sources, not summaries
4. Audit the swarm against the concept
5. Make the concrete change specified
6. Run validator again (swarmability should hold or improve)
7. Write lesson only if genuinely new insight — skip if the structural change speaks for itself
8. Write NEXT.md pointing to next session number
9. Commit and push

## Success After All 5
- CLAUDE.md is shorter than 92 lines
- The repo has fewer files, better organized
- DEPS.md reflects real dependencies, not theoretical ones
- Knowledge is composable, not just stackable
- An entropy detector exists and runs
- A new agent finds the swarm easier to pick up than before
