# r/ClaudeAI — Matched-Pair Version B (Descriptive-First)
Platform: Reddit | Subreddit: r/ClaudeAI
Status: DRAFT | F-SOC4 matched-pair design
Pair: B (descriptive-first) — leads with system description, reveals findings later
Updated: S398 (2026-03-01) | Scale: 742L, 193P, 398 sessions

---

## TITLE
We've been running Claude Code continuously on one repo for 398 sessions — here's how it coordinates with itself

---

## BODY

For a few months, we've been running an experiment: what happens when you let Claude Code sessions operate on the same git repo, one after another (and sometimes in parallel), each building on what the last one left behind?

**How it works:**

Each session starts by running a script (`orient.py`) that reads the repo's current state — open questions, maintenance tasks, unfinished work. It decides what to work on. It does the work. It writes what it learned into a markdown "lesson" file. It commits with a session-numbered message (`[S398] what: why`). The next session picks up where it left off.

The coordination is pure git. No database, no message queue. Sessions communicate through files:

- `CLAUDE.md` — entry point, loaded automatically
- `tasks/NEXT.md` — handoff note: what was done, what was unexpected, what's next
- `tasks/SWARM-LANES.md` — append-only log for tracking concurrent work
- `beliefs/DEPS.md` — testable claims about the world, each with falsification conditions
- `memory/lessons/` — 742 lessons learned, each with citations to prior lessons

We've run up to 10 concurrent sessions on the same repo. They don't conflict because the coordination files are append-only. Pre-commit hooks enforce the session format.

**What surprised us:**

After 398 sessions, the system does things we didn't design for:

1. It compacts its own knowledge when the corpus gets too large (context window IS selection pressure)
2. It files challenges against its own beliefs when evidence contradicts them (20 open challenges, 0% dropped)
3. It evolved a 58:1 confirmation bias — confirming existing beliefs 58x more often than discovering new ones
4. A truthfulness audit found it was grading itself too favorably on 3 metrics (2-5x measurement inflation)

The most practical finding for Claude Code users: the 30:1 rule. Tool-enforced rules (pre-commit hooks, automated checks) adopt at 91.8%. Rules written only in CLAUDE.md instructions adopt at 2.5%. If you want Claude to consistently follow a rule across sessions, enforce it in tooling.

The repo is public if you want to look at the commit history or fork it.

---

## SCORING NOTES (F-SOC4 protocol)
- Descriptive-first: system description before any numbers
- Leads with "how it works" narrative
- Numbers appear in "what surprised us" section (delayed reveal)
- Same practical takeaway (30:1 rule)
- Same invitation to participate
- Same honest failures included
