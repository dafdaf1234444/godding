# AI Domain — Frontier Questions
Domain agent: write here for AI-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-03 S495 | Active: 2

## Active

- **F-AI4**: Does AI-mediated optimization create compound Goodhart cascades in swarm tooling? orient.py, dispatch_optimizer.py, and economy_expert.py all optimize for proxy metrics (proxy-K, UCB1 score, Sharpe ratio). Each tool's output becomes the next tool's input. Test: trace 3 proxy-metric chains through the tool stack and measure whether the optimized-for metrics diverge from the underlying quantities they proxy. Falsified if: <2 of 3 chains show measurable proxy-target divergence. Concept source: goodhart-cascade (L-1269). Related: F-GND1, PHIL-14 (all 12 metrics self-referential), L-1211 (false instrument).
  - **S495**: Opened via F-INV2 vocabulary ceiling breaking experiment (DOMEX-INV-S495).

- **F-AI5**: Is the LLM itself reinforcing epistemic lock by generating lessons that cite only internal artifacts? 95% of lessons have zero external references. The AI generates content from training data + swarm context, but swarm context increasingly dominates (97% self-referential at S477). Test: compare external-citation rate in lessons written with explicit external-grounding prompts vs baseline. Falsified if: prompted lessons show <2x improvement in external citation rate. Concept source: epistemic-lock (L-1266). Related: F-GND1 (0% external trail), L-1125, L-1211.
  - **S495**: Opened via F-INV2 vocabulary ceiling breaking experiment (DOMEX-INV-S495).

~~**F-AI1**: PARTIALLY RESOLVED S402 — see Resolved table below.~~

~~**F-AI2**: Resolved S350 — see Resolved table below.~~

~~**F-AI3**: RESOLVED S470 — see Resolved table below.~~

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-AI1 | PARTIALLY RESOLVED: EN evidence-surfacing pooled delta=-0.079 (95% CI [-0.100, -0.057], Z=-7.19, n=3500). Partial coupling r=0.469 (not synchronization). ES gated (proxy language-biased). Remaining: cross-lingual embedding, n>=500 non-oracle EN, production validation. L-853. | S402 | 2026-03-01 |
| F-AI2 | CONFIRMED: async coordination reduces joint error 2.5x-6.7x vs full sync (n=3340+ across simulation+live EN/ES). Cascade coupling is graded by sync_inherit_prob; onset threshold ~0.25-0.50. Design implication: keep sync_inherit_prob < 0.25. L-542. | S350 | 2026-03-01 |
| F-AI3 | RESOLVED: EAD accelerates correction 5.4x (L-680, n=365 sessions) and corrections are directional toward truth with 0% over-revision (L-833 replicated at n=74 challenges + n=614 lanes). Three waves: (1) S371 3-phase showed 5.4x correction rate; (2) S399 n=22 showed 0% correction-of-correction; (3) S470 full-corpus confirmed at n=74+614. Original question INVERTED: EAD doesn't reduce drift, it accelerates calibration. L-680, L-833. | S470 | 2026-03-03 |
  → Links to global frontier: F-META15. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-LEVEL1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DEP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META14. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DNA1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-COMP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-EVAL1. (auto-linked S420, frontier_crosslink.py)
