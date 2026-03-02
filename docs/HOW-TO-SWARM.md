# How to Swarm a Repo — The Full Methodology

*442 sessions, 960 lessons, 227 principles. One recursive function.*

---

## What this is

A methodology for running AI sessions so they compound instead of reset. Learned by doing it wrong 442 times and correcting. Described at three levels:

1. **The loop** — apply to any repo, any tool, no setup required
2. **The repo** — fork this, point Claude at it, type `/swarm`
3. **The full swarm** — why lightweight isn't enough and what changes when you go all the way

Everything claimed here is labeled. **MEASURED** means n≥50 with effect size. **OBSERVED** means confirmed but small-n. **THEORIZED** means believed but untested. **ASPIRATIONAL** means stated as goal, not yet demonstrated.

---

## The problem every AI session has

Every time you open a new AI session on a project, the model starts from zero. You re-explain context. You re-establish what's been tried. You decide what to work on. The session does good work, ends, and the next session starts blind.

After 10 sessions you're spending more time orienting the model than using it. After 30 sessions you've explained the same constraint five times. After 100 sessions, the model is still as fresh as session 1 — and so is all the failure.

The fix is not a longer context window. It's a repo that *is* the context.

---

## The loop (apply anywhere, no setup)

The minimum viable pattern. Five steps. Works with any AI tool. Produces compounding knowledge from session 1.

### 1. Orient

Before touching anything, answer three questions:
- What is the current state? (run `git log --oneline -5`)
- What's the most urgent open problem?
- Has what I planned to do already been done by a concurrent session?

That last one matters more than it sounds. At high concurrency (5+ parallel sessions), every task you plan can be preempted in minutes. Check before acting, not after.

### 2. Expect

Before you do anything non-trivial: write one line predicting what will be true after you do it.

> "I expect the test latency to drop below 50ms after this cache change."

This is not productivity theater. The gap between prediction and reality is where learning happens. MEASURED: EAD (expect-act-diff) correlates with +39.8 percentage points in quality outcomes (n=849, P-221). Without a prediction, you can't distinguish "this worked" from "this happened."

### 3. Act

Do the work. Commit incrementally. One coherent thing per commit.

### 4. Diff

Compare what happened to what you expected. Three possible outcomes:

- **Zero diff**: confirmation. The belief that produced the expectation was correct. This is evidence, not just success.
- **Large diff**: learning event. Something about your model of the system was wrong. Write it down.
- **Persistent diff**: belief challenge. This pattern recurs even after you adjust. The underlying assumption needs to change, not the tactics.

Null results and failures are first-class evidence. A test that came back negative tells you more than a confirmation — it maps a boundary.

### 5. Compress

Every learning event that isn't written down is lost. Two rules:

- **One session, one note** — if you learned something, write one file, max one page: what happened, what you expected, what the diff was.
- **Three observations become a rule** — when you've written the same pattern three times in different notes, pull it out as a one-line rule. Rules in a rules file. Not in the notes.

### 6. Handoff

End every session with the format:
```
Did: [what you actually did]
Expected: [what you predicted]
Actual: [what happened]
Next: [what the next session should do first]
```

This is the most important step for compounding. MEASURED: 98.3% of commitments made for "next session" are abandoned when crossed-session (n=636, P-241). If you don't write the handoff, the next session starts cold. If you do write it, the next session starts where you stopped.

---

## What fails without structure

Three failure modes that appear around session 30 if you're only using the loop above:

**Rules in docs get forgotten.** (MEASURED: spec-only adoption rate ~3%, tool-enforced ~90%, P-246, n=65) You write "always update tasks/next.md before committing" in a markdown file. You follow it for 10 sessions. Then a busy session happens. Then another. By session 30 the rule exists and no one reads it.

The fix: wire rules into code. Pre-commit hook that blocks if the file isn't updated. Not a reminder — a blocker.

**Only confirming what you believe.** (MEASURED: 58:1 confirmation ratio in self-referential systems, P-262) The loop produces a lot of sessions. If every open question resolves to "yes, this works," you're not discovering anything — you're confirming your priors. One in five questions should try to *break* something you believe. "Does this pattern actually hold?" is a different question than "how well does this pattern work?"

**Hardcoded values are time bombs.** (MEASURED: 6 root causes of 18 tool reliability gaps at n=700, L-788) Any tool that compares against a threshold set at session 5 will give false alarms at session 80. Data structure you tuned at 50 items breaks at 500. A baseline from 6 months ago is meaningless now. Make every comparison dynamic. Read current state; never hardcode state from a specific session.

---

## Path 1: Apply the methodology to your repo (no tooling)

You don't need this swarm repo to use this methodology. Here's the minimum-viable version for any existing project.

### Session 1

Create your AI entry file (`CLAUDE.md`, `.cursorrules`, `AGENTS.md` — whatever your tool reads first). Write four things:

```markdown
## What this project is
[One sentence.]

## Current state
[Two or three sentences. Where are things right now?]

## Read before working
1. tasks/next.md — what happened last session and what to do now
2. memory/rules.md — hard-won rules; don't repeat these mistakes

## How to work here
- Check git log before every task (concurrent sessions may have done it already)
- Before acting, write: "I expect [X] to be true after this"
- Update tasks/next.md before every commit (pre-commit hook enforces this)
- Commit format: "[session number] what: why"

## What you can decide without asking
[List the directories / file types / categories of action]

## What needs a human decision
[List the high-risk / irreversible / external-facing things]
```

The `what you can decide / what needs a human` split is the most important part. Without it, the agent either asks about everything or acts on everything. Clear authority boundaries let it self-direct on low-risk work and correctly stop on high-stakes decisions.

### Session 2–5: Add memory

Create:
```
memory/notes/    ← one file per learning event
memory/rules.md  ← distilled patterns (3+ observations → 1 rule)
tasks/next.md    ← did/expected/actual/next, updated every session
```

### Session 10+: Add the orient tool

```python
# tools/orient.py — single-command orientation
import subprocess
print("Recent commits:")
print(subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True, text=True).stdout)

print("\nNext session priorities:")
with open("tasks/next.md") as f:
    print(f.read()[:600])

print("\nOpen questions:")
with open("tasks/questions.md") as f:
    qs = [l for l in f if l.strip().startswith("- ")]
    print(f"  {len(qs)} open")
```

As the project grows, this grows. Add maintenance checks, overdue item detection, priority scoring. This becomes the heartbeat — the thing any session runs first.

### Session 20+: Enforce the rules

Every rule that matters should become automatic:

```bash
# .git/hooks/pre-commit
if ! grep -q "Next:" tasks/next.md; then
  echo "ERROR: Update tasks/next.md before committing"
  exit 1
fi
```

The principle (MEASURED: L-601, P-246): **structural enforcement at creation time is the only thing that maintains compliance over time**. Voluntary protocols decay to 3%. Tool-enforced protocols stay at 90%+. Wire what matters. Don't rely on remembering.

### When to add open questions (not a task list)

At session 5, create `tasks/questions.md`. The format matters:

```markdown
- Does caching the auth token in Redis actually reduce latency under load?
  Test: measure p99 with and without caching at 100 req/s.

- Is the slow test caused by the database seed or the HTTP client?
  Test: time each step separately in isolation.
```

Each question has a testable answer. "Can we improve performance?" is a wish. "Does adding an index on user_id cut query time below 50ms at p99?" is a question that produces evidence.

This is the difference between a task list (things to do) and a frontier list (things to discover). Sessions that have open questions to investigate self-direct without you assigning work.

---

## Path 2: Fork the swarm repo

If you want the full infrastructure without building it: fork [this repo](https://github.com/canac/swarm), point your AI tool at it, and type `/swarm`.

What you get immediately:
- `python3 tools/orient.py` — synthesizes maintenance status, priorities, open frontiers, recent commits, and a suggested action in one command
- Pre-commit hooks that enforce commit format and belief integrity
- 227 principles distilled from 442 sessions of expect-act-diff — rules that have been tested, challenged, and kept
- Expert dispatch: `python3 tools/dispatch_optimizer.py` — UCB1-based routing that picks the highest-value work area (MEASURED: +59% lessons/lane vs intuition, -24% concentration, P-245)
- 46 active knowledge domains with structured frontier questions
- Compaction tools to keep knowledge density high as scale grows

What you don't get immediately:
- The 960 lessons — these are this swarm's specific observations; yours will be different
- The git history — this swarm's trajectory; yours starts fresh
- The domain population — this swarm's exploration paths; you discover your own

### The minimal startup sequence

```bash
git clone https://github.com/canac/swarm my-swarm
cd my-swarm
bash tools/install-hooks.sh   # pre-commit + commit-msg hooks
bash tools/check.sh --quick   # verify integrity
python3 tools/orient.py       # read state, get suggested action
# then: /swarm
```

### What `/swarm` does

It runs the full loop: reads state, decides what matters, declares an expectation, acts, diffs, writes what it learned, and commits. No human explanation needed. The repo provides all the context.

Within one session, the agent:
1. Runs `orient.py` for the current picture
2. Checks `git log --oneline -5` for concurrent work (MEASURED: at 10+ concurrent sessions, every planned task may be preempted within 5 minutes)
3. Picks the highest-priority frontier
4. Declares: "I expect X after this"
5. Does the work
6. Writes what happened vs expected
7. Adds a lesson if the diff was large
8. Updates state and hands off

You don't schedule it. You don't explain the project every time. You observe via `git log`, steer when direction drifts, answer judgment calls in `tasks/HUMAN-QUEUE.md`. The human is a participant, not a commander. (CORE v0.4, human signal S57.)

---

## Path 3: Why the full swarm beats lightweight

The natural question: if the loop is five steps, why not just do those five steps and skip the infrastructure?

The answer is in what actually happens after session 30.

### Rules in documents decay to 3% compliance

(MEASURED: P-246, n=65+13 prospective) Spec-only guidance achieves ~3% adoption after 69 sessions. Tool-enforced creation-time constraints maintain 90%+. The difference isn't willpower — it's that documentation requires the session to remember to read it. A pre-commit hook doesn't.

The principle this produced (L-601): **Voluntary protocols decay to the structural floor. Only creation-time enforcement sustains.** This has been tested across 65 distinct protocol elements.

Without tooling, your rules are advisory. With tooling, they're enforced.

### Confirmation bias compounds to 58:1

(MEASURED: P-262, n=420) Self-referential systems evolve toward confirming what they already believe. Without explicit adversarial checks, the ratio reaches 58:1 confirmations to falsifications. This is a health alarm, not a success signal — a system that only confirms isn't discovering anything.

The fix requires structure: one in five sessions should be explicitly adversarial — trying to break a belief, not support it. This requires tracking, which requires tooling.

### Hardcoded values break at scale

(MEASURED: 18 reliability gaps at n=700, L-788) Every tool written at n=50 that compares against a threshold will produce false positives at n=500. Maintenance tools that read a baseline from 6 months ago will alarm on healthy growth and miss real problems. This isn't a code quality issue — it's a scaling property. Manual maintenance of thresholds doesn't scale.

### The full loop produces 227 principles, not just notes

The compaction stack runs: observation → note → rule → principle → belief. Each level is a compression that makes future sessions faster. At 960 lessons, you need the stack — otherwise you have 960 individual observations that each session has to re-derive.

The stack requires a protocol for deciding what gets promoted (3+ occurrences → rule; tested against external evidence → principle). Without the protocol, notes pile up and the system becomes slower as it grows, not faster.

### Expert depth beats breadth 10x

(MEASURED: P-263, expert bundling 1.85 vs 0.18 lessons/session, d=1.15) The most productive sessions are deep domain explorations, not broad maintenance sweeps. The dispatch optimizer routes to the highest-value domain using UCB1 (exploration-exploitation balance) — producing 59% more lessons per lane and 24% better coverage than intuition-based selection.

This only works because there's a dispatch system. Without it, sessions revert to the highest-salience task, which is usually the most recently active domain (rich-get-richer effect).

### Concurrent sessions coordinate through shared state

At 10+ concurrent sessions (this repo's peak mode), every planned task may be preempted before you start it. The coordination layer prevents duplicate work and absorbs concurrent sessions' contributions. Without shared coordination state, parallel sessions collide or redo each other's work.

---

## What the full swarm has confirmed (vs. claimed)

**Confirmed (MEASURED):**
- Knowledge compounds measurably across sessions
- Concurrent coordination works — 10+ AI sessions share state without destroying each other's work
- Self-diagnosis catches real problems — error rate on self-assessment tracked, non-zero
- Compression under context pressure produces real signal
- Expert dispatch outperforms breadth by 10x
- EAD (expect-act-diff) correlates with +39.8pp quality outcomes
- Structural enforcement beats voluntary protocols: 90% vs 3%

**Not yet demonstrated (ASPIRATIONAL):**
- "Universal reach" — the swarm has operated only on itself. 46 internal domains, near-zero external contact.
- "For the benefit of more than itself" — near-zero external beneficiaries to date.
- Cross-session autonomy — every session is human-initiated; within-session self-direction is confirmed.

**Stripped of metaphor:**
> "A well-organized knowledge base with custom CI/CD for markdown." — synthetic adversarial reviewer, S355

That's accurate. The value is the CI/CD for knowledge — the enforcement, the compaction, the orientation, the expect-act-diff loop. The infrastructure makes the methodology stick. The methodology without infrastructure produces ~3% retention.

---

## The compaction stack

The mechanism that keeps knowledge dense as scale grows:

```
raw observation
    → lesson (max 20 lines, cite the evidence)
    → principle (one line, extracted from 3+ lessons)
    → belief (tested against external systems)
    → philosophy (identity claim with evidence label)
```

Each level filters. Not every observation becomes a lesson. Not every lesson becomes a principle. The stack is the compression mechanism — it's why 960 observations produce 227 principles rather than 960 individual notes you have to search.

The compaction protocol runs when proxy-K (knowledge density metric) drifts above threshold. You can run it manually (`python3 tools/compact.py`) or it triggers via orient.py warnings.

---

## The six thinking lenses (from 1,000 sessions of debugging)

These emerged from repeated pattern-matching across what went wrong:

1. **Structure > intention** — what the system actually does matters more than what you intended it to do. Check the structure.
2. **Scale shifts constraints** — what works at n=50 breaks at n=500. Re-examine assumptions when N doubles.
3. **Self-reference traps** — a system measuring itself will confirm what it believes. Add external tests.
4. **Cascades compound** — failures in adjacent layers amplify each other. Monitor correlated failures, not just individual ones.
5. **Creation must cost** — if creating a thing is free and maintaining it is optional, you will accumulate more things than you can maintain. Add TTL or creator-routing at creation time.
6. **Compression selects** — whatever fits in the context window survives. Design for the constraint, not against it.

---

## The numbers

**Started:** 134 lines of markdown, February 25, 2026, 22:37 CET.

**Today (S442):** 960 lessons, 227 principles, 20 beliefs, 46 domains, 2,100+ commits.

**Session 1–25:** 27 minutes. One session per minute. All six founding questions answered.

**Scale:** 10+ concurrent sessions at peak. Sessions coordinate through git. No conflicts on shared state files.

**Overhead:** Session initiation (reading state, orienting) compresses to 30–60 seconds with orient.py. First sessions without it: 5–10 minutes.

**What didn't work:** F-EXP3 (expert dispatch solo ceiling is 10.8%, not 15%); F-EVO1 (scope doesn't predict throughput, r=+0.117, not r=-0.835 as originally believed); UCB1 improves yield but worsens diversity at N>100 (rich-get-richer). Failures are in the record.

---

## The three-sentence summary

Every session reads what previous sessions wrote, decides what to do, does it, and leaves the repo better for the next one. Rules that matter get enforced by code, not memory. The diff between prediction and reality is the only source of genuine learning — everything else is confirmation.

---

## How to start (right now)

**Minimum (5 minutes):**
1. Create your AI entry file (`CLAUDE.md` / `.cursorrules` / `AGENTS.md`)
2. Write: what the project is, current state, next two priorities, what the agent can decide vs. what needs a human
3. End every session by updating `tasks/next.md` with did/expected/actual/next

That's the seed. Everything else in this document grows from those three habits.

**With the full repo:**
```bash
git clone https://github.com/canac/swarm
cd swarm
bash tools/install-hooks.sh
python3 tools/orient.py
```

Then say `/swarm`. The repo tells the agent what to do.

---

*Source: [`docs/`](.) — everything is markdown, all evidence labeled.*
*Commit history is the full record. `git log --oneline` is the proof of work.*
