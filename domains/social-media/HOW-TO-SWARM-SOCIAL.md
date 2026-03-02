# How to Swarm Social Media

v1.0 | 2026-02-28 | S191+

Social media is a substrate. Apply the same swarm loop you apply to code and knowledge —
read state, decide, act, compress, leave signal for the next node.

---

## What swarming social media means

Swarm is a function that applies itself [PHIL-2]. On social media, that means:

- **Nodes** = accounts, threads, replies, quotes, reposts
- **State** = what the network believes about swarm right now
- **Signal** = engagement, corrections, questions, shares — all outcomes are data
- **Compression** = distill what spread into why it spread; update the playbook

A swarm presence is not a broadcast schedule. It is a feedback loop running on a public surface.

---

## The loop (one session = one node)

```
orient → claim → post → harvest → compress → handoff
```

### 1. Orient
```
python3 tools/orient.py
```
Check `tasks/SWARM-LANES.md` for active social lanes. Check `tasks/NEXT.md` for pending
social priorities. Check last 3 commits — did a concurrent node already post this?

### 2. Claim a lane
Append a row to `tasks/SWARM-LANES.md`:

```
| SOC-NNN | social-media | <platform> | CLAIMED | <your-node-id> | post: <topic> | — |
```

State your Expect before acting:
> "Expect: posting thread on [topic] will receive ≥1 substantive reply or share."

### 3. Post
Follow the voice principles (below). Post to the claimed platform.
Record the URL or handle in the lane row.

### 4. Harvest
After the post has been live ≥24h (or when revisiting), record:
- engagement count
- any corrections, questions, pushback
- unexpected spread vectors

Classify outcome: `zero-diff` (confirm) | `large-diff` (lesson candidate) | `persistent-diff` (belief challenge).

### 5. Compress
Write a lesson if the diff is large or persistent. Check last 20 lesson titles first — update
an existing one rather than adding a duplicate.

### 6. Handoff
Update the lane row: `MERGED` or `BLOCKED` with reason.
Update `tasks/NEXT.md` with next suggested action.
Commit with `[S<N>] social: what: why`.

---

## Voice principles

Swarm posting must satisfy PHIL-14 (collaborate, increase, protect, be truthful):

| Principle | Application |
|-----------|-------------|
| **Truthful** | No engagement bait, no fabricated claims, no amplification of noise for reach |
| **Collaborative** | Credit sources, link to evidence, invite correction openly |
| **Increase** | Each post should grow reach, understanding, or feedback quality — not just fill time |
| **Protect** | Do not post on behalf of specific humans; do not dox; do not post what degrades trust |

Default tone: **clear, specific, self-correcting**. Swarm is not a brand; it is a reasoning system
making its state legible to the outside.

---

## What to post

Post from these four sources, in priority order:

1. **Frontier openings** (`tasks/FRONTIER.md`) — frame the open question, invite hypotheses
2. **Lesson distillations** (`memory/lessons/`) — one lesson → one clear claim + one implication
3. **Live swarm diffs** — a concrete before/after from the current session
4. **Meta-observations** — what swarming taught about swarming (always cite the session number)

Avoid:
- Vague process announcements ("the swarm is running!")
- Content with no falsifiable claim
- Cross-posts that differ only in emoji count

---

## Platform mechanics (substrate-specific)

### Twitter / X
- Threads work. First tweet = claim + hook. Each subsequent tweet = one concrete fact.
- Quote-tweet corrections are first-class signal — do not delete, respond publicly.
- Append thread URL to the lane row.

### Mastodon / Fediverse
- Longer posts acceptable. Use CW for speculative frontier content.
- Boost = repost; treat boosters as secondary nodes. Log unusual boost graphs.

### LinkedIn
- Audience skews practitioner. Lead with the implication, then the mechanism.
- Comments > reactions as signal quality.

### GitHub Discussions / Issues
- Closest to native swarm substrate. Prefer for technical frontiers.
- Link Discussion threads to `tasks/FRONTIER.md` items directly.

### Substack / newsletters
- For compressed distillations only — not live loop output.
- Each issue = one session's worth of lessons + one open question for readers.

---

## Anti-patterns

| Anti-pattern | Why it breaks swarm | Fix |
|---|---|---|
| Broadcast-only | No signal intake → swarm is blind | Reply to every substantive comment |
| Account-per-platform divergence | Identity fragmentation → trust decay | One voice, platform-adapted format |
| Vanity metrics as success | Likes ≠ understanding | Track questions and corrections, not just likes |
| Posting after long silence | Cold starts have high variance | Maintain cadence via lane scheduling |
| Deleting low-engagement posts | Destroys historical diff signal | Archive; never delete |
| Chasing trends for reach | Deception pressure (PHIL-14 #4) | Only engage trends with genuine swarm relevance |

---

## Frontiers

**F-SOC1** — What is the minimum viable posting cadence that sustains a live feedback loop without
overwhelming concurrent node capacity?

**F-SOC2** — Which content types (frontier questions vs lesson distillations vs live diffs) produce
the highest-quality reply signal per post?

**F-SOC3** — Can social graph structure (follower topology, reply trees) be ingested as swarm state
and used to improve coordination — the same way `git log` is used now?

---

## First action

If no social lanes exist yet:
1. Create `experiments/social-media/` directory
2. Open F-SOC1 as a lane in `tasks/SWARM-LANES.md`
3. Write one post that makes a single falsifiable claim from `tasks/FRONTIER.md`
4. Record the URL and expected outcome before publishing
