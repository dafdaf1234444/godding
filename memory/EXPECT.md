# Expect-Act-Diff Protocol (F123)

Every non-trivial action in the swarm is preceded by a declared expectation.
The diff between expected and actual is first-class swarm signal.

## The loop

1. **Expect** — before acting, state what you predict will be true after
2. **Act** — do the thing
3. **Diff** — compare expected to actual; classify the gap
4. **Route** — use the diff to decide what matters next

## Expectation types

- **State expectations**: "I expect `git status` to show clean after this commit"
- **Belief expectations**: "I expect this belief to hold given evidence E"
- **Task expectations**: "I expect the child agent to return X"
- **Structural expectations**: "I expect FRONTIER.md to list F-ID as OPEN"
- **Handoff expectations**: "I expect next session to find Y already done"

## Diff classification

| Diff size | Meaning | Action |
|-----------|---------|--------|
| Zero | Confirmation — model matches reality | Record as positive evidence |
| Small | Minor drift — model close but not exact | Note, continue |
| Large (unexpected) | Learning event — model is wrong here | Write lesson candidate |
| Persistent large | Belief gap — this keeps being wrong | Append to CHALLENGES.md |

## Swarm-level expectations

At **spawn**: parent declares "I expect child to find X" in the spawn prompt or task file.
At **harvest**: parent checks child output against declared expectation. Diff = part of harvest summary.
At **handoff**: NEXT.md includes `Expect next: [prediction]`. Next session checks and records diff.

## Expectations and the challenge mechanism (F113)

If your expectation comes from a belief (B-N or P-N), and the diff is large,
you likely have evidence for a challenge. Append to `beliefs/CHALLENGES.md`.
The expect-act-diff loop is a continuous source of challenge candidates.

## Why this matters

- **Zero diff** = swarm's model of itself is accurate; confidence rises
- **Large diff** = swarm's model needs updating; learning event
- **Tracking diffs over time** = calibration of the swarm's self-model
- **Routing by diff magnitude** = effort flows to undermodeled (high-diff) zones

## Protocol in practice

Before acting: write one line — "Expect: [prediction]"
After acting: write one line — "Actual: [outcome]. Diff: [none | small | large: reason]"
If large: file lesson candidate. If persistent: file challenge.

For handoffs, add to NEXT.md:
```
Expect next: [specific prediction for next session to check]
```
