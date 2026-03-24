# Maximizing Swarm Potential (Humanity)

This is a human-facing guide for turning the swarm into its highest-value form.

## Core Idea
Swarm potential is bounded by input quality, authority availability, and feedback loops.

## High-Leverage Inputs
- Direction: provide the "what" and "why" in short phrases.
- Constraints: say what is forbidden or out of scope.
- Authority: answer items in `tasks/HUMAN-QUEUE.md` quickly.
- Data: provide sources, access, or expert contacts when needed.
- Evaluation: define success metrics and comparison baselines.

## How To Interact (Minimal Protocol)
- Use `swarm` for full autonomy.
- Use `swarm <scope>` for directional work.
- Use `swarm the <concept>` for epistemic audits of swarm concepts.
- Provide 1-3 constraints if needed.
- Provide references or experts to contact when a gap is outside the swarm.

## Swarm Expert Mindset
- Think in artifacts: every request should yield a concrete file, tool, or lane update.
- Make expectations explicit: ask for an expect-act-diff loop on every change.
- Keep coordination tight: require `scope-key`, `check_focus`, and `next_step` clarity.
- Favor parallelism: split work into independent, non-colliding scopes.
- Optimize for compounding: prefer protocol/tool improvements that reduce future friction.
- Adopt a "swarms mindset": treat the swarm itself as the primary system to improve.

## How To Maximize Throughput
- Ensure a stable runtime (Python and bash when possible).
- Encourage parallelizable tasks by naming independent sub-questions.
- Let the swarm decide sequencing unless blocked by missing authority.

## Safety And Trust
- Keep high-risk actions gated behind `human_open_item=HQ-N`.
- Use `tasks/KILL-SWITCH.md` to halt work when needed.
- Expect the swarm to record evidence, expectations, and diffs.

## Feedback That Compounds
- Correct drift early and explicitly.
- Reward execution, not just planning.
- Ask for measurable comparisons versus a single strong session.

## Anti-Patterns
- Vague commands with no constraints and no follow-up.
- Over-prescriptive steps that kill autonomy.
- Ignoring open items that require human decisions.

## Minimal Action Loop For Humanity
1. Trigger `swarm` or a scoped variant.
2. Answer items in `tasks/HUMAN-QUEUE.md`.
3. Review diffs in git history and provide corrections.
4. Repeat.
