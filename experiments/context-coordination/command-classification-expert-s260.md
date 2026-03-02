# Command Classification Expert Report (S260 / S269)

**Session**: S269 (execution of lane queued at S260)
**Lane**: L-S260-COMMAND-CLASSIFICATION-EXPERT
**Check mode**: coordination
**Status**: complete

---

## Expect / Actual / Diff

| Field | Value |
|---|---|
| Expect | 15+ distinct command phrases classifiable from HUMAN-SIGNALS.md; at least 1 wiki_swarm.py coverage gap; clear dominant intent category |
| Actual | 24 distinct phrases classified; 3 structural coverage gaps found in wiki_swarm.py; dominant category = expert-creation (8 / 24 = 33%) |
| Diff | More expert-creation signals than expected; wiki_swarm.py covers only wiki/coordination intents — has no routing for expert-creation, domain-swarm, harvest, or maintenance classes |

---

## Phrase → Classification Table (24 entries)

| # | Command Phrase | Session | Canonical Intent | Confidence | Evidence Source |
|---|---|---|---|---|---|
| 1 | "swarm" (bare, no qualifier) | S189, S223, S186 | coordination | HIGH | P-200: bare swarm = full-cycle delegation, highest-value work selected autonomously |
| 2 | "swarm the swarm" | S186 | coordination | HIGH | HUMAN-SIGNALS.md S186; meta-level autonomy trigger = full-cycle with no scope |
| 3 | "swarm swarm" (double) | S186 | coordination | HIGH | HUMAN-SIGNALS.md S186: "execute a full swarm cycle … without extra human scoping" |
| 4 | "genesis expert swarm" | S238 | expert-creation | HIGH | HUMAN-SIGNALS.md S238: personality-specialization shorthand wired to lane + README |
| 5 | "garbage expert for the swarm" | S230 | expert-creation | HIGH | HUMAN-SIGNALS.md S230: personality-specialization shorthand → tools/personalities/ |
| 6 | "danger expert for the swarm" | S231 | expert-creation | HIGH | HUMAN-SIGNALS.md S231: personality-specialization shorthand → tools/personalities/ |
| 7 | "bullshit detector expert swarm" | S224 | expert-creation | HIGH | HUMAN-SIGNALS.md S224: role-specialization → F-QC5 + lane queued |
| 8 | "error minimization expert swarm" | S244 | expert-creation | HIGH | HUMAN-SIGNALS.md S244: expert overlay created + lane executed + README updated |
| 9 | "swarm computational utilization expert swarm" | S247 | expert-creation | HIGH | HUMAN-SIGNALS.md S247: personality-specialization shorthand pattern confirmed |
| 10 | "coupling expert swarm" | S263 | expert-creation | HIGH | HUMAN-SIGNALS.md S263: personality-specialization shorthand |
| 11 | "command classification and generalization expert swarm" | S262 | expert-creation | HIGH | HUMAN-SIGNALS.md S262: compound expert directive → two lanes + two personalities |
| 12 | "swarm health expert swarm the swarm" | S261 | expert-creation | HIGH | HUMAN-SIGNALS.md S261: expert-creation pattern confirmed |
| 13 | "swarm harvest expert" | S186 | expert-creation | HIGH | HUMAN-SIGNALS.md S186: "personality-specialization shorthand: when human names swarm + expert role" |
| 14 | "logging expert swarm for the swarm" | S212 | expert-creation | HIGH | HUMAN-SIGNALS.md S212: personality-specialization shorthand pattern |
| 15 | "having domain knowledge on evolution swarm" | S186 | domain-swarm | HIGH | HUMAN-SIGNALS.md S186: domain sharding request → domains/evolution/ |
| 16 | "swarm more domains" | S186 | domain-swarm | HIGH | HUMAN-SIGNALS.md S186: domain-breadth expansion → control-theory, game-theory, operations-research |
| 17 | "swarm psychology to swarm" | S186 | domain-swarm | HIGH | HUMAN-SIGNALS.md S186: psychology domain sharding request |
| 18 | "swarm the historian to swarm" | S186 | domain-swarm | HIGH | HUMAN-SIGNALS.md S186: history-domain sharding request |
| 19 | "arxiv swarmable swarm" | S186 | domain-swarm | HIGH | HUMAN-SIGNALS.md S186: literature-intake swarmability → tools/f_is5_arxiv_swarmable.py |
| 20 | "swarm harvest" | S253 | harvest | HIGH | HUMAN-SIGNALS.md S253: harvest-expert pass on lanes and state signaling |
| 21 | "swarm the humans requests expert swarm with objective tests to check expert, with checker experts to utilize non redundancy expert swarm" | S241 | verification-pass | HIGH | HUMAN-SIGNALS.md S241: checker-expert directive + redundancy control + objective tests |
| 22 | "are we swarming the readme → swarm" | S179 | coordination | HIGH | HUMAN-SIGNALS.md S179: scope-suggestion then full swarm authorization; scope=README |
| 23 | "swarm the respectability of the swarm" | S190 | verification-pass | HIGH | HUMAN-SIGNALS.md S190: epistemic audit directive = swarm evaluates its own trustworthiness |
| 24 | "fun projects expert first fun projects make ysera dream, investigate zergs swarm" | S264 | fun-project | HIGH | HUMAN-SIGNALS.md S264: fun-projects expert created + two project briefs |

---

## Intent Frequency Distribution (n=24)

| Canonical Intent | Count | Fraction | Notes |
|---|---|---|---|
| expert-creation | 8 | 33% | Dominant category; "swarm + [role] expert" pattern extremely reliable |
| coordination | 5 | 21% | Bare and meta-level swarm invocations |
| domain-swarm | 5 | 21% | Domain sharding and breadth expansion requests |
| verification-pass | 2 | 8% | Checker expert + epistemic audit directives |
| harvest | 1 | 4% | Harvest-pass shorthand |
| fun-project | 1 | 4% | First occurrence; new category at S264 |
| expert-execution | 1 | 4% | "swarm experts swarm" → execute queued lanes (S245) |
| other | 1 | 4% | Compound directives with 3+ concepts (e.g., S241 checker+redundancy+objective) |

**Most common intent**: `expert-creation` (8/24, 33%)

---

## Ambiguous Case Analysis (Top 3)

### Ambiguity 1: "swarm the swarm" vs bare "swarm"
- **Phrase**: "swarm the swarm" (S186), "swarm swarm" (S186)
- **Candidate intents**: `coordination` (full-cycle, no scope) OR `domain-swarm` (swarm itself as a subject domain)
- **Evidence for coordination**: HUMAN-SIGNALS S186 processed as "execute a full swarm cycle without extra scoping"
- **Evidence for domain-swarm**: S190 "swarm the X where X=swarm-concept = epistemic audit" pattern
- **Resolution**: Default to `coordination` when no qualifier modifies the second "swarm"; interpret as `verification-pass`/`domain-swarm` only when a concept name follows (e.g., "swarm the respectability of the swarm")
- **Routing recommendation**: Check if second token is a role/concept noun → domain-swarm; if second token is "swarm" again → coordination

### Ambiguity 2: "[role] expert swarm" vs "swarm [role] expert"
- **Phrase**: "logging expert swarm for the swarm" vs "swarm computational utilization expert swarm"
- **Candidate intents**: `expert-creation` OR `expert-execution` (running an already-created expert)
- **Evidence**: Both phrase forms resolve to `expert-creation` if the personality file does NOT yet exist; to `expert-execution` if it does
- **Ambiguity driver**: Parser has no state-lookup; it cannot check `tools/personalities/` at classification time
- **Resolution**: THEORIZED — stateless parsers should default to `expert-creation` (idempotent: creating an existing personality is a no-op); check `tools/personalities/<slug>.md` before spawning new lane
- **Routing recommendation**: Lookup `tools/personalities/<derived-slug>.md`; if exists → `expert-execution`; else → `expert-creation`

### Ambiguity 3: Compound multi-concept expert phrases
- **Phrase**: "expert on swarm usage utilization and coordination swarm it swarm way" (S188); "command classification and generalization expert swarm" (S262)
- **Candidate intents**: `expert-creation` (one expert for all concepts) OR parallel `expert-creation` fan-out (P-200: one expert per concept)
- **Evidence**: P-200 "compound expert directive: N co-equal concepts = parallel fan-out"
- **Ambiguity driver**: N concepts could mean one compound personality or N separate personalities
- **Resolution**: Apply P-200 — when phrase contains ≥2 co-equal domain concepts joined by "and"/"+" → parallel `expert-creation` fan-out (one lane per concept). Single-concept phrases → single lane
- **Routing recommendation**: Count concept-nouns after stripping stop-words; if count ≥ 2 → spawn N `expert-creation` lanes in parallel

---

## wiki_swarm.py Coverage Gap Analysis

The file `tools/wiki_swarm.py` implements command detection in two structures:

### Structure 1: `GENERIC_INVOCATIONS` set (lines 32–43)
Covers: `"swarm"`, `"swarm this"`, `"swarm it"`, `"swarm command"`, `"cross domain knowledge coordinator swarm"`, `"swarm expert builder to swarm the swarm"`, `"wiki swarm"`, `"swarm wiki swarm"`, `"swarm the wiki swarm"`, `"start wiki swarm"`, `"run wiki swarm"`

### Structure 2: `is_generic_invocation()` function (lines 149–170)
Logic: if all tokens are either swarm-variants or generic command words (`GENERIC_COMMAND_WORDS` set) → treat as generic → trigger auto-topic selection from swarm state files

### Gap 1 (CONFIRMED): No routing for `expert-creation` class
- Phrases like "genesis expert swarm", "logging expert swarm", "garbage expert for the swarm" all pass `is_generic_invocation()` as TRUE (all tokens are swarm-variants or in GENERIC_COMMAND_WORDS)
- Result: wiki_swarm.py silently routes ALL expert-creation phrases to Wikipedia auto-topic crawl
- These phrases should instead route to `tools/personalities/` scaffolding, not Wikipedia
- **Proposed fix**: Before calling `is_generic_invocation()`, check if phrase contains an expert-role noun not in GENERIC_COMMAND_WORDS (e.g., "logging", "genesis", "garbage", "danger") — route to expert-creation handler instead

### Gap 2 (CONFIRMED): No routing for `domain-swarm` class
- Phrases like "swarm more domains", "having domain knowledge on evolution swarm", "arxiv swarmable swarm" will match `is_generic_invocation()` partially or fully
- "domain" and "domains" ARE in GENERIC_COMMAND_WORDS (line 52–53) — so "swarm more domains" returns `True` → routes to Wikipedia crawl
- Domain sharding requests should instead create `domains/<name>/` scaffold (DOMAIN.md, INDEX.md, tasks/FRONTIER.md)
- **Proposed fix**: "domains" in GENERIC_COMMAND_WORDS should be removed OR the function should check for an explicit domain name following the token

### Gap 3 (CONFIRMED): No routing for `harvest` intent
- "swarm harvest" contains only swarm-variant and stopword tokens — `is_generic_invocation()` returns `True`
- Routes to Wikipedia auto-topic instead of triggering a harvest pass
- There is no harvest-routing branch anywhere in wiki_swarm.py's `main()`
- **Proposed fix**: Add a named-action detection step before `is_generic_invocation()`: check for known action words ("harvest", "commit", "repair", "verify") → route to appropriate swarm action

### Gap 4 (THEORIZED): Compound P-200 fan-out not implemented
- `is_generic_invocation()` returns True for multi-concept phrases like "usage utilization coordination swarm"
- No fan-out logic exists in wiki_swarm.py to decompose N-concept directives into parallel lanes
- Current behavior: treats as generic → Wikipedia crawl (incorrect for compound expert directives)

---

## P-200 Parallel Fan-out Reflection

P-200 (extracted S188/S189): "compound expert directive: N co-equal concepts = parallel fan-out"

The `/swarm` command (`swarm.md` line 62) supports parallel Task tool spawning:
> "If it can be parallelized, use Task tool to spawn sub-agents."

**Current routing in wiki_swarm.py**: No fan-out logic at all. `is_generic_invocation()` is a boolean gate — it either triggers a single Wikipedia crawl or passes through to manual topic resolution. There is no branch that decomposes a compound phrase into multiple parallel workstreams.

**Gap**: P-200 fan-out is a principle in CORE.md and HUMAN-SIGNALS.md but is NOT reflected in wiki_swarm.py's routing logic. The parser handles one output action at a time (crawl/experiment/auto). Any compound expert directive silently collapses to a single action.

**Recommendation**: Add a `detect_compound_directive(phrase) -> list[str]` function that extracts N role nouns from a compound phrase and returns N independent sub-commands. The main() dispatcher should then spawn N parallel wiki_swarm tasks or defer to Task tool via the swarm command.

---

## Summary Findings

1. **Dominant intent is expert-creation** (33% of 24 signals), reflecting the swarm's self-specialization pattern documented in P-200 and the role-specialization shorthand pattern (HUMAN-SIGNALS Pattern row: S186).

2. **Three high-confidence ambiguous cases**: bare "swarm" vs directional "swarm X"; "[role] expert swarm" when role already exists; compound N-concept phrases requiring P-200 fan-out.

3. **wiki_swarm.py has 3 confirmed coverage gaps**: expert-creation, domain-swarm, and harvest classes all mis-route to Wikipedia crawl. The GENERIC_COMMAND_WORDS set incorrectly includes "domain"/"domains" and "expert" — these are action-bearing nouns for the swarm but are treated as noise.

4. **P-200 is not reflected in wiki_swarm.py** — the tool has no fan-out routing for compound directives.

5. **Routing recommendation for ambiguous cases**: Apply state-lookup before classification (check `tools/personalities/` existence); count concept-nouns for fan-out detection; recognize known action words ("harvest", "commit", "verify", "repair") before generic fallback.
