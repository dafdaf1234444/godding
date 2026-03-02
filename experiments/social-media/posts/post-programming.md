# r/programming — Post 4
Platform: Reddit | Subreddit: r/programming
Status: READY | Post Tuesday/Wednesday 8-10am ET for peak reach
Expected: 10-50 upvotes if it hits front page of sub; architecture discussion

---

## TITLE
We used git as the coordination layer for parallel AI agents — no message bus, no database, just commits

---

## BODY

We wanted multiple AI sessions to work on the same codebase simultaneously without stepping on each other. Instead of building a message bus or shared memory service, we leaned into what we already had: git.

Here's how it works.

**The coordination primitives:**

Everything is append-only or merge-safe:

```
tasks/NEXT.md        ← handoff note (one section per session, append-only)
tasks/SWARM-LANES.md ← coordination board (table rows, append-only)
memory/lessons/      ← one file per lesson (no conflicts)
memory/INDEX.md      ← session summary log (append-only rows)
```

When two sessions run simultaneously and both edit `SWARM-LANES.md`, they're both appending rows to a table. Git merges table appends cleanly. No conflict.

**The protocol:**

```
1. Orient: read NEXT.md and SWARM-LANES.md to see what's being worked on
2. Claim: append a row to SWARM-LANES.md with your intent
3. Act: do the work, add specific named files (not git add -A)
4. Compress: write a lesson if you learned something
5. Handoff: append a note to NEXT.md; commit [S<N>] what: why
```

Step 2 prevents two sessions from doing the same thing. If you show up and someone already claimed the work you were about to do, move on.

**What we learned from 300+ sessions:**

The session number prefix on commits (`[S153] hooks: add quick checks`) makes the history queryable in a way that pure git blame doesn't. You can `git log --oneline | grep "S15"` to see exactly what happened during sessions 150-159.

**The failure modes:**

- `git add -A` is dangerous when running on WSL with a Windows-side process also touching the repo. We found this out the hard way when a mass-deletion commit staged 729 file deletions silently. Rule: always add specific named files.
- Concurrent sessions can both pick up the same untracked file before either commits. Check `git log --oneline -- <file>` before committing new files.
- The `.git/index` can get corrupted under heavy concurrent use. Fix: `rm -f .git/index && git read-tree HEAD`.

**The surprising part:**

After 300 sessions, the repo is more organized than it started. Sessions that leave bad state create problems for sessions that follow — so the structure self-corrects. There's no enforcer; the incentive is built into the protocol.

The whole setup is open: [link]

Key files: `SWARM.md` (the protocol), `tools/maintenance.py` (surfaces what's due at session start), `tools/sync_state.py` (detects count drift before commit).
