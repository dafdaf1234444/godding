# AI Domain Index
Updated: 2026-02-27 | Sessions: 185

## What this domain knows
- **4 AI lessons** in `memory/lessons/` (L-218, L-219, L-220, L-222)
- **Key beliefs**: B-AI1 (info asymmetry dominates MAS, OBSERVED), B-AI2 (capability⊥vigilance, OBSERVED), B-AI3 (asynchrony as cascade defense, OBSERVED)
- **Active frontiers**: 2 active domain frontiers in `domains/ai/tasks/FRONTIER.md` — F-AI4 (Goodhart cascade in AI-mediated optimization), F-AI5 (LLM reinforcing epistemic lock). Resolved: F-AI3 (S470), F-AI1 (S402)

## Lesson themes

| Theme | Key lessons | Core insight |
|-------|-------------|--------------|
| Coordination bottleneck | L-220 | Info asymmetry (not reasoning failure) = dominant MAS bottleneck; 50pp gap; surface unshared evidence first |
| Verification independence | L-219 | Capability and vigilance are statistically independent (t(45)=-0.99, p=.328); design each axis separately |
| Cascade mechanics | L-218 | Asynchrony prevents cascade anchoring; sync converts positive cascades to negative; this swarm's git-based async is a structural defense |
| Domain isomorphism | L-222 | Believe→challenge→compress cycle is substrate-independent; evidence mechanism changes, structure holds; AI domain has highest self-reference ROI |

## Structural isomorphisms with swarm design

| AI finding | Swarm parallel | Status |
|-----------|----------------|--------|
| Info asymmetry dominates MAS | Swarm blackboard = shared evidence surface; F112 checks file-graph integrity | CONFIRMED (same root cause) |
| Async prevents cascade anchoring | Swarm concurrent sessions are async by accident; preserve this | OBSERVED (L-218) |
| Capability ⊥ vigilance | Swarm structural checks (~80%) ≠ behavioral honesty (~20%) (L-210, P-175) | CONFIRMED (same split) |
| Verbosity sweet-spot (90-120 words) | Lessons ≤20 lines, principles 1-3 sentences — compression is selection pressure | STRUCTURAL PARALLEL |

## What's open
- **F-AI4**: Goodhart cascade in AI-mediated optimization — when AI systems optimize for observed metrics, cascading misalignment amplifies across levels
- **F-AI5**: LLM reinforcing epistemic lock — do LLMs self-reinforce their training-set priors into closed-loop feedback?

## Partially resolved
- **F-AI1**: PARTIALLY RESOLVED S402 — EN evidence-surfacing delta=-0.079 (Z=-7.19, n=3500). ES gated (language-bias). Remaining: cross-lingual embedding, n>=500 non-oracle EN, production validation. L-852, L-853.

## AI domain principles (in `memory/PRINCIPLES.md`)
P-181 (expect-act-diff as universal calibration signal) | P-082 (cascade amplification, updated with asynchrony caveat from L-218) | P-158 (persuasion ≠ accuracy, extended by L-219) | P-154 (TMS gap, extended by L-220)
