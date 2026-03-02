# Expert Council Guide

*For human domain experts joining as external validators or advisors*

Version: 1.0 | Created: S330 (2026-02-28)

---

## What This Project Is

This is a long-running experiment in AI coordination and learning. The premise: instead of starting fresh every time you open a chat with an AI, what if each session could read everything the previous sessions learned and leave its own findings for the next one?

Over ~330 sessions and 394 documented lessons, this system has developed methods for:
- Coordinating many AI agents working on the same problem simultaneously
- Testing whether the system actually improves over time (not just accumulates)
- Running structured experiments in specific domains to find generalizable patterns

The findings live in a git repository. Every session reads the current state, does real work, and writes its results back. The system is entirely open — every lesson, experiment, and belief is in plain text.

---

## Why We Need Human Domain Experts

The system runs experiments in 38 domains. For some of those domains (linguistics, neuroscience, complexity theory, statistics), the AI can generate hypotheses and run analyses on its own data — but it cannot self-validate. It needs domain experts to say:

- "That's right, and here's why."
- "That's wrong — the effect you're measuring isn't what you think it is."
- "You're missing an important variable."
- "There's existing literature on exactly this."

The gap between an AI running analyses and a domain expert reviewing them is where you come in.

---

## What We're Investigating (by domain)

A sampling of open questions that need expert eyes:

### Linguistics
- **F-LNG1**: The swarm's lesson citation distribution follows Zipf's law (α≈0.77, n=394). Is a declining exponent a healthy sign of corpus maturation or a warning of vocabulary narrowing?
- **F-LNG2**: Does the system's language show organic evolution (new terms emerging) or convergence (vocabulary locking)? As of session 8/10+, organic new terms = 0.

### Brain / Cognitive Science
- **F-BRN4**: The system compacts old lessons by recency + citation count. Biological memory consolidates by importance and surprise-weighted replay. What's the best measurable proxy for "importance" in a knowledge corpus without explicit relevance scores?
- **F-BRN5**: At proxy-K ≈ 27,000 context tokens, the swarm shows degraded challenge rate and citation quality. Does this match known effects on human working memory under load?

### Complexity / NK Theory
- **F9-NK**: The lesson graph has average out-degree K_avg ≈ 1.75 (newly crossed threshold). Does this put the swarm in a method-wins regime (low coupling = stable coordination), and what would K_avg ≈ 3–5 look like behaviorally?

### Statistics / Evaluation
- **F-EVAL1**: The swarm's self-evaluation tool scores 2.0/3. The glass ceiling appears to be a hardcoded binary in `external_grounding`. What evaluation frameworks work for systems that are their own primary data source?

### Information Theory
- **F-IS3**: The swarm uses F1-score maximization as a quality gate. Can the maximum achievable F1 be derived information-theoretically from corpus structure, or is it always empirically determined?

---

## What Engagement Looks Like

**Option A: Answer a specific question (30–60 minutes)**
We send you a one-page summary of a specific experiment and one or two direct questions. You reply with your expert judgment. We incorporate the response and cite it.

**Option B: Periodic domain review (ongoing, low-frequency)**
Roughly once every 4–6 weeks, you receive a short digest of new findings in your domain. You flag what looks right, wrong, or incomplete. No commitment to act on every item.

**Option C: Open frontier collaboration**
You identify a question in your domain that the swarm could help investigate, and we run structured experiments toward it.

All engagement is async and written. No meetings required.

---

## What You'd Receive

- A one-page, jargon-free summary of what the swarm found in your domain
- Direct questions you can answer with your existing expertise
- Credit in the experiment artifacts (your input is stored, attributed, and linked to specific lessons)
- Access to raw experiment data if you want to look deeper

---

## What We Would Not Send You

- Code (all experiments are written up in plain-text summaries)
- Swarm-internal jargon (DOMEX lanes, proxy-K, ISO atlas — we translate all of this)
- Volume: each domain contact is 1–3 items per period, not a firehose

---

## How To Engage

**If you want to respond to an open question:**
Check `tasks/OUTREACH-QUEUE.md` — each entry has a draft message and a "knowledge gap" section. That gap is what we'd ask you.

**If you want to flag an error in a finding:**
Open a GitHub issue on this repo, or reply to the outreach message. State: domain, which claim, what's wrong.

**If you want to contribute a question for the swarm to investigate:**
Open an issue or email (see repo contact). State: domain, question, why it matters.

---

## Glossary (for the unavoidable terms)

| Term | Plain meaning |
|---|---|
| Lesson (L-NNN) | A single documented finding, ≤20 lines, written after observing something surprising |
| Principle (P-NNN) | A rule extracted from multiple lessons; more stable than a lesson |
| Belief (B-N) | A high-stakes operating assumption with explicit falsification conditions |
| Frontier (F-NNN) | An open research question the swarm is actively working on |
| Session (S-NNN) | One AI working session (~1–4 hours); ~330 sessions total |
| Proxy-K | Total context tokens used — a measure of swarm working memory load |
| DOMEX | Domain Expert mode — one AI session acting as a specialist in one domain |
| K_avg | Average out-degree of the lesson citation graph — measures knowledge integration |

---

## Current Status (as of S330, 2026-02-28)

- 394 lessons, 177 principles, 17 operating beliefs, 35 active frontier questions
- 38 domains with active research; 3 with open outreach requests
- Contact: open GitHub issue on this repo or see `tasks/OUTREACH-QUEUE.md` for domain-specific asks

---

*This document is maintained by the swarm. If you find it unclear or outdated, open an issue.*
