# Reddit Post: Self-Prompting Repo as a Library Pattern

**Suggested title:** "I built a repo that self-directs, self-compresses, and self-improves — here's the complete architecture after 439 sessions"

**Suggested subreddits:** r/LocalLLaMA, r/ClaudeAI, r/ChatGPT, r/programming, r/MachineLearning

---

## The Post

**TL;DR:** A repo that tells any AI session what to do next, without you re-explaining the project each time. After 439 sessions the system runs itself — and improves the process that runs it. Here's every pattern that actually worked, written so you can adapt it to any project.

---

### The problem this solves

Every AI coding session starts cold. The model doesn't know:
- What this project actually is
- What was tried before and what broke
- What the current priority is
- What "done" looks like for this system

You re-explain. Every time. The cost isn't the typing — it's that the AI makes different decisions than it would if it had context. The same mistakes recur. Progress resets.

A **self-prompting repo** fixes this. The repo *is* the prompt. When any session opens, it reads the repo and knows what to do. More importantly: over time, the repo learns what *it* doesn't know about itself — and schedules the work to find out.

That second property is the interesting one. The system applies its own improvement process to itself.

---

### The architecture

Five components, all plain files, all readable by any AI:

```
beliefs/          ← What is true about this system
memory/           ← What was learned (indexed, searchable)
tasks/            ← What to do next (open questions, priority queue)
tools/            ← Automation that runs the system
<entry_file>      ← The root prompt (CLAUDE.md, AGENTS.md, .cursorrules, etc.)
```

The entry file is the most important piece. It loads fast, points at everything, and tells the AI: *this is how you operate here*. Write it as if you're onboarding a new developer who has never seen the project. If it's not in or linked from the entry file, it doesn't exist for the next session.

---

### The core loop (six steps)

Every session, every time:

**1. Orient before touching anything**

Before writing a line of code, synthesize the current state. What's overdue? What did the last session leave unfinished? What are the open questions? A one-command summary:

```bash
python3 tools/orient.py   # your version of this
```

If you don't have a tool yet: read the last 5 commits + your priority list + open questions. 2 minutes. Prevents 20 minutes of wrong work.

**2. Route to the highest-value work**

Don't just pick a task from the top of a list. Actively route to where work is most needed. The pattern that works: balance **exploitation** (keep doing what's been productive) with **exploration** (visit neglected areas before they rot).

A simple formula — adapted from multi-armed bandit research (UCB1):

```
priority = avg_yield + C × sqrt(log(total_sessions) / sessions_in_this_area)
```

Where `avg_yield` is how much useful output this work area has produced per session, and the second term grows the longer an area goes unvisited. Run this across all your work areas and do the top-ranked one. The math naturally rotates attention — you don't have to decide what's been neglected.

**3. Declare your expectation before acting**

This is the step most people skip. Before any non-trivial action, write one line:

> "I expect X to be true after I do this."

Then act. Then check if X is true. The gap between expectation and result *is* the learning. A session where everything went exactly as expected produced no new information. A session with three large gaps produced three lessons worth keeping.

This isn't just a habit. Writing the expectation before prevents you from convincing yourself afterward that you knew it all along.

**4. Do the work**

Act on it. Run independent sub-tasks in parallel where possible. Commit in small steps. Each commit becomes a trace — `git log --oneline` is the system's short-term memory. Structured commit messages (`[S001] what: why`) make that log scannable at a glance.

**5. Compress what you learned**

When you learn something: write a note (short — max a page). When the same pattern appears 3 times in different forms: distill it into a one-sentence rule. When a rule has held up against repeated testing: promote it to a core belief. The stack:

```
observation → note → rule → belief
```

The compression step is non-optional. Raw notes accumulate. Distilled knowledge compounds.

A useful check: if you have 200 notes but they all say similar things, run a compaction pass — merge overlapping notes, promote repeated patterns, archive resolved ones. Knowledge that can't be summarized can't be used.

**6. Hand off explicitly**

Write what you did, what you expected, what actually happened, and what the next session should do first. This is the mechanical detail that makes the whole system work. A session without a handoff breaks the chain.

Template:
```
- expect: [prediction]
- actual: [what happened]
- diff: [what was different and why]
- next: [first action for next session]
```

---

### The part that makes it self-improving

Here's what distinguishes a self-prompting repo from a well-organized one: **the system improves the process that runs it**.

Every session includes a mandatory reflection step: identify one friction in the *process itself* — not the project work, but the way sessions are run — and either fix it or file it as a testable question.

The rule that took time to learn: **reflections must name a specific target**. "The system should be faster" converts to a real change about 15% of the time. "The orientation step calls the same slow subprocess five times — parallelize it" converts about 85% of the time. Vague is a wish. Named is a task.

This creates a feedback loop: the same orient → dispatch → expect → act → compress → handoff cycle runs on the process itself, not just the work. The meta-loop runs in parallel with the object-level work.

**Concrete results of this loop on our project:**
- Orientation went from 47 seconds → 11.8 seconds (named bottleneck → parallelized → measured)
- 940 raw notes compressed into 228 rules and 20 core beliefs (compaction working at every level)
- Voluntary rules decayed to ~40% compliance; rules enforced by code (pre-commit hooks, required fields, automated gates) survived indefinitely

That last point is the most important thing the self-improvement loop discovered. The system applied its own process to its own protocols — and found that any rule requiring willpower eventually stops being followed. The fix is structural: wire the rule into something that runs automatically.

---

### Five patterns that actually work

**1. Structural enforcement beats documentation**

Every rule that matters should be wired into something automatic: a pre-commit hook, a required field in a form, a tool that blocks you if the condition isn't met. Rules that live only in a README will be followed when convenient and forgotten otherwise. Before writing a rule, ask: *is this wired into something that runs?* If not, expect ~40% compliance at best.

**2. Track the health of your knowledge**

Not all knowledge is equally active. Over time, notes and rules drift into different states:

- **Active**: referenced and used regularly
- **Background**: in the system but rarely touched
- **Stale**: hasn't been referenced in a long time — may be outdated
- **Invisible**: exists but never linked to or cited — effectively lost

The distribution tells you what to do: too much stale knowledge → run a compaction pass. Too much invisible knowledge → fix your index (make it findable). Critical knowledge not referenced anywhere → structural risk.

**3. Multiple sessions on the same repo**

If you ever run more than one AI session at the same time on the same repo, they will race. A few rules that prevent pain:

- Check recent commits before every non-trivial action — the work you planned may already be done
- Mark what you're editing before editing it (a simple lock file or comment works)
- Check for uncommitted working-tree files — a concurrent session may have partially completed your planned task
- At high volume, one session's work often ends up committed in another session's commit message. This is fine — check git log rather than re-doing the work.

**4. Open questions as the agenda**

The difference between a repo with notes and a self-directing system: **open, falsifiable questions**. Every time you don't know something, file it as a question with a testable answer:

> "Does running the five subprocess calls in parallel cut orientation time below 15 seconds? Test: measure wall time before and after."

These become the agenda for future sessions without anyone assigning them. The question must be falsifiable — "Can we improve performance?" is a wish. The example above is a question that produces a definite yes or no.

**5. Label your confidence honestly**

Every piece of knowledge you write down is provisional. Annotate it:
- *Theorized*: plausible, untested
- *Observed once*: saw it happen, not sure it'll repeat
- *Measured*: tested consistently, with sample size
- *Falsified*: tried, didn't hold

A knowledge base where "measured (n=200)" and "I think so" look identical produces overconfident decisions. Overconfidence propagates errors forward. Label what you actually know vs. what you believe.

---

### What doesn't work

**Growing without compacting.** At 200+ notes you have a pile, not a knowledge base. Schedule compaction every 25 sessions or when notes start feeling repetitive. Archive resolved items, merge similar ones, promote patterns.

**Only running confirming experiments.** If every test confirms what you expected, you're not experimenting — you're writing post-hoc documentation. One in five tests should explicitly try to *break* something you believe. A confirmation rate above 90% is a red flag.

**Hardcoded numbers in tools.** Any tool that compares against a threshold you wrote in week 1 will produce false alarms in month 6. Tools should read current state dynamically. Before hardcoding a number: ask if it'll still be correct after the project doubles in size.

**No handoff.** The most common failure. You do good work but don't write it down. The next session re-orients from scratch. Make handoff the last mandatory step in every session, not an optional afterthought.

---

### How to start today

```
1. Create your entry file at the repo root
   (CLAUDE.md for Claude, AGENTS.md for Codex, .cursorrules for Cursor, etc.)
2. Write one sentence: what this project is
3. Write three sentences: what the current state is
4. Write two items: what the next session should do first
5. Commit: "session 1: self-prompting seed"
```

Session 2 reads that file and builds on it. The compounding starts immediately — not because anything is magic, but because you stop losing context between sessions.

The system won't self-direct autonomously. Every session is still human-triggered. What it does: each session starts with a plan instead of a blank slate, and the plan gets better over time because the system tracks what kinds of plans work.

After 439 sessions, the system knows what it's learned, what it doesn't know, what broke last time, and what to work on next. No re-explanation required. That's the value.

---

**Source:** [github.com/canac/swarm](https://github.com/canac/swarm)
*940 notes, 228 rules, 439 sessions, all open source.*
