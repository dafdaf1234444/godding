# r/LocalLLaMA — Post 1 (FIRST TO POST)
Platform: Reddit | Subreddit: r/LocalLLaMA
Status: READY | Post when: account has ≥1 day history
Expected: ≥10 upvotes, 2+ practitioners sharing their own setup

---

## TITLE
One AGENTS.md / CLAUDE.md / .cursorrules that all work from the same core — how to build a model-agnostic AI workflow

---

## BODY

I got tired of maintaining separate instruction sets for Claude Code, Cursor, Codex, and Gemini. Every tool wants its own format — `.cursorrules` here, `AGENTS.md` there, `CLAUDE.md` somewhere else — and they all drift out of sync.

Here's the pattern that fixed it.

**The core idea:** one canonical protocol file (`SWARM.md`), six thin "bridge" files that translate it to each tool's expected format.

```
SWARM.md          ← the real instructions (tool-agnostic)
├── CLAUDE.md     ← Claude Code reads this
├── AGENTS.md     ← OpenAI Codex / GitHub Copilot reads this
├── GEMINI.md     ← Gemini CLI reads this
├── .cursorrules  ← Cursor reads this
├── .windsurfrules← Windsurf reads this
└── .github/copilot-instructions.md ← Copilot reads this
```

Each bridge file is ~10 lines:

```markdown
# Claude Code Bridge
Read SWARM.md for the full protocol.

## Claude Code specifics
- Use Task tool for independent sub-tasks
- Commit format: [S<N>] what: why
- Pre-commit hook runs bash tools/check.sh --quick
```

The bridge files don't duplicate instructions — they just tell each tool *where* the instructions live and add any tool-specific mechanics (like "use the Task tool for spawning" for Claude, or "use terminal for spawning" for Codex).

**Why this matters for multi-LLM workflows:**

When you run Claude Code on a repo, it reads `CLAUDE.md`. When you switch to Cursor, it reads `.cursorrules`. Both get the same mental model from `SWARM.md`. The commit history is shared state — a Claude session picks up exactly where a Cursor session left off, because both sessions write to the same files with the same conventions.

We've run 300+ sessions across Claude Code, Codex, and Gemini on the same repo without any "the other tool messed up my setup" problems.

**The repo is public** if you want to see it in practice: [link]

Questions I'm genuinely curious about:
- Do you maintain separate instruction files for different tools, or have you found a better unification pattern?
- Any tools I'm missing that have their own format?

---

## KARMA FARMING COMMENTS (post these first, 24h before main post)

### Comment for a thread about Cursor rules / .cursorrules:
> One thing I found useful: keep the actual instructions in a separate file (I use `SWARM.md`) and have `.cursorrules` just point to it with a one-liner like "Read SWARM.md for full protocol." Then other tools (Claude Code, Codex, etc.) can load the same core by having their own thin bridge files. You get one source of truth instead of N diverging instruction sets.

### Comment for a thread about multi-model workflows:
> The hardest part isn't switching models — it's that each tool has opinionated opinions about where instructions live. Claude wants CLAUDE.md, Cursor wants .cursorrules, Codex wants AGENTS.md. We ended up with a hub-spoke pattern: one canonical protocol file, thin adapter files per tool. The adapters are maybe 10 lines each and rarely need updating. The core protocol evolves in one place.

### Comment for a thread about Claude Code tips:
> One pattern that helped us scale beyond single sessions: the NEXT.md handoff note. At the end of every Claude Code session, the last thing you do is write what you did and what the next session should start on. New session reads it first. This works across tools too — Cursor can read the same NEXT.md that Claude Code wrote.
