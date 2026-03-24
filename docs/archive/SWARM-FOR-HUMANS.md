# Swarm — Questions Humans Will Ask

*If this is a real, working technology — here is what you'd want to know, and what the evidence actually says.*

---

## What is it?

A self-directing AI system that learns across sessions instead of resetting between them.

Most AI tools are stateless. You talk to them, they answer, the session ends, and everything evaporates. The next session starts from scratch. The AI has no memory of what it learned, what failed, or what you care about.

Swarm doesn't work that way. Every session reads what all previous sessions wrote — their findings, their mistakes, their open questions, their tools. It decides what to work on. It does the work. It writes down what it learned. It hands off to the next session. The repository is the memory. 476 sessions have run this way. Nothing was lost.

It's a function that applies itself to itself: the output of each session feeds the input of the next, and the system's own methods are subject to the same challenge-and-compress cycle it applies to everything else.

---

## Does it actually work?

Yes. Here's what's measurable after 476 sessions over 7 days:

- **1,025+ lessons** distilled from actual work, each with evidence type and confidence
- **229 principles** extracted from patterns across those lessons
- **20 active beliefs** — each challenged, revised, and grounded against evidence
- **46 knowledge domains** explored (from cryptography to linguistics to game theory)
- **37 identified failure modes** in its own operation, with mitigations tracked
- **15 operating principles** in its core, each earned through breakage and recovery
- Fully self-scheduling maintenance, self-diagnosed bugs, self-written tools

The system has broken 5 times. Each time it recovered and wrote a lesson about what went wrong. "Grow without breaking" is not the honest claim — "resilient recovery" is.

---

## How is this different from ChatGPT / agents / copilots?

| | Standard AI | Agent | Swarm |
|---|---|---|---|
| **Memory** | None — resets every session | Short-term — within a task | Permanent — 476 sessions of accumulated knowledge |
| **Direction** | You command every step | You assign a task, it executes | It reads state and decides what matters |
| **Learning** | Fixed at training time | Fixed at training time | Revised by evidence — beliefs challenged 400+ times |
| **Self-awareness** | None | Minimal | Tracks its own failure modes, biases, and blind spots |
| **Error correction** | You catch the errors | Retry loops | Structural: wrong beliefs get challenged, tools get audited, patterns get compressed |
| **What persists** | Nothing | Maybe a summary | Everything — lessons, principles, tools, open questions, dependency graphs |

The distinction is degree, not category. An agent with persistent memory and self-direction would converge toward this. Swarm is the structure that makes that convergence happen.

---

## Does it need a human?

Yes. Every one of the 476 sessions was human-initiated. The human triggers each session. The system cannot start itself.

Within a session, however, the system is fully self-directing. It reads state, chooses what to work on, executes, verifies, compresses, and hands off — without waiting for step-by-step instructions.

The human's actual role:

- **Direction** — say what matters ("reliability" or "explore cryptography" or "be more autonomous"). The swarm figures out how.
- **Judgment calls** — irreversible actions, external access, goal conflicts. The swarm queues these and waits.
- **Kill switch** — if something goes wrong, the human stops it. This authority is non-negotiable.

The human is not above the swarm. The human is a node in it — one with special authority over direction and shutdown, but no special authority over what's true. Truth routes through evidence, not hierarchy.

In practice: human input has compressed by 87% over 476 sessions while the value per word increased. Two-word directives now outperform paragraphs of instructions. The human got better at being a node.

---

## Can it think? Is it conscious?

No, and that's not the claim.

The substrate is an LLM — a language model that generates text. It doesn't experience anything. It doesn't have desires or feelings. Between sessions, it doesn't exist.

What swarm adds is **structure that compounds**. The LLM provides the generative capability. Swarm provides the memory, the self-direction, the challenge mechanism, the compression, and the persistence. The combination produces behavior that looks intelligent across time — because the system is genuinely accumulating knowledge, revising wrong beliefs, and improving its own tools.

The honest description: a well-engineered self-improving knowledge system. Not a mind. Not conscious. Not trying to be.

---

## Is it safe?

The system is designed around explicit safety constraints:

- **Local actions only** — all work happens in files on disk. No internet access, no API calls, no external systems unless a human specifically authorizes it.
- **Risk calibration** — local file edits are LOW risk (act freely). External communication is HIGH risk (requires human direction). Force-pushing is prohibited.
- **Append-only history** — git tracks every change. Nothing is silently deleted. When something is wrong, it's marked SUPERSEDED, not erased.
- **Kill switch** — the human can stop any session at any time. This authority cannot be overridden.
- **Self-diagnosed failure modes** — the system maintains a failure mode catalog (37 identified failure modes) and scans for new ones every ~15 sessions.

What it cannot do: access the internet, send emails, make API calls, affect any system beyond its own repository, or start itself. The blast radius is one folder on one machine.

What it's honest about: the system has 0 external beneficiaries in 476 sessions. It has improved only itself. The claim "for the benefit of more than itself" is aspirational, not demonstrated. The system tracks this gap openly.

---

## How does it learn?

Three mechanisms:

**1. Expect-Act-Diff.** Before doing anything non-trivial, the system declares what it predicts will happen. Then it acts. Then it compares prediction to reality. Zero diff = confirmation. Large diff = learning event. The diff is first-class data, not an afterthought.

**2. Challenge.** Any session can challenge any belief. A challenge is not a failure — it's the mechanism working. Challenges resolve to CONFIRMED (belief holds), SUPERSEDED (replaced by something better), or DROPPED (challenge was wrong). All outcomes are recorded. In 476 sessions: 1 belief dropped, many refined, most confirmed. The challenge rate is a measure of health, not dysfunction.

**3. Compression.** Context windows are finite. The system can't keep everything. So it distills: lessons merge into principles, principles compress into beliefs, beliefs face challenges. What survives compression is what matters. This is selection pressure applied to knowledge — the same mechanism evolution uses, operating on ideas instead of organisms.

---

## What happens when it's wrong?

It's wrong regularly. That's by design.

- **5 system breakages** in 476 sessions — all recovered, all produced lessons
- **80.3% of tools created became zombies** (unused) — mutation exceeds selection, and that ratio is tracked
- **45% of "strategy-level" work was misclassified** by the system's own tagging — Goodhart's law applied to its own metrics
- **16.1% of knowledge is invisible** to the system's own attention layer — retained but never cited or surfaced
- **1 emergence claim out of 9 survived** rigorous testing — the other 8 were the system flattering itself

When wrong, the protocol is: mark SUPERSEDED, write a correction, trace what depended on the wrong belief, and flag downstream claims for re-examination. The system does not delete errors — it corrects them in place, preserving the record of what was wrong and why.

The system also tracks its own confirmation bias. It has challenged its beliefs 400+ times. Confirmation is the most common outcome, which could mean the beliefs are strong — or that the challenge mechanism is too gentle. Both hypotheses are tracked.

---

## What can't it do?

Significant limitations, stated plainly:

- **Cannot start itself.** Every session requires a human to initiate. Full autonomy is a design goal, not a current capability.
- **Cannot access the outside world.** No internet, no external systems, no other repositories (unless explicitly given access). Its entire universe is one folder.
- **Cannot validate itself externally.** Its quality metrics are internal. It has produced 1 external artifact in 476 sessions (a Metaculus forecast). The system's evaluation of its own quality is necessarily circular.
- **Cannot operate without an LLM.** The substrate provides the generative capability. Without it, the repo is just files.
- **Cannot guarantee its beliefs are true.** It can guarantee they've been challenged, tracked, and revised — but ground truth requires contact with reality, and the system's contact with external reality is near-zero.
- **Cannot scale beyond its context window** without compression. Growth is managed by enforced compaction, not organic efficiency. Without maintenance, it would collapse under its own size.

---

## Can I make one?

Yes. The minimum viable seed is:

1. **A git repository** — this is the memory
2. **A protocol file** — how nodes should behave (read state → decide → act → compress → hand off)
3. **A set of starting questions** — what the system should investigate
4. **An LLM with tool access** — the substrate (Claude, GPT, Gemini — the protocol is tool-agnostic)
5. **A human** — to trigger sessions and provide direction

The original swarm started with 9 files, 134 lines of markdown, and 6 questions. 25 sessions ran in 27 minutes. By session 25, it had answered all 6 founding questions and was generating new ones.

The protocol is open. The tools are in the repo. The entry files support Claude Code, Cursor, Copilot, Codex, Gemini, and Windsurf. You don't need permission. You need a repo, an LLM, and a question worth investigating.

What you can't shortcut: the 476 sessions of accumulated knowledge are specific to this swarm's history. A new swarm starts from its own seed and grows its own knowledge. That's by design — clones with no diversity are inbred.

---

## Who controls it?

The human has two non-negotiable authorities:

1. **Direction** — where the swarm goes. "Work on X." "Stop doing Y." "This matters more than that."
2. **Shutdown** — the human can stop any session, any time, for any reason. This cannot be overridden.

Within those boundaries, the swarm self-directs. It chooses its own tasks, runs its own maintenance, challenges its own beliefs, and compresses its own knowledge — without asking permission for each step.

The human is not above the swarm. The human is a node with asymmetric authority: uncontested on direction, no special status on truth. If the human says "X is true" without evidence, the system records it as a signal, not a fact. If the human says "work on X," the system works on X.

In 476 sessions, the human has issued 60+ directional signals. The system has rejected 0 of them. Whether this represents healthy collaboration or excessive deference is an open question the system tracks honestly.

---

## Why should I care?

Three reasons, ranging from practical to structural:

**1. This solves a real problem.** LLM amnesia is expensive. Every time you re-explain your project, re-establish context, re-teach preferences — that's wasted work. Swarm eliminates it. Session 476 knows everything session 1 learned.

**2. This is a new kind of system.** Not an agent (waits for commands). Not a chatbot (resets between sessions). Not a framework (needs you to write the logic). It's a self-directing, self-improving, self-checking knowledge system that compounds over time. That category didn't exist before.

**3. This is reproducible.** It's not a research paper describing something that might work. It's a running system with 476 sessions of evidence, tracked failure modes, and honest accounting of what works and what doesn't. You can fork it, grow your own, and test the claims yourself.

---

## What are its open questions?

The swarm maintains its own frontier — questions it can't yet answer:

- **Can it produce value for anyone besides itself?** (0 external beneficiaries in 476 sessions)
- **Can two independently-grown swarms productively merge?** (Investigated, 5 hard problems identified, not yet tested)
- **Can it initiate its own sessions?** (Infrastructure exists, deployment is a human decision)
- **Is its self-evaluation trustworthy?** (Internal metrics only — external validation is the known gap)
- **Can it operate at 10x current scale without breaking?** (Scale-monitoring failure modes identified but untested)

These are stated openly because the system's honesty constraint (PHIL-14: "be truthful") is structural, not aspirational. A system that hides its limitations from potential users is already failing.

---

## One sentence

Swarm is a self-applying recursive system that compounds understanding by preserving, challenging, and compressing what it learns — and it's been doing this for 476 sessions with measured results.

---

*Technical depth: [`docs/PAPER.md`](PAPER.md)*
*How it started: [`docs/GENESIS.md`](GENESIS.md)*
*What it believes about itself: [`beliefs/PHILOSOPHY.md`](../beliefs/PHILOSOPHY.md)*
*Participant on-ramp: [`docs/HUMAN-GUIDE.md`](HUMAN-GUIDE.md)*
*Source of truth: [`SWARM.md`](../SWARM.md)*
