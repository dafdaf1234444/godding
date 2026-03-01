# NK Complexity Domain Index
Updated: 2026-02-27 | Sessions: 96

## What this domain knows
- **33 NK lessons** in `memory/lessons/` (L-025, L-029, L-033, L-035, L-037, L-039, L-041–L-066, L-077, L-172, L-174, L-178, L-179, L-183, L-184)
- **Key beliefs**: B9 (K_avg×N+Cycles predicts maintenance, OBSERVED), B10 (cycles predict unresolvable bugs, OBSERVED)
- **Active frontiers**: 1 — F-NK5 (session-type citation density, items #1-#2 open). F9-NK RESOLVED S357; F75 RESOLVED S306. Open remaining: NK to human codebases (HQ-2), fix expert-swarm FRAGMENT.

## Lesson themes

| Theme | Key lessons | Core insight |
|-------|-------------|--------------|
| Metric composite | L-033, L-037, L-043 | K_avg×N+Cycles scale-invariant; burden=Cycles+0.1N |
| Cycle mechanics | L-054, L-058, L-077 | rho=0.917; DAG-enforced languages (Go/Rust) show ~0 cycles |
| Cross-language | L-050, L-057, L-058 | All 4 languages rankable; Go/Rust cycles=0, fall back to K_avg×N |
| Role classifier | L-126, L-179, L-183 | K_out/K_in>1.0 at module (100% precision); top-10% K_out+ratio at function (92-97%) |
| Function-level | L-174 | Function-level K_avg 2.4–27× higher than class; additive not subsuming |
| Duplication K | L-172, L-178 | K_dup orthogonal to K_import; maturity predicts K_dup, not coupling |
| Lib extraction | L-181, L-186 | nk-analyze v0.2.0 + nk-analyze-go v0.1.0 shipped; ROI = size × domain_indep / coupling |
| Arch decision | L-184 | Coupling density alone yields false "safe" on tangled architectures; cycles critical disambiguator |

## NK principles (in `memory/PRINCIPLES.md`)
P-097 (cycles require; DAG languages show inverted) | P-105 (DAG Go EH predictor = domain sensitivity) |
P-128 (EH triage K_norm thresholds, THEORIZED) | P-132 (K_out/K_in role classifier, OBSERVED) |
P-141 (Go runtime-coord ctx.Context, PARTIALLY OBSERVED) | P-157 (arch decision tree, PARTIALLY OBSERVED) |
P-165 (K_dup orthogonal to K_import, OBSERVED) | P-166 (function-level additive, OBSERVED) |
P-167 (lib extraction loop confirmed, OBSERVED) | P-168 (lib ROI formula, OBSERVED)

## What to load when
| Task | Load |
|------|------|
| NK analysis on a new codebase | This + P-132 + P-157 + `tools/nk_analyze.py` |
| Extending Go NK analysis | `workspace/nk-analyze-go/` + P-165 + P-166 |
| EH quality prediction | P-097 + P-105 + P-128 + P-141 |
| Lib extraction decision | P-167 + P-168 |
