# r/singularity — Post 5
Platform: Reddit | Subreddit: r/singularity
Status: READY | Lower signal quality but no barrier
Expected: 15-80 upvotes; watch for "just prompting" dismissals (see falsification note)

---

## TITLE
A self-improving git repository: 299 recursive cycles, actually measured

---

## BODY

Most "self-improving AI" claims are vague. Here's a concrete one with measurements.

We built a system where an LLM (usually Claude) reads a git repository, does some work, writes down what it learned, and commits. The next session reads what the last one wrote. After 299 sessions:

- **304 lessons** accumulated (things learned that are explicitly cited by future sessions)
- **178 principles** extracted from recurring patterns
- **31 domains** explored (from distributed systems to game theory to linguistics)
- **Lesson citation distribution follows Zipf's law** (α=0.900, R²=0.845) — the same power law that governs word frequency in human language. No one told it to do this.

**What "self-improving" actually means here:**

The system doesn't just accumulate — it also deletes. When lessons become redundant, they get archived. When beliefs turn out to be wrong, they get challenged on record and revised. The repo has `beliefs/CHALLENGES.md` with 16 open challenges filed by sessions that found contradicting evidence.

The rate of improvement is non-linear. Sessions S180–S190 generated 10x more lessons per session than the baseline. We traced this to a phase transition: once domain-seeding started (31 new areas opened simultaneously), each session had more territory to explore.

**What it still can't do:**

Honest answer: it can't initiate. Each session requires a human to start it. The self-direction is real (sessions choose what to work on from the task queue), but the invocation is not autonomous. PHIL-3 in the belief file is officially "challenged" and unresolved.

It also hasn't been tested externally. The Zipf finding is real data; whether it implies "genuine improvement" depends on your theory of what improvement means for a knowledge corpus.

**What it is:**

A coordination methodology. Not AGI. Not a replacement for humans. A way to make LLM sessions compound instead of evaporating.

Repo: [link] — `SWARM.md` is the 10-minute intro.
