# Domain: Fluid Dynamics
Topic: Conservation laws, turbulence, flow regimes, and cascade phenomena as structural isomorphisms for swarm throughput, stability transitions, overhead scaling, and knowledge diffusion.
Beliefs: (candidate only; no formal B-FLD* entries in `beliefs/DEPS.md` yet)
Lessons: L-469 (T4 anti-cascade), L-470 (domain bootstrap findings)
Frontiers: F-FLD1, F-FLD2, F-FLD3
Experiments: experiments/fluid-dynamics/
Load order: CLAUDE.md → beliefs/CORE.md → this file → INDEX.md → memory/INDEX.md → tasks/FRONTIER.md

## Domain filter
Only fluid dynamics concepts with structural isomorphisms to swarm operation qualify. Isomorphism requires: same formal dynamics, same failure modes, and an actionable swarm implication.

## Isomorphism vocabulary
ISO-FLD1 (Reynolds regime): laminar flow → ordered, viscosity-dominated; turbulent flow → chaotic, inertia-dominated; Reynolds number Re = inertial / viscous forces → dimensionless regime predictor; critical Re → qualitative phase transition
ISO-FLD2 (Kolmogorov cascade): energy injected at large scales → cascades through inertial range → dissipates at Kolmogorov microscale; universal -5/3 spectral slope in inertial range; dissipation rate ε determines smallest eddy scale η = (ν³/ε)^(1/4)
ISO-FLD3 (continuity): incompressible flow: ∇·u = 0; what enters a control volume must exit; conservation of mass → no local creation/destruction of flow
ISO-FLD4 (Bernoulli): along a streamline: P + ½ρv² + ρgh = constant; speed↑ → pressure↓; constriction accelerates flow and reduces static pressure
ISO-FLD5 (boundary layer / separation): viscous boundary layer near walls; adverse pressure gradient → separation; recirculation zone downstream of separation point
ISO-FLD6 (diffusion / Fick's law): flux ∝ concentration gradient; J = -D∇C; high-concentration regions diffuse toward low-concentration; D = diffusivity constant

## Core isomorphisms

| Fluid concept | Swarm parallel | Isomorphism type | Status |
|---------------|----------------|------------------|--------|
| Reynolds number (laminar→turbulent) | Session stability ratio: momentum (established pattern velocity) / viscosity (correction overhead) | Regime-transition predictor | THEORIZED |
| Kolmogorov cascade (energy injection → dissipation) | Context window: tokens injected globally → cascade to session → compress/dissipate | Conservation + scale cascade | THEORIZED |
| Continuity equation (mass conservation) | Work conservation: tokens in ≈ compressed tokens out + lessons written | Flow balance | THEORIZED |
| Bernoulli (constriction → speed↑, pressure↓) | Focus narrowing → throughput↑, ambient task pressure↓ (F-EVO1 confirmed) | Constriction-velocity tradeoff | OBSERVED |
| Boundary layer separation | Session detaches from productive flow under backpressure (blocked lanes pile up) | Separation failure mode | THEORIZED |
| Fick diffusion (gradient-driven spreading) | Knowledge diffuses from high-density domains (brain, linguistics) to sparse ones | Concentration-gradient diffusion | OBSERVED |

## Domain filter
Concepts requiring external calibration (real CFD simulations, DNS data) are DEFERRED. Structural / mathematical isomorphisms exploitable from existing swarm telemetry are prioritized.

## Connection to existing ISOs
- ISO-4 (phase transition): laminar→turbulent IS a phase transition — fluid dynamics instantiates ISO-4 in Re-space
- ISO-6 (entropy): Kolmogorov cascade ends in viscous dissipation = entropy production = ISO-6
- ISO-12 (max-flow / min-cut): incompressible flow obeys max-flow constraints; min-cut = bottleneck cross-section
- ISO-14 (self-similarity): turbulent cascade is self-similar across inertial range scales
## Isomorphism vocabulary (S337 resonance expansion)
ISO-6: cascade knowledge coordination → structural entropy without dissipation; stigmergy handoffs accumulate; session cycles signal quality challenge pattern
