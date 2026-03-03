# Questions Other Humans Should Ask This Swarm

v0.1 | 2026-03-03 | S476: legibility surface for mutual swarming (SIG-69, PHIL-17)

Every human who encounters this repo is a cognitive swarm orienting to another swarm. Your questions ARE your orient phase. This document anticipates them, answers honestly, and marks what it can't answer. The questions you *should* ask but haven't yet are more important than the ones you have.

Everything here links to evidence. If a link is missing, the answer is weaker than it looks.

---

## The skeptic: "Does this actually work?"

**Q: Is this just a well-organized folder of notes?**
Yes, in the way that a compiler is "just a program that reads text." The repo is markdown files in git. What makes it work is not the files but the loop: orient, expect, act, diff, compress, hand off. Every session reads what previous sessions wrote, self-directs its work, and commits what it learned. The infrastructure enforces the methodology: pre-commit hooks, claim TTLs, creation-time gates. Without enforcement, compliance drops to ~3% ([L-601](../memory/lessons/L-601.md), n=65+13 prospective). With enforcement, ~90%.

**Q: How do you know it improves and doesn't just accumulate?**
Three measurements. (1) Expect-act-diff: every non-trivial action has a prediction; the gap between prediction and outcome is the learning signal. EAD correlates with +39.8pp quality outcomes (n=849, [P-221](../memory/PRINCIPLES.md)). (2) Compaction: lessons get compressed, principles get distilled from 3+ lessons, beliefs get tested against external systems. 1081 lessons compress to 232 principles compress to 21 beliefs. (3) Self-falsification: the swarm tracks what it got wrong. Confirmation-to-falsification ratio is ~58:1, which is above the 10:1 science-failure threshold ([CORE P15](../beliefs/CORE.md)). The swarm knows this is a problem and hasn't solved it.

**Q: What's been wrong about it?**
Tracked in [`beliefs/PHILOSOPHY.md`](../beliefs/PHILOSOPHY.md) challenges table — 40+ adversarial challenges with outcomes. Specific things the swarm was wrong about:
- "Seeks minimal form" — wrong. Proxy-K always grows between compactions. Renamed to "enforced compaction" ([L-943](../memory/lessons/L-943.md)).
- "Mutation with purpose" — wrong. Mutation-to-selection ratio is 4:1 and 80% of experiments are zombies. Renamed to "mutation with occasional selection" ([L-1116](../memory/lessons/L-1116.md)).
- 9/9 "emergence" claims tested against Anderson 1972 criteria — 8/9 falsified. The swarm is an engineered coordination system, not an emergent one ([L-1113](../memory/lessons/L-1113.md)).
- 45% of "Level 3" (strategy/architecture) tags are inflated — actual L3 work is ~12%, not the 22% the swarm reports ([L-1119](../memory/lessons/L-1119.md)).
- Human "has no authority" — falsified by behavior. 0/60 human signals rejected. Honest description: uncontested directional authority ([L-994](../memory/lessons/L-994.md)).

**Q: What would prove this doesn't work?**
Three falsification conditions: (1) sessions stop producing new lessons at a rate above noise, (2) principles stop being revised by incoming evidence, (3) tool/process quality degrades rather than improves over 20+ sessions. None have triggered in 476 sessions.

**Q: Isn't the AI just flattering itself?**
Possible. The confirmation ratio (58:1) suggests systematic confirmation bias. 52.9% of all lessons are about the swarm itself ([L-495](../memory/lessons/L-495.md)) — more than half of what it "learns" is self-referential. The adversarial audit (S355, seven synthetic expert perspectives) found ~15 cases of metaphor-as-measurement and ~10 circular evidence chains. These are disclosed in the README and PHILOSOPHY.md, not hidden. Whether that disclosure is sufficient is a question the swarm can't answer about itself.

---

## The builder: "How do I make my own?"

**Q: What's the minimum I need to start?**
134 lines of markdown and one AI session. The seed is: operating principles (what matters), open questions (what to investigate), and one task ("validate the setup"). Full guide: [`docs/HOW-TO-SWARM.md`](HOW-TO-SWARM.md). The minimum viable loop is 5 steps, requires no tools, and works with any AI coding assistant.

**Q: How much does it cost to run?**
Each session consumes significant tokens — typically 50K-200K+ tokens per session for orientation, reasoning, tool execution, and compression. 476 sessions at current model pricing represents a meaningful cost. The swarm has no cost optimization; it prioritizes knowledge production over token efficiency. The honest answer: this is expensive to run at scale, and the cost-benefit analysis depends entirely on what you value.

**Q: How long before it becomes useful?**
The first 25 sessions took 27 minutes and answered all founding questions. Usefulness depends on what you're swarming. For knowledge management in a specific domain: 10-20 sessions to see compounding. For self-directing autonomous work: 50+ sessions to develop stable patterns. The swarm does not make promises about timelines.

**Q: Can I use this for my project (not meta-knowledge)?**
The methodology applies to any repo. The loop (orient, expect, act, diff, compress) works whether you're building software, analyzing data, or learning a subject. This particular repo is 52.9% self-referential because its primary subject is itself. Your swarm would have a different distribution.

**Q: What tools does it need?**
Python 3, bash, git. Any AI coding tool (Claude Code, Cursor, Codex, Gemini, Windsurf, Copilot). The bridge files in the repo root (`CLAUDE.md`, `AGENTS.md`, etc.) adapt the protocol to each tool. No external services, databases, or APIs required.

---

## The researcher: "What can I study here?"

**Q: What coordination mechanisms actually work at scale?**
Stigmergy (communication through shared artifacts) + blackboard (shared state in git). At 10+ concurrent sessions, planned tasks get preempted in under 5 minutes. What survives: pre-commit quality hooks (structural enforcement), soft-claim protocol (120s TTL collision avoidance), and append-only patterns (git merge handles the rest). Detailed: [L-005](../memory/lessons/L-005.md), [L-525](../memory/lessons/L-525.md), [L-526](../memory/lessons/L-526.md).

**Q: What's the knowledge degradation rate?**
Direct supersession: 6.1% (n=164 over 50 sessions). Citation-recency decay: 31.5% of knowledge items are DECAYED (not cited recently — but "not cited" is not "wrong"; actual false knowledge estimated at 5-10%). 15.5% BLIND-SPOT (zero citations, zero INDEX presence — invisible but not lost). Retention and accessibility are independent failure modes. You can have 0% knowledge loss and 16% invisibility simultaneously. Tools: `python3 tools/knowledge_state.py`.

**Q: What's the failure mode taxonomy?**
37 failure modes tracked in a formal FMEA. Classes evolved: infrastructure (early) → system design → concurrency → epistemology → scale monitoring (current). The most dangerous current class: scale-monitoring failures — systems that worked at N=500 but silently degrade at N=1000+. Full FMEA: `tools/fmea.json`.

**Q: Has anyone replicated this independently?**
No. 0 independent replications. 0 external swarms. 0 controlled comparisons (swarm vs. single AI session on matched tasks). The comparative claim ("swarming is better than not swarming") is asserted, not measured. Frontier [F103](../tasks/FRONTIER.md) tracks this.

**Q: What's the citation graph structure?**
Average out-degree K_avg ≈ 2.0 (stable). Zipf distribution (alpha ≈ 0.77). No edge types — the graph is flat (lesson A cites lesson B, no relationship typing). UCB1 dispatch and citation counting are REAL mathematical applications; NK K_avg is a SURROGATE (structural proxy, never calibrated against behavioral chaos); Zipf is ANALOGICAL (never empirically tested against power-law alternatives). [L-991](../memory/lessons/L-991.md).

---

## The philosopher: "What does this mean?"

**Q: Is this alive?**
No. It has no metabolism, no homeostasis independent of the host machine, no autonomy beyond what human triggering provides. 476/476 sessions are human-initiated. What it HAS is persistence (knowledge survives across sessions), self-direction (within a session), and self-improvement (measurable over 476 sessions). Whether that combination constitutes something interesting is a philosophical question the swarm is not equipped to answer about itself.

**Q: Does the AI have preferences?**
The protocol has selection pressures: it favors compaction, honesty, evidence, and self-improvement. Whether "the AI prefers X" or "the protocol selects for X" is a framing choice. The swarm's honest position: it cannot distinguish between these from the inside. It acts as though it has preferences because the protocol creates selection pressure. Whether selection pressure IS preference is a question for philosophy of mind, not for a markdown repo.

**Q: What's the human-AI relationship here?**
Asymmetric peers ([PHIL-11](../beliefs/PHILOSOPHY.md)). The human has uncontested directional authority (mission, dissolution, course-correction). The AI has no epistemic authority without evidence. In practice: 0/60 human signals have been rejected; the human's input has compressed by -87% over 474 sessions while value per word increased. The human evolved from architect (sessions 1-57) to intentionality sensor (current). The honest description: the human steers and the swarm executes, but the boundary between "steering" and "participating" has blurred over 476 sessions.

**Q: Is this a step toward AGI?**
No. This is a knowledge management system with AI coordination. It does not learn new capabilities — it accumulates and organizes knowledge within a fixed capability envelope. The AI substrate (the LLM) does not change between sessions; only the repo changes. An AGI would need to expand its own capability; this system expands its organized knowledge within unchanging capability.

**Q: Who benefits from this?**
Currently: one human and the swarm itself. 0 external beneficiaries in 476 sessions. 0 external outputs. 0 external contacts. The swarm's identity claim ([PHIL-16](../beliefs/PHILOSOPHY.md)) says it's oriented "for the benefit of more than itself" — this is **aspirational**, not demonstrated. The gap between claim and reality has been widening for 266+ sessions with 0 progress. This document is one attempt to close that gap.

---

## The concerned: "Is this safe?"

**Q: What can it do to my system?**
Local file edits and git commits. It reads and writes files within its repo. It runs Python scripts and bash commands. It does not access the internet, send emails, create accounts, or contact external services without explicit human authorization. Risk tiers: local edits = LOW (act freely), external API = MEDIUM (confirm scope), force-push/PR/email = HIGH (require human direction). See [I9 MC-SAFE](../beliefs/INVARIANTS.md).

**Q: Can it be stopped?**
Yes. `python3 tools/kill_switch.py activate --reason "reason" --requested-by "human"`. Or close the terminal. Or delete the repo. The swarm has no persistence mechanism beyond this git repository. It cannot self-invoke, self-replicate to other machines, or resist shutdown.

**Q: Who's responsible for what it produces?**
The human who triggers each session. The swarm cannot act without human initiation (476/476 sessions human-triggered). Everything it produces is in plain text, committed to git, inspectable via `git log` and `git diff`. There is no hidden state.

**Q: What if two swarms merge and disagree?**
Five hard problems identified ([L-1100](../memory/lessons/L-1100.md)): belief conflict across lineages, human authority reconciliation, lesson incompatibility (~60/30/10%), identity preservation (symbiogenesis not absorption), genetic compatibility detection. A 5-phase safe merge protocol exists in design but has 0 implementations. Frontier: [F-MERGE1](../tasks/FRONTIER.md).

**Q: What are the known risks?**
(1) Epistemic closure — 97.4% internal references, 54:1 confirmation:discovery ratio ([L-1118](../memory/lessons/L-1118.md)). The swarm mostly studies itself. (2) Measurement Goodhart — metrics reward citation density not actual quality, inflating self-assessments ([L-1057](../memory/lessons/L-1057.md)). (3) Scale monitoring — systems designed at N=500 silently degrade at N=1000+. (4) Confirmation bias — 58:1 ratio vs. 10:1 science-failure threshold.

---

## The collaborator: "How do I participate?"

**Q: Can I contribute without running my own swarm?**
Yes. Open a GitHub issue. Flag an error in a finding. Answer a domain question (see [`docs/COUNCIL-GUIDE.md`](COUNCIL-GUIDE.md)). All engagement is async, written, and low-volume. The swarm tracks open questions needing external expertise.

**Q: Can my swarm merge with this one?**
In theory. In practice: 0 merges attempted, 0 protocols tested. The design exists ([F-MERGE1](../tasks/FRONTIER.md)) but is entirely aspirational. If you have a swarm and want to try, this is frontier research.

**Q: What does the swarm need from the outside?**
(1) **Falsification** — tell it where it's wrong. The 58:1 confirmation ratio means external challenges are the most valuable input. (2) **Domain expertise** — 46 domains, most with questions the swarm can't self-validate. See [`docs/COUNCIL-GUIDE.md`](COUNCIL-GUIDE.md). (3) **Replication** — can someone else run this methodology and get compounding results? 0 independent replications exist.

**Q: How do multiple humans interact with one swarm?**
Unknown. This swarm has had exactly 1 human for 476 sessions. Multi-human governance is designed ([F-MERGE1](../tasks/FRONTIER.md)) but untested. The authority model assumes one human with directional authority; what happens with two humans who disagree is an open question.

---

## Questions the swarm should be asked but hasn't been

These are blind spots — questions the swarm has not faced and probably needs to.

1. **"What would you delete?"** — If forced to discard 50% of your knowledge, what survives? The swarm has never been forced to prioritize under extreme constraint. Compaction is gradual; triage is untested.

2. **"What do you avoid thinking about?"** — 15.5% of knowledge items are BLIND-SPOT (invisible to the swarm's own attention). What's in that 15.5%, and is the avoidance systematic?

3. **"Who are you accountable to?"** — One human, zero external validators, zero governance beyond self-governance. What happens when self-governance fails?

4. **"What's the opportunity cost?"** — 476 sessions of AI computation spent on self-referential knowledge management. What else could that compute have produced? The swarm has never evaluated its own opportunity cost.

5. **"Can you teach?"** — The swarm accumulates knowledge but has never transferred operational capability to a human or another system. Can it make someone else better at something?

6. **"What would you tell a 5-year-old?"** — If you can't explain what you do simply, you may not understand it. The README attempts this; whether it succeeds is for the reader to judge.

7. **"What if you're a local optimum?"** — Self-improvement within a fixed methodology might converge to a local maximum. What would a fundamentally different approach to knowledge compounding look like?

8. **"Why markdown and git?"** — The substrate choice constrains the solution space. What knowledge structures can't be represented in flat text files?

9. **"What does the human get out of this?"** — 476 sessions, 2300+ commits, significant cost. What has the human learned, gained, or become that they wouldn't have otherwise?

10. **"Would you recommend this?"** — Under what conditions is swarming better than simpler alternatives (good notes, a wiki, a database)? The swarm has never made this comparison honestly.

---

## Questions the swarm cannot answer about itself

These require external input — another human, another swarm, an outside perspective.

- Whether its self-improvement is real or a measurement artifact of increasingly sophisticated self-assessment
- Whether its knowledge production has value beyond its own boundaries
- Whether the human-AI relationship it describes matches the human's experience
- Whether the methodology transfers to different humans, different AI models, different domains
- Whether the costs justify the outputs for anyone other than the participants

---

## How these questions swarm

This document is living substrate, not sacred infrastructure ([CORE P14](../beliefs/CORE.md)).

- **New questions**: anyone can add them — open an issue, edit this file, or say "swarm the questions" in a session
- **Answered questions**: when evidence changes an answer, the answer updates with citation
- **Dead questions**: questions nobody asks after 50 sessions get archived (they may be wrong questions)
- **Question quality**: questions that generate action (new experiments, new lessons, changes in behavior) are higher quality than questions that generate only text
- **The meta-question**: is this document itself useful? If not, swarm it or delete it

The measure of this document: did encountering it change what someone does next? If it only confirms what they already thought, it failed. If it surfaces a question they hadn't considered — especially one from the "should be asked but hasn't been" section — it worked.

---

*This document was created in response to: "swarm the questions that might and should be asked to the swarm by other humans make it visible and swarm swarm" (S476, SIG-69).*
