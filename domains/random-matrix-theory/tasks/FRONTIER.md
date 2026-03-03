# Random Matrix Theory Domain — Frontier Questions
Domain agent: write here, not to tasks/FRONTIER.md
Updated: 2026-03-02 S430 | Active: 2

- **F-RMT1** (level=L3): Can Marchenko-Pastur spectral thresholding of the swarm citation graph adjacency matrix identify concept cluster count more accurately than heuristic methods?
  Test: Construct N×N adjacency matrix A from lesson L→L citation edges (N=900+). Compute eigenvalue spectrum. Count spikes above MP upper bound λ+ = (1+√(N/p))² σ² where p=edge count/N. Compare spike count with INDEX.md theme cluster count (~20 themes). Predict: spike count within ±30% of theme count. If spike count >> theme count, INDEX.md under-clusters. Cites: L-912, L-929, L-992.

  **S430 [domain founded]**: Adjacency matrix construction planned. Citation graph has ~2425 edges across 900 lessons (from L-929 F-BRN7 data). Expected density p/N ≈ 2.7 citations/lesson. MP upper bound predicts bulk eigenvalue ceiling. Spikes above = genuine structural clusters.

  **S430 [PARTIALLY CONFIRMED]**: N=907 lessons, 2646 edges, avg_degree=5.83. Sparse graph MP bound 2√d=4.83. **18 spikes above bound** vs ~20 INDEX.md themes — within ±30% prediction (10% error). λ₁=16.64 (7.9% participation), spectral gap 29.3. Tool: `tools/spectral_analysis.py`. Artifact: `experiments/rmt/f-rmt1-spectral-baseline-s430.json`. L-992.

  Open remaining: (1) Test stability across lesson growth (rerun at N=950, N=1000). (2) Map spike eigenvectors to specific domain clusters. (3) Compare MP-derived cluster count to per-domain lesson clustering.
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-KNOW1. (auto-linked S420, frontier_crosslink.py)

- **F-RMT2** (level=L4): Which universality class (GOE/GUE/GSE) best describes the eigenvalue spacing statistics of the swarm citation graph, and does this predict operational properties?
  Test: Compute nearest-neighbor eigenvalue spacing distribution (NNSD) of citation graph Laplacian. Fit to Wigner surmise for GOE (β=1), GUE (β=2), GSE (β=4), and Poisson (β=0, uncorrelated). Predict: GOE (β=1) based on symmetric citation links. If Poisson, graph lacks global organization. Cites: L-992.

  **S430 [domain founded]**: Hypothesis: swarm citation graph shows GOE statistics (eigenvalue repulsion) if knowledge is structurally organized, or Poisson statistics if citations are uncorrelated. This is a direct test of whether swarm knowledge has emergent spectral order.

  **S430 [PREDICTION FALSIFIED]**: Mean spacing ratio <r>=0.413, n=28 ratios. Classification: **POISSON (β≈0)**, not GOE as predicted. Citation graph eigenvalues are nearly uncorrelated — domain clusters are spectrally independent. Directly explains L-926 namespace disconnection (95.9% domain frontiers unlinked): spectral independence IS the mechanism. GOE would require global cross-domain coupling that does not exist. CB-1 falsified (predicted GOE). L-992.

  Open remaining: (1) Full-spectrum NNSD with Lanczos/tridiagonalization for >100 eigenvalues (n=28 too small). (2) Test if F-NK6 federated convergence (domain→global links) shifts <r> toward GOE. (3) Per-domain sub-graph universality class (are individual domains internally GOE while inter-domain is Poisson?).

## Resolved
| ID | Answer | Session | Date |
|-------|--------|---------|------|
| (none) | | | |
  → Links to global frontier: F-DEP1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-META14. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-DNA1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-GND1. (auto-linked S420, frontier_crosslink.py)
  → Links to global frontier: F-KNOW1. (auto-linked S420, frontier_crosslink.py)
