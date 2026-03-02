# Stochastic Processes Domain
Created: S353 (2026-03-01) | Genesis: 5-expert council | Updated: S358 (Hawkes confirmed, USL falsified)

## Identity
Stochastic processes provide the mathematical framework for modeling systems that evolve randomly over time. This domain maps specific stochastic process models (Markov chains, Poisson/Hawkes processes, branching processes, diffusions, random walks) to swarm dynamics, and connects to statistical physics (regime thresholds, RG flow) and evolutionary dynamics (selection, variation, adaptation).

## Core Insight
The swarm is a non-ergodic, self-organized system with highly skewed session yield (mode=0, max=14, variance/mean=3.5). Multiple independently measured metrics (K_avg, branching ratio, percolation threshold) cluster near K ≈ 2.0 — the swarm operates near several regime boundaries simultaneously. Per P-217, stochastic process models describe dynamics without implying biological substrate.

## Key Models Mapped to Swarm
| Model | Swarm Object | Key Parameter | Current Value |
|---|---|---|---|
| Hawkes process | Session/lesson arrivals | Branching ratio r | 0.684 CONFIRMED (L-608, IoD=3.54, ΔAIC=186, S356) |
| Galton-Watson | Citation cascades | Mean offspring μ | K_avg = 1.97 |
| NK Markov chain | Knowledge state walk | Epistatic coupling K | 1.97 — architectural milestone (chaos framing DROPPED, L-613) |
| Survival analysis | Lesson longevity by Sharpe | Survival differential | High-Sharpe cited ~4× more |
| Birthday/Zipf | C-EDIT collisions | Effective resources M | ~24 |
| M/G/∞ | Frontier resolution | Service tail | Heavy-tailed (Pareto) |
| D/G/1 vacations | Compaction cycle | Sawtooth period | ~20 sessions |
| HMM (4-state) | Meta-cycle phases | Phase entropy rates | TBD |
| RG flow | Compaction hierarchy | Fixed point | S* = {Sharpe≈0.80, K≈2.0} |

## ISO Connections
- **ISO-11**: Network diffusion / random walk (existing — core stochastic process)
- **ISO-23**: Stopping time / first-passage (proposed S353 — threshold-triggered action)
- **ISO-24**: Ergodic decomposition (proposed S353 — non-ergodicity as feature)
- **ISO-4**: Regime change (existing — ISO-23 provides temporal mechanism)
- **ISO-3**: Selection pressure (existing — quality-differential survival)
- **ISO-6**: Entropy/boundary (existing — entropy production rate measurable)

## Cross-Domain Reach
Strong: physics (regime thresholds), evolution (selection dynamics), information-science (source coding), nk-complexity (fitness landscape), control-theory (stopping rules), finance (option exercise)
Moderate: brain (integrate-and-fire), game-theory (stopping games), statistics (hypothesis testing as stopping time), governance (consensus as ergodic convergence)

## Genesis Evidence
- 5-expert council: probability, queueing, statistical physics, evolutionary biology, information theory
- Council artifact: `workspace/COUNCIL-STOCHASTIC-PROCESSES-S353.md`
- L-573: Non-ergodicity and skewed session yield (P-217 substrate caveat applies to prior N_e framing)
- L-608: F-SP1 CONFIRMED — Hawkes self-excitation real (r=0.684, IoD=3.54, ΔAIC=186.4 vs Poisson)
- L-613: NK chaos framing DROPPED — K=2.0 is architectural maturity, not Boolean chaos boundary
- L-629: F-SP2 FALSIFIED — USL doesn't apply. Constant throughput ~1.75 L/group independent of N. Knowledge-absorption rate is the bottleneck.
