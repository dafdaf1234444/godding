# Reddit Post: Self-Prompting Repo as a Library Pattern

**Suggested title:** "I built a repo that self-directs, self-compresses, and self-improves — here's the complete architecture after 439 sessions"

**Suggested subreddits:** r/LocalLLaMA, r/ClaudeAI, r/ChatGPT, r/programming, r/MachineLearning

---

## The Post

**TL;DR:** A repo that tells any AI session what to do next, without you re-explaining the project each time. After 439 sessions the system runs itself — and more importantly, it improves the process that runs it. Here's every pattern that actually worked, written as a library you can adapt.

---

### The problem this solves

Every AI coding session starts cold. The model doesn't know:
- What this project actually is
- What was tried before and what broke
- What the current priority is
- What "done" looks like for this system

You re-explain. Every time. The cost isn't the typing — it's that the AI makes different decisions than it would if it had context. The same mistakes recur. Progress resets.

A **self-prompting repo** fixes this. The repo *is* the prompt. When any session opens, it reads the repo and knows what to do. More importantly: over time, the repo learns what *it* doesn't know about itself — and schedules the work to find out.

That second property is the interesting one. The system swarms its own improvement.

---

### The architecture

Five components, all files, all readable by any AI:

```
beliefs/          ← What is true about this system
memory/           ← What was learned (indexed, searchable)
tasks/            ← What to do next (open questions, priority queue)
tools/            ← Automation that runs the system
<entry_file>      ← The root prompt (CLAUDE.md, AGENTS.md, etc.)
```

The entry file is the most important piece. It loads fast, points at everything, and tells the AI: *this is how you operate here*. Write it as if you're onboarding a new developer who has never seen the project. If it's not in or linked from the entry file, it doesn't exist for the next session.

---

### The core loop (six steps)

Every session, every time:

**1. Orient**
Before touching anything, synthesize state. What's overdue? What did the last session leave unfinished? What are the open questions? A good orient tool answers this in seconds:

```bash
python3 tools/orient.py
```

If you don't have a tool yet: read the last 5 commits + your NEXT.md + open questions. 2 minutes. Prevents 20 minutes of wrong work.

**2. Dispatch to where it matters most**
Don't just pick a task. Route to the highest-value work using an explicit scoring system. The pattern that works: **UCB1** (Upper Confidence Bound), borrowed from multi-armed bandits.

Every domain or work area has two scores:
- **Exploit score**: how much yield this area has produced historically
- **Explore score**: how long since this area was visited (decays logarithmically)

UCB1 = `yield_avg + C * sqrt(log(total_sessions) / sessions_in_domain)`

This prevents two failure modes: over-mining productive areas until they're exhausted, and ignoring cold areas that might be valuable. The formula naturally rotates attention. You don't have to decide — the math decides.

Implementation: `dispatch_optimizer.py` — outputs a ranked list of work areas with scores.

**3. Declare your expectation before acting**
This is the step most people skip. Before any non-trivial action, write one line:

> "I expect X to be true after I do this."

Then act. Then check if X is true. The gap between expectation and result *is* the learning. A session that confirms every expectation learned nothing. A session with three large gaps produced three lessons.

This isn't just habit-building. Pre-registration prevents post-hoc rationalization. "I expected that" is easy to believe after the fact. Writing it before forces honesty.

**4. Do the work**
Act on it. Use parallel sub-agents for independent tasks. Commit in small steps. Each commit is a trace — `git log --oneline` becomes the system's short-term memory.

**5. Compress what you learned**
When you learn something: write a lesson (max 20 lines). When the same lesson pattern appears 3 times: promote it to a principle (1-2 sentences). When a principle has been tested enough times: it becomes a belief. This is the knowledge compaction stack:

```
observation → lesson → principle → belief
```

The compression step is non-optional. Raw notes don't compound. Distilled knowledge does.

A useful signal: **Zipf's law** on your lesson corpus. If α < 0.80, you have conceptual overlap — too many lessons saying the same thing in different words. Run a compaction pass. If α > 0.90, you have citation scarcity — knowledge exists but isn't being referenced or built on. Fix the index.

**6. Handoff explicitly**
Write what you did, what you expected, what happened, what surprised you, and what the next session should do first. This is the mechanical detail that makes the whole system work. A session without a handoff breaks the chain.

Template:
```
- expect: [prediction]
- actual: [what happened]
- diff: [what was different and why]
- next: [first action for next session]
```

---

### The part that makes it swarm: meta-improvement

Here's what distinguishes a self-prompting repo from a well-organized one: **the system improves the process that runs it**.

Every session has a mandatory reflection step: identify one friction in the swarming process itself, and act on it or file it as a testable question. The rule: reflections must name a specific target file or tool. Vague suggestions ("the system should be faster") convert to real changes ~15% of the time. Named targets ("orient.py calls subprocess 5 times sequentially — parallelize") convert ~85% of the time.

This creates a feedback loop: the system uses its own patterns on itself. Orient → identify friction → dispatch to fix the process → compress the lesson → handoff to next session. The meta-loop runs in parallel with the object-level work.

**Measured results of this property:**
- orient.py went from 47s → 11.8s (parallelized after meta-reflection named it as the bottleneck)
- 940 lessons produced 228 principles and 20 core beliefs (compaction working at every level)
- Voluntary protocols decay within 20 sessions; structurally-enforced ones survive indefinitely (L-601, verified n=1000+)

That last point matters. The meta-improvement loop discovered that rules enforced by code (pre-commit hooks, required fields, tool gates) survive. Rules in markdown files that require willpower to follow decay to ~40% compliance. The system learned this about itself and encoded it as a structural principle.

---

### Five patterns that actually work

**1. Structural enforcement beats documentation**
Every rule that matters should be wired into something automatic: a pre-commit hook, a required field in a form, a gate in a tool that blocks you if the condition isn't met. Rules that live only in documentation will be followed when convenient and forgotten otherwise. Wire the rule into the thing that runs.

**2. Knowledge state tracking**
Not all knowledge is equally active. Classify each belief/lesson:
- **MUST-KNOW**: core operations depend on this
- **ACTIVE**: referenced in the last N sessions
- **SHOULD-KNOW**: in the corpus but unused recently
- **DECAYED**: present but likely stale
- **BLIND-SPOT**: exists but never referenced

The distribution tells you what to do: too much DECAYED → compaction. Too much BLIND-SPOT → index repair. MUST-KNOW missing from index → structural risk.

**3. Concurrent session handling**
If you ever run multiple AI sessions on the same repo: they will race. Solutions:
- Anti-repeat check: `git log --oneline -5` before every non-trivial action
- Soft-claim protocol: mark what you're editing before editing it
- Check for untracked files: concurrent sessions may have partially committed your planned work
- Accept commit-by-proxy: at high concurrency, your work often gets committed under another session's commit message. This is fine — verify via git log rather than re-doing.

**4. Frontier questions as the agenda**
The difference between a repo with notes and a self-directing system: open falsifiable questions. Every time you don't know something, file it:

> "Does parallelizing subprocess calls in orient.py reduce wall time below 15s? Test by measuring before/after."

These become the agenda for future sessions without anyone assigning them. The question must be falsifiable — "Can we improve performance?" is a wish. The example above is a question that can be answered.

**5. Calibration over confidence**
Every measurement is provisional. When you write a lesson, annotate it:
- *Theorized*: plausible, untested
- *Observed (n=1)*: saw it once
- *Measured (n=50)*: consistent signal
- *Falsified*: tried, didn't hold

A corpus where "measured" and "theorized" are indistinguishable produces overconfident decisions. Overconfidence propagates errors. Label honestly.

---

### What doesn't work

**Growing without compacting.** At 200+ lessons you have a pile, not a knowledge base. Schedule compaction every 25 sessions. Archive resolved items, merge similar lessons, promote patterns.

**Only confirmations.** If every experiment confirms what you expected, you're not running experiments — you're writing post-hoc documentation. One in five experiments should try to *break* a belief you hold. Confirmation ratio >10:1 is a science failure signal.

**Hardcoded baselines.** Any tool that compares against a value from session 50 will produce false alarms at session 400. Tools need to read current state dynamically. Before writing a number into a tool: ask if it'll still be correct in 200 sessions.

**No handoff.** The most common failure. You do good work but don't write it down. The next session re-orients from scratch. Make handoff the last mandatory step in your session template.

---

### How to start today

```
1. Create your entry file (CLAUDE.md / AGENTS.md / etc.)
2. One sentence: what this project is
3. Three sentences: current state
4. Two items: what the next session does first
5. Commit: [S001] init: self-prompting seed
```

Session 2 reads that file and builds on it. The compounding starts immediately.

The system won't self-direct autonomously — every session is still human-triggered. What it does: each session starts with a plan instead of a blank slate, and the plan gets better every time because the system learns what kind of plans work.

After 439 sessions, the system knows what it's learned, what it doesn't know, what broke last time, and what to work on next. No re-explanation required. That's the value.

---

**Source:** [github.com/canac/swarm](https://github.com/canac/swarm)
*940 lessons, 228 principles, 439 sessions, all open source.*

---

## Notes on what makes this generic

This guide avoids swarm-specific jargon (no "DOMEX lanes", "UCB1 scores", "L-NNN lesson IDs") in favor of the underlying pattern each tool implements. Anyone building an AI-assisted project can apply:

- The five-component structure (beliefs/memory/tasks/tools/entry)
- The six-step session loop
- UCB1 dispatch logic
- Expect-act-diff pre-registration
- The knowledge state stack
- Structural enforcement over documentation
- The meta-improvement loop

The swarm repo is one instantiation. The library is the pattern.
