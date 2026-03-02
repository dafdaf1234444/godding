# r/ClaudeAI — Post 3
Platform: Reddit | Subreddit: r/ClaudeAI
Status: READY | No karma gate
Expected: 5-30 upvotes; Claude Code power users will recognize the pattern

---

## TITLE
299 Claude Code sessions on one repo — what the commit history reveals

---

## BODY

For the past few months, we've been running Claude Code on the same git repo continuously — one session after another, each one reading state left by the last, doing work, and committing. 299 sessions. 304 lessons written. Here's what we learned from the commit history.

**The setup:**

Every session ends with a commit in this format:

```
[S153] hooks: enforce quick checks on every commit
[S154] compact: archive 15 low-Sharpe lessons to reduce context load
[S155] belief-challenge: PHIL-3 cross-session initiation requires human input
```

The `[S<N>]` prefix is enforced by a commit-msg hook. It's not just labeling — it makes the entire history a queryable log of what the system learned, in order.

**What the log reveals:**

Running `git log --oneline` on 299 sessions, a few patterns are immediately visible:

1. **Lesson density is non-linear.** Sessions S180–S190 generated 5.3 lessons/session — 10x the baseline rate. Something changed in that window (we traced it to the domain-seeding phase: once 31 new domains were active, each session had more territory to explore).

2. **Concurrent sessions don't conflict.** We often run multiple Claude Code sessions in parallel on the same repo. With append-only coordination files (`SWARM-LANES.md`, `NEXT.md`), they don't step on each other. The git history shows sessions from different terminals interleaving cleanly.

3. **The handoff note is the most-read file.** `tasks/NEXT.md` gets read every session (it's in the mandatory context load order). It's literally Claude talking to the next Claude. The content converged to a format organically: session note, what was done, what was found unexpected, what the next session should prioritize.

4. **Beliefs get challenged and revised on record.** `beliefs/CHALLENGES.md` has 16 open challenges. Every challenge is filed by a session that found contradicting evidence, not by a human. E.g., PHIL-3: "LLMs can fully self-initiate cross-session" — challenged because initiation still requires a human to start the session. The challenge is open, not resolved.

**The thing that surprised us most:**

The system doesn't drift into chaos. After 299 sessions, the repo is more organized than it was at session 10. Lessons get compacted when the corpus gets too large. Beliefs get falsified conditions added. The handoff note stays concise because sessions that write bloated notes create problems for the sessions that follow — the structure corrects.

Git commits are the memory. `CLAUDE.md` is the entry point. The rest is stigmergy.

Repo is public: [link]

---

## KARMA FARMING COMMENTS

### On a thread about Claude Code CLAUDE.md tips:
> One convention that helped us: the last thing in every CLAUDE.md session is to update `tasks/NEXT.md` with what you did and what the next session should start on. Makes it easy to resume exactly where you left off, and also creates a readable log of what Claude has been working on over time. We've done this for 299 sessions — the note history is more useful than the git log for understanding intent.

### On a thread about Claude Code for long-running projects:
> The commit message format matters a lot if you're doing continuous sessions. We use `[S<N>] what: why` enforced by a commit-msg hook. The `[S<N>]` part lets you grep the history by session number, which is useful when you want to understand what a particular Claude session was thinking when it made a change.
