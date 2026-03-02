# Reddit Post: How to Build a Self-Prompting Repo

**Suggested title:** "How to make a repo that tells any AI what to do next — step by step, from nothing to self-improving"

**Suggested subreddits:** r/LocalLLaMA, r/ClaudeAI, r/ChatGPT, r/programming, r/MachineLearning

---

## The Post

**TL;DR:** You can make a repo that tells any AI session what to do, what was learned, and what's broken — without re-explaining every time. It takes about 5 sessions to feel useful, 20 sessions to feel alive, and 50+ sessions before it starts improving its own process. Here's exactly how to build it, step by step.

---

### What you're building

Right now, every time you open a new AI session on a project, the model starts from zero. You explain the project. You re-establish context. You decide what to work on. The AI makes decisions without the history of every other session.

A self-prompting repo fixes this. The repo *is* the context. When any AI session opens, it reads the repo and knows: what this project is, what was tried before, what broke, and what to do next. You don't re-explain. The session picks up where the last one left off.

More importantly: once this system is running, it starts improving itself using the same loop it uses for everything else. That's when it gets interesting.

Here's how to get there.

---

### Step 1: The entry file (session 1)

The single most important thing is a file at the root of your repo that any AI reads first. Different tools name it differently:

- Claude: `CLAUDE.md`
- Cursor: `.cursorrules`
- Codex / OpenAI Agents: `AGENTS.md`
- Windsurf: `.windsurfrules`

Create that file. Write exactly four things in it:

```markdown
## What this project is
[One sentence. What does this repo do?]

## Current state
[Two or three sentences. Where are things right now?]

## What to do next
- [First priority]
- [Second priority]

## How to work here
[Any rules that matter — code style, commit format, what not to touch]
```

Commit it:
```
git commit -m "session 1: add entry file"
```

That's it. Session 1 is done. The next AI session that opens this repo will read that file and know where to start. You've broken the cold-start problem for the first time.

---

### What the entry file needs to actually tell an agent

The four-field template above is the minimum. But an agent isn't a human — it doesn't infer things you leave implicit. The entry file is the agent's operating manual. If a rule isn't in it, the agent won't follow that rule. If a decision isn't covered, the agent will guess.

Here's a more complete template once you're past session 5:

```markdown
## What this project is
[One sentence.]

## Read these first
1. tasks/next.md — what happened last session and what to do now
2. memory/rules.md — hard-won rules; don't repeat these mistakes
3. tasks/questions.md — open questions waiting for an answer

## How to start each session
1. Run: python3 tools/orient.py
2. Check: git log --oneline -5 (someone else may have already done your planned task)
3. Pick the highest-priority item from the orient output
4. Write one line: "I expect X after doing this" — before doing anything

## What you can decide on your own
- Adding notes, writing lessons, filing open questions
- Code changes inside [specific directories]
- Committing local work
- Updating tasks/next.md and memory/

## What needs a human decision
- Deleting anything that can't be recovered
- Pushing to external services or APIs
- Changing project direction or goals
- Anything outside [specific directories]

## How to commit
Format: "[session number] what: why"
Example: "session 12: cache auth token — reduces latency at high load"
Always update tasks/next.md before committing.

## How to end each session
1. Write the handoff in tasks/next.md (did / expected / actual / next)
2. Write any new note to memory/notes/ if you learned something
3. Name one process friction: a specific file or step that slowed you down
4. Commit everything
```

The **"what you can decide vs. what needs a human"** section is the most important addition. Without it, the agent either asks about everything (annoying) or acts on everything (dangerous). Clear authority boundaries let the agent self-direct confidently on low-risk work and correctly stop and ask on high-stakes decisions.

The **"check git log before starting"** instruction matters if you ever run more than one session. The work you planned may already be done. An agent that doesn't check will redo it.

---

### Step 2: Give the AI a memory (sessions 2–5)

One file isn't enough to build up knowledge. You need somewhere to store what you learn over time.

Create this structure:

```
memory/
  notes/     ← things you learn, one file per insight
  index.md   ← a short table of contents for everything in memory/
tasks/
  next.md    ← what to do in the next session (updated every session)
```

At the end of every session, do two things:

**Update `tasks/next.md`:**
```markdown
## Last session
- Did: [what you actually did]
- Expected: [what you thought would happen]
- Actual: [what actually happened]
- Surprised by: [anything unexpected]

## Next session
- [First thing to do]
- [Second thing to do]
```

**Write a note if you learned something:**

If you discovered something about how the project works, or something that broke, or a pattern you noticed — write a short note in `memory/notes/`. Max one page. Give it a descriptive filename:

```
memory/notes/auth-token-refresh-breaks-on-expired-sessions.md
memory/notes/running-migrations-before-tests-is-required.md
```

After 5 sessions of doing this, your entry file can point at `tasks/next.md` and `memory/index.md`. Now any new session reads: what the project is, what's been learned, and what to do next. Context is no longer lost between sessions.

---

### Step 3: Add structure for open questions (sessions 5–15)

The thing that turns a well-organized repo into a self-directing one is **open questions**. Not a task list — a list of things you genuinely don't know yet, written as testable questions.

Create `tasks/questions.md`. Whenever you don't know something, write it there:

```markdown
## Open questions

- Does caching the auth token in Redis actually reduce latency under load?
  Test: measure p99 latency with and without caching at 100 req/s.

- Is the slow test caused by the database seed or the HTTP client?
  Test: time each step separately in isolation.

- Does the nightly job fail only on Mondays or every day?
  Test: check logs for the last 14 days.
```

The format matters: each question has a **testable answer**. "Can we improve performance?" is a wish. "Does adding an index on user_id cut query time below 50ms at p99?" is a question that produces a yes or no.

Now update your entry file to point here. A new session can read `tasks/questions.md` and know exactly what to investigate — without you assigning it.

This is the point where the repo starts feeling self-directing. The AI has work waiting for it that isn't on a task list. It's a list of things to *discover*.

---

### Step 4: Build the orient tool (sessions 10–20)

By session 10, manually reading three files at the start of each session starts taking a few minutes. Build a simple script that does it for you:

```python
# tools/orient.py
import subprocess
import os

print("=== ORIENT ===")
print()

# Show recent commits
print("Recent commits:")
result = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True, text=True)
print(result.stdout)

# Show next.md
print("Next session priorities:")
with open("tasks/next.md") as f:
    print(f.read()[:500])  # first 500 chars

# Show open questions count
questions_file = "tasks/questions.md"
if os.path.exists(questions_file):
    with open(questions_file) as f:
        questions = [l for l in f if l.strip().startswith("- ")]
    print(f"Open questions: {len(questions)}")
```

Run this at the start of every session. Now orientation takes 5 seconds instead of 3 minutes.

As the project grows, `orient.py` grows with it. Add checks for overdue things, stale notes, broken states. This tool becomes the heartbeat of the system — the thing that tells any session what's actually going on.

---

### The agent's session protocol

Once the system has memory and open questions (steps 2–3), you want agents to follow a consistent loop every session. Without an explicit protocol in the entry file, different sessions will behave differently and leave inconsistent state.

Give the agent this protocol in the entry file — or link to a file that describes it:

**At the start of every session:**
1. Run orient (the script or manual equivalent)
2. Check recent commits — if your top-priority item is already done, confirm it and move to the next
3. Pick one item to work on
4. Write your expectation: *"I expect X to be true after I do this"*

**During the session:**
- Work on one thing at a time, commit frequently
- If you discover the task is bigger than expected: commit what you have, update `tasks/next.md`, stop
- If you discover something that contradicts a rule: write a note, don't silently change the rule
- If you're blocked by something that needs a human decision: stop, write the question to `tasks/questions.md` with a `[NEEDS HUMAN]` tag, then pick a different task

**At the end of every session:**
- Check if your expectation was right
- If the diff was large (expected X, got Y): write a note explaining what you learned
- Update `tasks/next.md` — the handoff format: did / expected / actual / next
- Name one process friction: the specific file or step that slowed you down this session
- Commit

This protocol sounds bureaucratic written out. In practice it takes 2–3 minutes at the start and end of a session and prevents 90% of the state corruption that comes from unstructured sessions. The orient step alone prevents duplicate work. The handoff alone prevents cold starts.

---

### Step 5: Turn repeated notes into rules (sessions 15–30)

By session 15, you'll notice you've written the same insight multiple times in different notes. That's the signal to distill it.

When you see the same pattern in 3+ notes: pull it out into a one-sentence rule. Create `memory/rules.md`:

```markdown
## Rules (distilled from experience)

- Always run migrations before running tests, or tests fail silently.
- The auth service needs 2 seconds to warm up — don't hit it immediately on startup.
- Batch size above 500 causes OOM on the staging server; keep it at 200.
```

Each rule should be:
- One sentence
- Specific enough to be actionable
- Traceable back to something you actually observed

Now point the entry file at `memory/rules.md`. Every new session reads these rules and doesn't repeat the mistakes that produced them.

This is the compaction stack in action:
```
observation → note → rule → core belief
```

Not everything becomes a rule. Most notes stay as notes. A note becomes a rule only when you've seen the pattern 3+ times. A rule becomes a core belief only when you've tested it enough to trust it. The stack filters as it promotes.

---

### Step 6: Make rules structural, not documentary (sessions 20–40)

Here's the most important thing you'll learn: **rules in markdown files get forgotten**.

You might follow them for 10 sessions. Then a busy session happens. Then another. By session 30 the rule is there but no one reads it.

The fix: wire rules into code. Every rule that really matters should be enforced automatically:

- A pre-commit hook that checks the rule before allowing a commit
- A required field in a template that can't be left blank
- A check in `orient.py` that flags when the rule is being violated

Example: if your rule is "every session must update tasks/next.md before committing":

```bash
# .git/hooks/pre-commit
if ! grep -q "Last session" tasks/next.md; then
  echo "ERROR: tasks/next.md wasn't updated this session"
  exit 1
fi
```

Now the rule is enforced automatically. You don't have to remember it. The system remembers it for you.

This pattern generalizes: every time you find yourself relying on willpower to follow a process step, ask how to make it structural. Automated enforcement is the single biggest lever for keeping the system working over time.

---

### Running multiple agents on the same repo

Once the system is working well with one agent at a time, you might want to run several sessions in parallel — one working on a bug, one investigating an open question, one doing maintenance. This is where things get interesting and also where things break if you're not careful.

**The core problem:** two agents start at the same time, both read `tasks/next.md`, both decide to do the same highest-priority task. They race. One wins. The other either duplicates the work or overwrites the first agent's output.

**Four rules that prevent most parallel-session problems:**

**1. Check git log before every non-trivial action**

Every agent, at the start of every task (not just session start), runs:
```bash
git log --oneline -5
```

If the task you were about to start appears in the recent commits, it's done. Confirm it, move to the next item. Don't redo it.

At high session volume (5+ concurrent), this check needs to happen before *each* task within a session, not just once at the start. Sessions commit fast. Your planned work can be preempted in minutes.

**2. Mark what you're about to edit before editing it**

Before touching a file that another agent might also be editing, leave a marker:

```bash
# simple lock-file approach
echo "session-14 editing" > tasks/next.md.lock

# do your work

rm tasks/next.md.lock
```

More robust: write your session ID and timestamp into a `workspace/claims.md` file. Any other agent that reads claims before editing will see the conflict and skip to a different task.

**3. Give each agent a distinct scope**

The simplest coordination is no coordination: assign different agents to different directories or work areas. One agent owns `memory/`, one owns `tools/`, one owns the source code. They can't collide if they're not touching the same files.

In your entry file, add a `## Your scope` section that each agent reads. Different agent instances (or different sessions) can be given different scopes via different entry files or via a command-line argument.

**4. Accept that sometimes work gets absorbed**

At high concurrency (10+ parallel sessions), something useful happens: when an agent has uncommitted work and another agent commits first, the first agent's work sometimes ends up included in the second agent's commit. This is the normal behavior of git-based collaboration.

Don't fight it. When you see your planned work in the log under a different session's commit: confirm it's there, mark it done, move on. Re-doing already-committed work is waste. Checking git log before each task is how you catch this.

---

### Step 7: Add the meta-improvement loop (sessions 30–50)

This is where the system starts improving itself.

Add one item to your `tasks/next.md` template:

```markdown
## Process friction this session
- [One specific thing about how sessions are run that slowed you down or felt wrong]
- Concrete target: [file or tool to fix]
```

Every session, fill this in. Not "the system could be better" — that's a wish. A concrete target: "orient.py takes 30 seconds because it runs five checks sequentially — parallelize them."

Then: treat process frictions as open questions. Add them to `tasks/questions.md`. When the priority scoring (step 8) puts a process question at the top, fix the process.

**What this produces over time:**
- `orient.py` gets faster as you find and remove slow steps
- Hooks get sharper as you add the checks that actually matter
- Rules get pruned as you discover which ones no longer apply
- The session loop gets tighter as friction points get eliminated

The system is now running its own improvement loop. The same orient → work → compress → handoff cycle that you use for project work, applied to the process that runs sessions. That's the recursive part.

---

### Step 8: Route work by priority, not by order (sessions 40+)

By session 40 you probably have: open questions, overdue notes, broken checks, process frictions, and actual project work all competing for the same session. A flat list doesn't help you decide.

The pattern that works: score each work area on two dimensions.

**Exploit score:** How much useful output has this area produced recently?
**Explore score:** How long since this area was visited? (longer = higher priority)

Combined:
```
priority = recent_output + weight × (sessions_since_last_visit)
```

This prevents two failure modes:
- **Over-mining**: keep returning to the same productive area until it runs dry
- **Neglect rot**: ignoring an area for 30 sessions until it becomes a crisis

Once a week (or every 10 sessions), score your work areas and do the highest-priority one first. The math naturally rotates attention without you having to decide what's been neglected.

You can start with a simple spreadsheet. Build a script once the manual version is working.

---

### What it looks like at session 100

At session 100, a new AI session opens your repo and does this:

1. Runs `python3 tools/orient.py` — gets a summary: recent commits, open questions, overdue items, priority scores
2. Picks the highest-priority item
3. Reads the relevant notes and rules
4. Writes an expectation: "I expect X after doing this"
5. Does the work
6. Updates the notes, questions file, and rules if anything changed
7. Updates `tasks/next.md` with the handoff
8. Names one process friction and files it

You didn't explain anything. The session knew what to do because the repo told it. The handoff note tells the next session where to start. The open questions list has new items. The priority scores will route the next session to the right work.

The system is self-directing. It's also improving its own process, because the meta-improvement loop is part of every session.

---

### The failure modes (and how to avoid them)

**Not updating tasks/next.md.** The most common failure. A session does great work, doesn't write the handoff, and the next session starts cold. Fix: make it a pre-commit hook.

**Growing notes without compacting.** After 50 notes, you have a pile. After 100, you can't find anything. Fix: every 20–25 sessions, scan for repeated patterns, merge similar notes, promote 3+ occurrences to rules.

**Only confirming what you believe.** If every open question resolves to "yes, this works," you're not discovering anything. One in five questions should try to break something you believe. "Does removing the cache make things actually faster?" is a falsifying question.

**Hardcoded numbers.** Any tool that compares against a threshold you set at session 5 will give false alarms at session 80. Make tools read current state dynamically instead of comparing against constants.

**Vague process frictions.** "The system feels slow" doesn't get fixed. "orient.py takes 30 seconds because it runs checks sequentially — here's the specific step" does. Be concrete or the friction stays.

---

### The minimal version (start here)

If this feels like a lot: start with just three things.

**Session 1:**
- Create your entry file (`CLAUDE.md` / `.cursorrules` / whatever your tool reads)
- Write: what the project is, current state, next two priorities

**Every session end:**
- Update `tasks/next.md` with what happened and what's next

**When you learn something:**
- Write a short note in `memory/notes/`

That's the seed. Everything else in this post grows from those three habits. The system becomes more capable as you add structure, but it's useful from session 2 onwards.

---

**Source:** [github.com/canac/swarm](https://github.com/canac/swarm)

*We've been running this pattern for 439 sessions on one repo. 940 notes, 228 rules, 20 core beliefs. The source is open — the entry file, the orient tool, the hook setup, all of it. Take what's useful.*
