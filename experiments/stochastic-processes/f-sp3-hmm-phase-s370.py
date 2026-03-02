#!/usr/bin/env python3
"""F-SP3: Is the 4-phase meta-cycle an HMM with phase-specific entropy rates?

Hypothesis: 4-state HMM (accumulation/burst/integration/convergence)
with burst phases having 3-5x entropy rate of convergence phases.

Test: Extract emissions from SESSION-LOG.md, fit 4-state Gaussian HMM
via Baum-Welch, Viterbi decode, compare state entropy rates.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
LOG = REPO / "memory" / "SESSION-LOG.md"


def parse_sessions(path: Path) -> list[dict]:
    """Extract per-session emissions from SESSION-LOG.md."""
    sessions = []
    seen = set()
    pat = re.compile(
        r"^(S\d+\w*)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*"
        r"\+(\d+)L.*?\+(\d+)P\s*\|\s*(.*)"
    )
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pat.match(line.strip())
        if not m:
            continue
        sid = m.group(1)
        if sid in seen:
            continue
        seen.add(sid)
        lessons = int(m.group(3))
        principles = int(m.group(4))
        summary = m.group(5)
        # Count frontier resolutions mentioned
        f_resolved = len(re.findall(r"(?:RESOLVED|CONFIRMED|FALSIFIED|DONE)", summary))
        # Count tools/files mentioned (proxy for breadth)
        files_mentioned = len(re.findall(r"\b\w+\.\w{2,4}\b", summary))
        sessions.append({
            "sid": sid,
            "date": m.group(2),
            "lessons": lessons,
            "principles": principles,
            "f_resolved": f_resolved,
            "breadth": min(files_mentioned, 10),  # cap outliers
        })
    return sessions


def gaussian_log_pdf(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """Log PDF of univariate Gaussian."""
    sigma = max(sigma, 1e-6)
    return -0.5 * np.log(2 * np.pi * sigma**2) - 0.5 * ((x - mu) / sigma) ** 2


def baum_welch(obs: np.ndarray, n_states: int = 4, n_iter: int = 100,
               tol: float = 1e-4) -> dict:
    """Fit Gaussian HMM via Baum-Welch (EM) algorithm.

    obs: 1D array of observations (e.g., lessons per session).
    Returns: dict with pi, A, means, stds, log_likelihood.
    """
    T = len(obs)
    K = n_states

    # Initialize: spread means across data range
    sorted_obs = np.sort(obs)
    quantiles = [sorted_obs[int(q * (T - 1))] for q in np.linspace(0.1, 0.9, K)]
    means = np.array(quantiles, dtype=float)
    stds = np.full(K, max(np.std(obs), 0.5))
    pi = np.ones(K) / K
    A = np.full((K, K), 0.1 / (K - 1))
    np.fill_diagonal(A, 0.9)  # strong self-transition prior

    prev_ll = -np.inf

    for iteration in range(n_iter):
        # E-step: forward-backward
        # Emission log-probs
        log_B = np.zeros((T, K))
        for k in range(K):
            log_B[:, k] = gaussian_log_pdf(obs, means[k], stds[k])

        # Forward (log-space)
        log_alpha = np.zeros((T, K))
        log_alpha[0] = np.log(pi + 1e-300) + log_B[0]
        for t in range(1, T):
            for k in range(K):
                log_alpha[t, k] = (
                    np.logaddexp.reduce(log_alpha[t - 1] + np.log(A[:, k] + 1e-300))
                    + log_B[t, k]
                )

        # Backward (log-space)
        log_beta = np.zeros((T, K))
        for t in range(T - 2, -1, -1):
            for k in range(K):
                log_beta[t, k] = np.logaddexp.reduce(
                    np.log(A[k] + 1e-300) + log_B[t + 1] + log_beta[t + 1]
                )

        # Log-likelihood
        ll = np.logaddexp.reduce(log_alpha[-1])
        if ll - prev_ll < tol and iteration > 5:
            break
        prev_ll = ll

        # Posterior (gamma)
        log_gamma = log_alpha + log_beta
        log_gamma -= np.logaddexp.reduce(log_gamma, axis=1, keepdims=True)
        gamma = np.exp(log_gamma)

        # Xi (transition posterior)
        xi = np.zeros((T - 1, K, K))
        for t in range(T - 1):
            for i in range(K):
                for j in range(K):
                    xi[t, i, j] = (
                        log_alpha[t, i]
                        + np.log(A[i, j] + 1e-300)
                        + log_B[t + 1, j]
                        + log_beta[t + 1, j]
                    )
            xi[t] -= np.logaddexp.reduce(xi[t].ravel())
        xi = np.exp(xi)

        # M-step
        pi = gamma[0] / gamma[0].sum()
        for k in range(K):
            gk = gamma[:, k]
            gk_sum = gk.sum() + 1e-300
            means[k] = (gk * obs).sum() / gk_sum
            stds[k] = max(np.sqrt((gk * (obs - means[k]) ** 2).sum() / gk_sum), 0.3)

        for i in range(K):
            xi_sum = xi[:, i, :].sum(axis=0)
            A[i] = xi_sum / (xi_sum.sum() + 1e-300)

    return {
        "pi": pi,
        "A": A,
        "means": means,
        "stds": stds,
        "log_likelihood": float(ll),
        "n_iter": iteration + 1,
    }


def viterbi(obs: np.ndarray, pi: np.ndarray, A: np.ndarray,
            means: np.ndarray, stds: np.ndarray) -> np.ndarray:
    """Viterbi decoding for most likely state sequence."""
    T = len(obs)
    K = len(means)

    log_B = np.zeros((T, K))
    for k in range(K):
        log_B[:, k] = gaussian_log_pdf(obs, means[k], stds[k])

    V = np.zeros((T, K))
    bp = np.zeros((T, K), dtype=int)
    V[0] = np.log(pi + 1e-300) + log_B[0]

    for t in range(1, T):
        for k in range(K):
            scores = V[t - 1] + np.log(A[:, k] + 1e-300) + log_B[t, k]
            bp[t, k] = np.argmax(scores)
            V[t, k] = scores[bp[t, k]]

    # Backtrack
    path = np.zeros(T, dtype=int)
    path[-1] = np.argmax(V[-1])
    for t in range(T - 2, -1, -1):
        path[t] = bp[t + 1, path[t + 1]]
    return path


def entropy_rate(obs: np.ndarray, states: np.ndarray, state_id: int) -> float:
    """Estimate entropy rate for observations in a given state.

    Uses sample variance as proxy: H ≈ 0.5 * log(2*pi*e*var).
    """
    mask = states == state_id
    if mask.sum() < 3:
        return float("nan")
    x = obs[mask]
    var = np.var(x)
    if var < 1e-6:
        return 0.0
    return 0.5 * np.log(2 * np.pi * np.e * var)


def main():
    sessions = parse_sessions(LOG)
    if len(sessions) < 20:
        print(f"ERROR: Only {len(sessions)} sessions parsed, need ≥20")
        sys.exit(1)

    print(f"Parsed {len(sessions)} sessions from SESSION-LOG.md")

    # Primary emission: lessons per session (captures production intensity)
    lessons = np.array([s["lessons"] for s in sessions], dtype=float)
    principles = np.array([s["principles"] for s in sessions], dtype=float)
    f_resolved = np.array([s["f_resolved"] for s in sessions], dtype=float)

    # Combined emission: lessons + 0.5*principles + 0.3*f_resolved
    combined = lessons + 0.5 * principles + 0.3 * f_resolved

    print(f"\nEmission stats (combined): mean={combined.mean():.2f}, "
          f"std={combined.std():.2f}, min={combined.min():.1f}, max={combined.max():.1f}")

    # Fit 4-state HMM
    result = baum_welch(combined, n_states=4, n_iter=200)
    print(f"\nHMM fit: {result['n_iter']} iterations, LL={result['log_likelihood']:.1f}")

    # Sort states by mean (low→high = convergence→burst)
    order = np.argsort(result["means"])
    sorted_means = result["means"][order]
    sorted_stds = result["stds"][order]
    sorted_A = result["A"][order][:, order]
    sorted_pi = result["pi"][order]

    state_names = ["convergence", "accumulation", "integration", "burst"]

    print("\n--- State parameters ---")
    for i, name in enumerate(state_names):
        print(f"  {name:15s}: mean={sorted_means[i]:.2f}, std={sorted_stds[i]:.2f}, "
              f"pi={sorted_pi[i]:.3f}")

    print("\n--- Transition matrix ---")
    print("  " + "".join(f"{n[:5]:>8s}" for n in state_names))
    for i, name in enumerate(state_names):
        row = "  ".join(f"{sorted_A[i, j]:.3f}" for j in range(4))
        print(f"  {name[:5]:5s}  {row}")

    # Viterbi decode
    path = viterbi(combined, sorted_pi, sorted_A, sorted_means, sorted_stds)

    # Entropy rates per state
    print("\n--- Entropy rates per state ---")
    entropy_rates = {}
    state_counts = {}
    for i, name in enumerate(state_names):
        h = entropy_rate(combined, path, i)
        n_sessions = (path == i).sum()
        entropy_rates[name] = h
        state_counts[name] = int(n_sessions)
        print(f"  {name:15s}: H={h:.3f} nats  (n={n_sessions} sessions)")

    # Test hypothesis: burst entropy 3-5x convergence entropy
    h_burst = entropy_rates["burst"]
    h_conv = entropy_rates["convergence"]
    if h_conv > 0 and not np.isnan(h_burst) and not np.isnan(h_conv):
        ratio = h_burst / h_conv
        print(f"\n--- Hypothesis test ---")
        print(f"  Burst/Convergence entropy ratio: {ratio:.2f}x")
        print(f"  Target: 3.0-5.0x")
        if 3.0 <= ratio <= 5.0:
            print(f"  CONFIRMED: ratio {ratio:.2f} within 3-5x range")
            verdict = "CONFIRMED"
        elif ratio > 1.5:
            print(f"  PARTIAL: ratio {ratio:.2f} — burst > convergence but outside 3-5x")
            verdict = "PARTIAL"
        else:
            print(f"  FALSIFIED: ratio {ratio:.2f} — insufficient entropy difference")
            verdict = "FALSIFIED"
    else:
        print("\n  Cannot compute ratio (insufficient data or zero entropy)")
        ratio = None
        verdict = "INSUFFICIENT_DATA"

    # Also compare to 2-state and 3-state models (BIC comparison)
    print("\n--- Model comparison (BIC) ---")
    bic_results = {}
    for n_states in [2, 3, 4, 5]:
        r = baum_welch(combined, n_states=n_states, n_iter=200)
        n_params = n_states - 1 + n_states * (n_states - 1) + 2 * n_states
        bic = -2 * r["log_likelihood"] + n_params * np.log(len(combined))
        bic_results[n_states] = bic
        print(f"  {n_states}-state: LL={r['log_likelihood']:.1f}, "
              f"params={n_params}, BIC={bic:.1f}")

    best_n = min(bic_results, key=bic_results.get)
    print(f"  Best model: {best_n}-state (BIC={bic_results[best_n]:.1f})")

    # Transition self-loop analysis (persistence)
    print("\n--- State persistence (self-transition probability) ---")
    for i, name in enumerate(state_names):
        print(f"  {name:15s}: P(stay)={sorted_A[i, i]:.3f}")

    # Build experiment artifact
    artifact = {
        "frontier": "F-SP3",
        "session": "S370",
        "date": "2026-03-01",
        "hypothesis": "4-state HMM with burst entropy 3-5x convergence entropy",
        "n_sessions": len(sessions),
        "emission": "lessons + 0.5*principles + 0.3*frontiers_resolved",
        "emission_stats": {
            "mean": float(combined.mean()),
            "std": float(combined.std()),
        },
        "hmm_states": {
            name: {
                "mean": float(sorted_means[i]),
                "std": float(sorted_stds[i]),
                "entropy_rate": float(entropy_rates[name]) if not np.isnan(entropy_rates[name]) else None,
                "n_sessions": state_counts[name],
                "self_transition": float(sorted_A[i, i]),
            }
            for i, name in enumerate(state_names)
        },
        "transition_matrix": sorted_A.tolist(),
        "model_comparison_bic": {str(k): float(v) for k, v in bic_results.items()},
        "best_n_states": best_n,
        "entropy_ratio_burst_convergence": float(ratio) if ratio is not None else None,
        "verdict": verdict,
        "log_likelihood": result["log_likelihood"],
    }

    out_path = Path(__file__).with_suffix(".json")
    out_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"\nArtifact written: {out_path.relative_to(REPO)}")
    print(f"\nVERDICT: {verdict}")


if __name__ == "__main__":
    main()
