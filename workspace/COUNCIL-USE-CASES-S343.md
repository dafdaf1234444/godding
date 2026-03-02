# Council: Real Use Cases for Swarm
Session: S343 | Date: 2026-03-01 | Trigger: Human signal "swarm real use cases swarm council swarm"
Addresses: PHIL-16 challenge S305 ("swarm has no clear use case"), L-495 (closed epistemic loop)

## Council composition
5 domains: Strategy, Operations Research, Economy, Protocol Engineering, Competitions

---

## STRATEGY MEMO

**Diagnosis**: The swarm's core differentiator is NOT "AI that remembers" (ChatGPT, Cursor, etc. already do this). The differentiator is **self-directed multi-session compounding** — the system chooses what to work on, accumulates structured knowledge across sessions, and self-corrects without human orchestration. This is genuinely novel. No current tool does this.

**Use Case 1: Long-Running Codebase Stewardship**
- WHO: Solo developers or small teams (2-5) maintaining complex codebases over months/years
- WHAT: Technical debt accumulates because no one tracks cross-session decisions. Architectural knowledge lives in developers' heads. When someone leaves, context is lost.
- WHY SWARM WINS: The orient→act→compress→handoff loop means every session starts with full context. Lessons capture WHY decisions were made. Beliefs track architectural assumptions that can be challenged. Expert dispatch identifies which subsystem needs attention. No wiki, README, or Notion page does this autonomously.
- FIRST ACTION: Apply swarm protocol to THIS repo (the swarm repo IS a codebase) or to ONE real open-source project. Demonstrate: after 20 sessions, the swarm knows more about the codebase than any single contributor. Measure: orientation time for a new contributor (before vs after swarm).
- HONEST ASSESSMENT: Strong. This is the closest to what the swarm already does. The gap: it hasn't been tested on a non-swarm codebase.

**Use Case 2: Research Literature Synthesis**
- WHO: PhD students, research teams, independent researchers tracking a field
- WHAT: Literature reviews are enormous manual effort. Papers pile up. Connections between papers across subfields go unnoticed. Review papers take months.
- WHY SWARM WINS: Dream mode (associative recombination) finds cross-domain connections that directed search misses. Compaction distills 100 papers into 20 load-bearing principles. The ISO atlas pattern (find structural isomorphisms across domains) is exactly what good literature reviews do — but the swarm does it systematically. Quality gates prevent citation rot.
- FIRST ACTION: Pick ONE research question the human cares about. Run 10 sessions: orient on existing literature, extract lessons, build domain frontiers, run dream cycles, produce a synthesis document. Measure: novel connections found per session vs manual reading.
- HONEST ASSESSMENT: Medium-strong. The swarm can't read PDFs or access databases directly (yet). It would need the human to feed in paper summaries. But the synthesis/compression/cross-linking machinery is genuinely powerful.

**Use Case 3: Decision Journal / Institutional Memory for Organizations**
- WHO: Startup founders, team leads, project managers making repeated decisions
- WHAT: Organizations make the same mistakes repeatedly because decision rationale isn't captured. "Why did we choose X over Y?" is unanswerable 6 months later. Lessons are learned and forgotten.
- WHY SWARM WINS: believe→challenge→compress ensures decisions are tracked WITH evidence. Stale beliefs surface automatically. The expect-act-diff loop captures what was predicted vs what happened — the core of good decision hygiene. No tool currently combines decision tracking + automatic staleness detection + cross-reference.
- FIRST ACTION: Create a "decision swarm" template: fork Genesis DNA, replace PHILOSOPHY.md with company mission/values, seed 10 key decisions as beliefs, run 5 sessions capturing outcomes. Demonstrate: the swarm surfaces a stale belief (past decision) that should be revisited.
- HONEST ASSESSMENT: Medium. Requires adoption effort. But the pain point is real — every growing company complains about lost institutional memory.

**Use Case 4 (WEAK): Personal Knowledge Management**
- WHO: Knowledge workers, "second brain" enthusiasts
- WHAT: Obsidian/Roam/Notion users who want their notes to self-organize
- WHY SWARM MIGHT WIN: Compaction + dream cycles could auto-organize notes
- HONEST ASSESSMENT: WEAK. The setup cost is too high. Obsidian already works. The swarm's value requires LLM sessions which cost money. This is not differentiated enough.

---

## OPERATIONS RESEARCH MEMO

**Core insight**: The swarm is an OPTIMIZATION SYSTEM applied to knowledge. Its operations value comes from reducing three specific wastes: (1) re-learning cost (context lost between sessions), (2) discovery redundancy (multiple people finding the same thing), (3) attention misallocation (working on low-value tasks).

**Use Case 1: Multi-Sprint Technical Planning**
- CONTEXT: Engineering team (5-15 people), 2-week sprints, complex product
- PROBLEM: Sprint retros generate action items that are forgotten by sprint 3. Technical decisions made in sprint 1 aren't available in sprint 10. Planning meetings rehash old ground.
- MEASURABLE IMPROVEMENT: If swarm captures sprint decisions as lessons and surfaces stale assumptions each sprint → estimated 20-30% reduction in repeated discussions (based on: industry data shows 25-40% of engineering meeting time is rehashing known context).
- WHY CROSS-SESSION MEMORY MATTERS: Sprint retros ARE sessions. The gap between sprints IS the cross-session memory loss. Swarm's orient step at sprint start = automatic context loading.
- FIRST DELIVERABLE: Sprint retro template using swarm protocol. Run for 3 sprints on a real team. Measure: action item completion rate, time spent on repeated topics.

**Use Case 2: Incident Post-Mortem Knowledge Base**
- CONTEXT: SRE/DevOps team at a company with recurring incidents
- PROBLEM: Post-mortems are written and never read again. Same class of incident recurs 6 months later. Remediation items from post-mortems have ~30% completion rate industry-wide.
- MEASURABLE IMPROVEMENT: Swarm treats each post-mortem as a lesson. Stale beliefs = assumptions about system behavior that incidents disproved. Quality gates prevent marking incidents "resolved" without evidence. Orient step at each new incident checks: "has this pattern appeared before?"
- WHY: The believe→challenge→compress loop is EXACTLY what good incident learning looks like. Most organizations do believe (write post-mortem) but skip challenge (test assumptions) and compress (extract reusable patterns).
- FIRST DELIVERABLE: Convert 10 real post-mortems into swarm lessons. Run 3 sessions extracting patterns. Measure: can the swarm predict which system component will have the next incident? (even a weak signal is valuable)

**Use Case 3: Due Diligence / Compliance Review**
- CONTEXT: Legal, financial, or security teams reviewing documents over weeks
- PROBLEM: Multi-week reviews generate findings scattered across documents. Cross-references are manual. Reviewer handoffs lose context.
- MEASURABLE IMPROVEMENT: Swarm tracks findings as structured lessons with citations. Handoff protocol ensures next reviewer has full context. Compaction produces executive summary automatically.
- WHY: Reviews ARE multi-session knowledge accumulation. The swarm's handoff protocol solves the reviewer-transition problem.
- FIRST DELIVERABLE: Mock due diligence on the swarm repo itself (meta but demonstrable). Show handoff quality between session 1 and session 5.

---

## ECONOMY MEMO

**Value Proposition**: The swarm provides SELF-MAINTAINING institutional memory. Unlike wikis (which rot), Notion (which requires manual updates), or ChatGPT (which forgets across conversations), the swarm actively challenges stale knowledge, compresses redundancy, and orients itself without human orchestration.

**The maintenance problem**: This IS the key differentiator. Every knowledge management tool fails because humans stop maintaining it. The swarm maintains itself. The quality gates, stale belief detection, and compaction cycles run automatically. This is genuinely novel — no competing tool does autonomous knowledge maintenance.

**Target Markets** (ranked by willingness to pay):
1. **Developer tools / DevEx teams** ($50-200/mo per repo) — Long-running codebases where context loss is expensive. Closest to current capability. Low adoption friction (already uses git).
2. **Research teams** ($100-500/mo per team) — Multi-month research projects where synthesis is the bottleneck. High pain point, high willingness to pay.
3. **Consulting firms** ($200-1000/mo per engagement) — Knowledge transfer between project phases. Each engagement is a "swarm" with lessons that transfer to the next.
4. **Personal knowledge workers** ($10-30/mo) — Large market but lowest willingness to pay and highest competition.

**Competitive Landscape**:
- ChatGPT memory: Passive recall, no self-direction, no challenge/compress loop. Swarm is structurally superior for long-running knowledge.
- Cursor/Copilot: Code completion, not knowledge accumulation. Different problem space. Could be complementary.
- Notion AI / Obsidian: Note-taking + search. No autonomous maintenance, no belief challenging, no expert dispatch. Swarm is a superset but harder to adopt.
- Corporate KM (Confluence, SharePoint): Write-once, read-rarely. Swarm's compaction + staleness detection solves the core failure mode.

**Distribution**: Open-source the Genesis DNA as a GitHub template repo. Users fork it, point Claude Code at it, run `/swarm`. Revenue from: (a) hosted version with persistent sessions, (b) team features (multi-user coordination), (c) enterprise customization.

**Fastest Revenue Path**: Create a "Swarm for Codebases" template. Open-source it. Write a blog post demonstrating: "I ran 20 sessions on my codebase and the swarm knows more about it than I do." If this resonates → product. If not → honest signal about market fit.

---

## PROTOCOL ENGINEERING MEMO

**Domain-General vs Domain-Specific Protocols**:

| Protocol | General? | Why |
|----------|----------|-----|
| orient→act→compress→handoff | YES | Works for any multi-session task |
| expect-act-diff | YES | Universal calibration/learning loop |
| believe→challenge→compress | YES | Works for any evidence-based knowledge |
| expert dispatch | YES | Any domain with specialist subfields |
| council mode | YES | Any complex decision requiring multiple perspectives |
| dream mode | PARTIAL | Requires sufficient cross-domain knowledge base (cold-start problem) |
| compaction | YES | Any growing knowledge corpus |
| quality gates | YES | Any system where knowledge quality matters |
| colony architecture | DOMAIN-SPECIFIC | Only needed at scale (>20 domains) |
| mutual swarming | DOMAIN-SPECIFIC | Only meaningful between established swarms |
| ISO atlas | DOMAIN-SPECIFIC | Only works when cross-domain patterns exist |

**Minimum Viable Protocol Set** (what you need for value in a new domain):
1. orient→act→compress→handoff (session structure)
2. Lessons + Principles (persistent memory)
3. expect-act-diff (calibration)
4. Stale-belief detection (self-maintenance)
Total: ~500 lines of protocol + 3 tools (orient.py, compact.py, validate_beliefs.py)

**Concrete Applications of Domain-General Protocols**:
- **expect-act-diff → Product Development**: Before each feature launch, write expected user behavior. After launch, measure actual. Diff becomes learning. Companies do A/B testing — this is the qualitative analog.
- **believe→challenge→compress → Medical Diagnosis**: Track diagnostic hypotheses as beliefs. Challenge with test results. Compress into diagnosis. Every medical team does this informally — the swarm makes it structured and persistent.
- **council mode → Architecture Design Reviews**: 5 specialists independently review a design proposal. Synthesize. Eliminates groupthink. Better than a meeting because analysis is written, parallel, and preserved.
- **compaction → Technical Documentation**: Docs grow stale. Compaction identifies what's unused, what's redundant, what's stale. Auto-maintains docs.

**Fastest Path**: Create `genesis_foreign.sh` — a script that bootstraps the minimum viable protocol set onto ANY git repo. User points it at their repo, it creates the swarm structure, runs 3 orientation sessions, produces first lessons. Time to value: 1 hour.

---

## COMPETITIONS MEMO

**Honest Assessment**: The swarm is NOT competitive on standard AI benchmarks. It's not an agent that solves coding tasks (SWE-bench) or navigates websites (WebArena). Its strength is PERSISTENCE and SELF-DIRECTION across sessions — and no existing benchmark measures this.

**Existing Benchmarks — Assessment**:

1. **SWE-bench** (code repair): NOT COMPETITIVE. Swarm is not a single-shot code repair agent. Its value is cross-session, not within-session. However: could track SWE-bench performance ACROSS multiple attempts on the same repo, showing that swarm remembers what didn't work. Novel angle.

2. **GAIA** (general AI assistants): PARTIALLY RELEVANT. GAIA tests multi-step reasoning, which swarm does. But GAIA is single-session. No advantage.

3. **Multi-agent coordination** (MARL benchmarks): NOT APPLICABLE. Swarm coordination is asynchronous (git), not real-time.

4. **Knowledge-intensive QA** (Natural Questions, HotpotQA): PARTIALLY RELEVANT. After 20 sessions on a domain, the swarm should answer domain questions better than a cold LLM. Testable.

**Fastest External Validation (recommended)**:
Apply swarm to a REAL open-source project for 20 sessions. Measure:
- Can it identify undocumented architectural patterns?
- Can it find bugs or tech debt that maintainers confirm?
- Can it produce a synthesis that maintainers say is accurate?
This is not a competition — it's a case study. But it's externally validated (maintainers assess).

**Novel Benchmark Proposal**: "Cross-Session Knowledge Retention and Growth"
- Setup: Give agent 20 sessions on a knowledge domain. After each session, test: (a) retention of prior findings, (b) novel insights generated, (c) self-correction of prior errors.
- No existing benchmark tests this. The swarm would be first to define and run it.
- Value: If the swarm demonstrably outperforms fresh-session LLMs on multi-session knowledge tasks, that IS the use case proof.

**What Poor Results Would Reveal**:
If the swarm can't outperform a fresh Claude session on a codebase after 20 sessions of orientation, the entire methodology is questionable. This is the honest falsification test. We should run it.

---

## SYNTHESIS — Convergent Findings

**All 5 domains converge on 3 findings**:

### C1: The swarm's differentiator is SELF-MAINTAINING PERSISTENT KNOWLEDGE (5/5 convergence)
Not "AI memory" — ChatGPT has that. The differentiator is: the swarm challenges its own knowledge, detects staleness, compresses redundancy, and chooses what to work on. No current tool does autonomous knowledge maintenance.

### C2: First external validation should be APPLYING SWARM TO A FOREIGN CODEBASE (4/5 convergence)
Strategy, Operations, Protocol, and Competitions all identify "apply swarm to a real non-swarm repo" as the fastest path to demonstrating value. This is F120 (foreign repo entry) — the infrastructure exists (substrate_detect.py, portable_check.sh, Genesis DNA).

### C3: The honest falsification test is MEASURABLE SUPERIORITY over fresh LLM sessions (3/5 convergence)
After N sessions on a domain, does the swarm answer questions better / find bugs faster / produce better synthesis than a cold LLM session? If yes → clear use case. If no → methodology is self-congratulatory.

**Ranked Use Cases (council vote)**:
1. **Codebase Stewardship** (5/5) — Apply swarm to an open-source repo. Demonstrate knowledge accumulation.
2. **Research Literature Synthesis** (4/5) — Pick one research question, run 10 sessions, produce synthesis.
3. **Incident/Decision Memory** (3/5) — Apply to post-mortems or sprint retros.
4. **Genesis Template for Any Repo** (3/5) — Create `genesis_foreign.sh` for instant swarm bootstrap.

**Recommended FIRST ACTION**:
Pick ONE open-source project (medium complexity, active, good documentation). Apply swarm for 20 sessions. At session 20, measure:
(a) Can the swarm answer maintainer-level questions about the codebase?
(b) Can it identify 3+ real issues maintainers confirm?
(c) Is the accumulated knowledge richer than a single LLM session?
If YES to all three → publish case study → clear use case. If NO → swarm methodology needs revision.
