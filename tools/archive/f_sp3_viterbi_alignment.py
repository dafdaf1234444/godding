#!/usr/bin/env python3
"""F-SP3 Viterbi Burst-Window Alignment (S376)

Tests whether the 3-state HMM from f-sp3-hmm-phase-s370.json recovers
known burst windows (S57, S186, S347) via Viterbi decode.

Pure Python implementation — no numpy/scipy/hmmlearn required.

Emission model: Gaussian per state.
Emission value: lessons + 0.5 * principles (per session).
Baseline S01-S56: distributed as 117L + 121P over 56 sessions.
"""
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / "memory" / "SESSION-LOG.md"
HMM_JSON = REPO / "experiments" / "stochastic-processes" / "f-sp3-hmm-phase-s370.json"
OUT_JSON = REPO / "experiments" / "stochastic-processes" / "f-sp3-viterbi-alignment-s376.json"

# Known burst sessions to validate against
KNOWN_BURSTS = [57, 186, 347]
BURST_WINDOW = 5  # +/- sessions for proximity check


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _session_number(sid: str) -> int:
    """Extract numeric session ID, e.g. 'S57a' -> 57, 'S186' -> 186."""
    m = re.match(r"S(\d+)", sid)
    return int(m.group(1)) if m else -1


def parse_sessions(path: Path) -> list[dict]:
    """Parse SESSION-LOG.md into per-session records.

    Returns list sorted by session number. Duplicate session IDs are
    merged by summing lessons and principles.
    """
    pat = re.compile(
        r"^S(\d+[a-z+]*)\s*\|\s*[\d-]+\s*\|\s*\+(\d+)L.*?\+(\d+)P"
    )
    # Accumulate by numeric session ID
    by_num: dict[int, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        m = pat.match(line)
        if not m:
            continue
        sid_raw = m.group(1)
        num = _session_number("S" + sid_raw)
        if num < 0:
            continue
        lessons = int(m.group(2))
        principles = int(m.group(3))
        if num in by_num:
            by_num[num]["lessons"] += lessons
            by_num[num]["principles"] += principles
        else:
            by_num[num] = {
                "num": num,
                "sid": f"S{num}",
                "lessons": lessons,
                "principles": principles,
            }

    # Build baseline block S01-S56 (117L + 121P distributed uniformly)
    baseline_l = 117.0 / 56.0  # ~2.089
    baseline_p = 121.0 / 56.0  # ~2.161
    for n in range(1, 57):
        if n not in by_num:
            by_num[n] = {
                "num": n,
                "sid": f"S{n}",
                "lessons": baseline_l,
                "principles": baseline_p,
            }

    # Fill gaps in sequence with 0 emission (minimal sessions)
    if by_num:
        max_num = max(by_num)
        for n in range(1, max_num + 1):
            if n not in by_num:
                by_num[n] = {
                    "num": n,
                    "sid": f"S{n}",
                    "lessons": 0.0,
                    "principles": 0.0,
                }

    # Sort by session number
    sessions = sorted(by_num.values(), key=lambda s: s["num"])
    return sessions


def compute_emissions(sessions: list[dict]) -> list[float]:
    """Compute emission = lessons + 0.5 * principles for each session."""
    return [s["lessons"] + 0.5 * s["principles"] for s in sessions]


# ---------------------------------------------------------------------------
# Gaussian emission model
# ---------------------------------------------------------------------------

def gaussian_log_pdf(x: float, mu: float, sigma: float) -> float:
    """Log PDF of univariate Gaussian."""
    sigma = max(sigma, 1e-6)
    return -0.5 * math.log(2 * math.pi * sigma ** 2) - 0.5 * ((x - mu) / sigma) ** 2


# ---------------------------------------------------------------------------
# Viterbi algorithm (pure Python, log-space)
# ---------------------------------------------------------------------------

def log_sum_exp(vals: list[float]) -> float:
    """Numerically stable log-sum-exp."""
    if not vals:
        return float("-inf")
    m = max(vals)
    if m == float("-inf"):
        return float("-inf")
    return m + math.log(sum(math.exp(v - m) for v in vals))


def viterbi(obs: list[float], pi: list[float], A: list[list[float]],
            means: list[float], stds: list[float]) -> list[int]:
    """Viterbi decoding for most likely state sequence.

    Args:
        obs: list of T emission values
        pi: initial state distribution (length K)
        A: K x K transition matrix
        means: per-state Gaussian means (length K)
        stds: per-state Gaussian std devs (length K)

    Returns:
        list of T state indices (0-indexed)
    """
    T = len(obs)
    K = len(means)

    # Log transition matrix
    log_A = [[math.log(A[i][j] + 1e-300) for j in range(K)] for i in range(K)]
    log_pi = [math.log(p + 1e-300) for p in pi]

    # Initialize
    V = [[0.0] * K for _ in range(T)]
    bp = [[0] * K for _ in range(T)]

    for k in range(K):
        V[0][k] = log_pi[k] + gaussian_log_pdf(obs[0], means[k], stds[k])

    # Forward pass
    for t in range(1, T):
        emit_log = [gaussian_log_pdf(obs[t], means[k], stds[k]) for k in range(K)]
        for k in range(K):
            best_score = float("-inf")
            best_prev = 0
            for j in range(K):
                score = V[t - 1][j] + log_A[j][k]
                if score > best_score:
                    best_score = score
                    best_prev = j
            V[t][k] = best_score + emit_log[k]
            bp[t][k] = best_prev

    # Backtrack
    path = [0] * T
    path[-1] = max(range(K), key=lambda k: V[-1][k])
    for t in range(T - 2, -1, -1):
        path[t] = bp[t + 1][path[t + 1]]

    return path


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def find_clusters(path: list[int], target_state: int,
                  sessions: list[dict]) -> list[dict]:
    """Find contiguous runs of target_state in the Viterbi path."""
    clusters = []
    i = 0
    T = len(path)
    while i < T:
        if path[i] == target_state:
            start = i
            while i < T and path[i] == target_state:
                i += 1
            end = i - 1  # inclusive
            clusters.append({
                "start_session": sessions[start]["num"],
                "end_session": sessions[end]["num"],
                "start_idx": start,
                "end_idx": end,
                "length": end - start + 1,
            })
        else:
            i += 1
    return clusters


def check_burst_recovery(path: list[int], sessions: list[dict],
                         burst_state: int, known_bursts: list[int],
                         window: int) -> dict:
    """Check whether known burst sessions fall in burst state.

    Returns dict with exact hits, windowed hits, and per-burst details.
    """
    # Build session-number -> index map
    num_to_idx = {s["num"]: i for i, s in enumerate(sessions)}

    results = []
    exact_hits = 0
    window_hits = 0

    burst_clusters = find_clusters(path, burst_state, sessions)

    for burst_num in known_bursts:
        entry = {"session": f"S{burst_num}"}
        if burst_num not in num_to_idx:
            entry["in_data"] = False
            entry["exact_hit"] = False
            entry["window_hit"] = False
            entry["assigned_state"] = None
            results.append(entry)
            continue

        idx = num_to_idx[burst_num]
        assigned = path[idx]
        entry["in_data"] = True
        entry["assigned_state"] = assigned
        entry["exact_hit"] = (assigned == burst_state)
        if entry["exact_hit"]:
            exact_hits += 1

        # Check if any session within +/- window is in burst state
        nearby_burst = False
        for delta in range(-window, window + 1):
            check_num = burst_num + delta
            if check_num in num_to_idx:
                check_idx = num_to_idx[check_num]
                if path[check_idx] == burst_state:
                    nearby_burst = True
                    break
        entry["window_hit"] = nearby_burst
        if nearby_burst:
            window_hits += 1

        # Find which cluster it falls in (if any)
        for cl in burst_clusters:
            if cl["start_session"] <= burst_num <= cl["end_session"]:
                entry["cluster"] = cl
                break
            # Check window overlap with clusters
            for cl2 in burst_clusters:
                if (cl2["start_session"] - window <= burst_num <= cl2["end_session"] + window):
                    entry["nearest_cluster"] = cl2
                    break

        results.append(entry)

    return {
        "exact_hits": exact_hits,
        "exact_total": len(known_bursts),
        "exact_precision": exact_hits / len(known_bursts) if known_bursts else 0,
        "window_hits": window_hits,
        "window_total": len(known_bursts),
        "window_precision": window_hits / len(known_bursts) if known_bursts else 0,
        "per_burst": results,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # 1. Parse sessions and compute emissions
    print("=" * 60)
    print("F-SP3 Viterbi Burst-Window Alignment (S376)")
    print("=" * 60)

    sessions = parse_sessions(LOG)
    emissions = compute_emissions(sessions)
    T = len(emissions)

    print(f"\nParsed {T} sessions (S1..S{sessions[-1]['num']})")
    mean_e = sum(emissions) / T
    var_e = sum((e - mean_e) ** 2 for e in emissions) / T
    std_e = math.sqrt(var_e)
    print(f"Emission stats: mean={mean_e:.3f}, std={std_e:.3f}, "
          f"min={min(emissions):.1f}, max={max(emissions):.1f}")

    # 2. Load HMM parameters from S370 experiment
    print(f"\nLoading HMM parameters from {HMM_JSON.name}...")
    with open(HMM_JSON, "r", encoding="utf-8") as f:
        hmm_data = json.load(f)

    # The S370 JSON has 4 named states but effective_states=3
    # (convergence and accumulation are identical). We use the
    # 3-state effective model: quiescent, integration/production, burst
    # Map: states 0,1 (convergence+accumulation) -> quiescent(0)
    #       state 2 (integration) -> production(1)
    #       state 3 (burst) -> burst(2)

    # Extract parameters from the 4-state model, collapsing states 0+1
    states_data = hmm_data["hmm_states"]
    trans = hmm_data["transition_matrix"]

    # 4-state parameters (sorted by mean: convergence, accumulation, integration, burst)
    state_names_4 = ["convergence", "accumulation", "integration", "burst"]
    means_4 = [states_data[n]["mean"] for n in state_names_4]
    stds_4 = [states_data[n]["std"] for n in state_names_4]

    # Since convergence and accumulation are identical (same mean, same std,
    # same self-transition), we collapse to 3 effective states.
    # Quiescent: merge states 0+1 (weight by n_sessions proportion)
    n_conv = states_data["convergence"]["n_sessions"]
    n_acc = states_data["accumulation"]["n_sessions"]
    n_int = states_data["integration"]["n_sessions"]
    n_burst = states_data["burst"]["n_sessions"]

    # Since n_acc=0, quiescent is just convergence
    state_names_3 = ["quiescent", "production", "burst"]
    means_3 = [means_4[0], means_4[2], means_4[3]]
    stds_3 = [stds_4[0], stds_4[2], stds_4[3]]

    # Collapse 4x4 transition matrix to 3x3
    # State mapping: {0,1}->0, 2->1, 3->2
    # For transitions from quiescent (merged 0+1):
    #   weight by stationary proportion (n_conv >> n_acc, so mostly state 0)
    # Since accumulation has 0 sessions, we just use convergence row
    trans_3 = [[0.0] * 3 for _ in range(3)]

    # From quiescent (state 0 in 4-model = convergence):
    # to quiescent = trans[0][0] + trans[0][1]
    # to production = trans[0][2]
    # to burst = trans[0][3]
    trans_3[0][0] = trans[0][0] + trans[0][1]
    trans_3[0][1] = trans[0][2]
    trans_3[0][2] = trans[0][3]

    # From production (state 2 in 4-model = integration):
    trans_3[1][0] = trans[2][0] + trans[2][1]
    trans_3[1][1] = trans[2][2]
    trans_3[1][2] = trans[2][3]

    # From burst (state 3 in 4-model):
    trans_3[2][0] = trans[3][0] + trans[3][1]
    trans_3[2][1] = trans[3][2]
    trans_3[2][2] = trans[3][3]

    # Initial distribution (proportional to session counts)
    total_sessions = max(n_conv + n_acc + n_int + n_burst, 1)
    pi_3 = [
        (n_conv + n_acc) / total_sessions,
        n_int / total_sessions,
        n_burst / total_sessions,
    ]

    print(f"\n--- 3-State HMM Parameters (from S370) ---")
    for i, name in enumerate(state_names_3):
        print(f"  {name:12s}: mean={means_3[i]:.3f}, std={stds_3[i]:.3f}, "
              f"pi={pi_3[i]:.3f}")

    print(f"\n  Transition matrix:")
    print(f"  {'':12s}  {'quiescent':>10s}  {'production':>10s}  {'burst':>10s}")
    for i, name in enumerate(state_names_3):
        row = "  ".join(f"{trans_3[i][j]:.4f}" for j in range(3))
        print(f"  {name:12s}  {row}")

    # 3. Run Viterbi decode
    print(f"\n--- Viterbi Decode ---")
    path = viterbi(emissions, pi_3, trans_3, means_3, stds_3)

    # State assignment counts
    state_counts = [0, 0, 0]
    for s in path:
        state_counts[s] += 1

    print(f"\n  State assignment counts:")
    for i, name in enumerate(state_names_3):
        pct = 100.0 * state_counts[i] / T
        print(f"    {name:12s}: {state_counts[i]:4d} sessions ({pct:.1f}%)")

    # 4. Find burst clusters
    burst_state_idx = 2  # burst is state index 2
    clusters = find_clusters(path, burst_state_idx, sessions)

    print(f"\n  Burst clusters ({len(clusters)} found):")
    for cl in clusters:
        print(f"    S{cl['start_session']}..S{cl['end_session']} "
              f"({cl['length']} sessions)")

    # 5. Check known burst recovery
    print(f"\n--- Known Burst Recovery ---")
    print(f"  Known bursts: {['S' + str(b) for b in KNOWN_BURSTS]}")
    print(f"  Window: +/- {BURST_WINDOW} sessions")

    recovery = check_burst_recovery(
        path, sessions, burst_state_idx, KNOWN_BURSTS, BURST_WINDOW
    )

    for detail in recovery["per_burst"]:
        session = detail["session"]
        if not detail["in_data"]:
            print(f"  {session}: NOT IN DATA")
            continue
        state_name = state_names_3[detail["assigned_state"]]
        exact = "YES" if detail["exact_hit"] else "NO"
        window = "YES" if detail["window_hit"] else "NO"
        print(f"  {session}: state={state_name}, "
              f"exact_hit={exact}, window_hit={window}")

    print(f"\n  Exact precision: {recovery['exact_hits']}/{recovery['exact_total']} "
          f"= {recovery['exact_precision']:.1%}")
    print(f"  Window precision: {recovery['window_hits']}/{recovery['window_total']} "
          f"= {recovery['window_precision']:.1%}")

    # 6. Compute recall: known bursts in burst state / total burst-state sessions
    total_burst_sessions = state_counts[burst_state_idx]
    recall = recovery["exact_hits"] / total_burst_sessions if total_burst_sessions > 0 else 0.0
    print(f"\n  Recall (known_in_burst / total_burst): "
          f"{recovery['exact_hits']}/{total_burst_sessions} = {recall:.3f}")

    # 7. Show emission values at known burst points
    num_to_idx = {s["num"]: i for i, s in enumerate(sessions)}
    print(f"\n--- Emission values at known bursts ---")
    for burst_num in KNOWN_BURSTS:
        if burst_num in num_to_idx:
            idx = num_to_idx[burst_num]
            e = emissions[idx]
            s = sessions[idx]
            print(f"  S{burst_num}: emission={e:.1f} "
                  f"(L={s['lessons']}, P={s['principles']})")

    # 8. Show top-emission sessions for context
    indexed = [(emissions[i], sessions[i]["num"]) for i in range(T)]
    indexed.sort(reverse=True)
    print(f"\n--- Top 10 emission sessions ---")
    for e, num in indexed[:10]:
        idx = num_to_idx[num]
        state_name = state_names_3[path[idx]]
        print(f"  S{num}: emission={e:.1f} -> {state_name}")

    # 9. Build and write JSON artifact
    # Serialize burst details
    burst_details = []
    for detail in recovery["per_burst"]:
        d = {
            "session": detail["session"],
            "in_data": detail["in_data"],
            "exact_hit": detail["exact_hit"],
            "window_hit": detail["window_hit"],
        }
        if detail["assigned_state"] is not None:
            d["assigned_state"] = state_names_3[detail["assigned_state"]]
        if "cluster" in detail:
            d["in_cluster"] = f"S{detail['cluster']['start_session']}..S{detail['cluster']['end_session']}"
        if "nearest_cluster" in detail:
            d["nearest_cluster"] = f"S{detail['nearest_cluster']['start_session']}..S{detail['nearest_cluster']['end_session']}"
        burst_details.append(d)

    cluster_list = [
        {
            "range": f"S{cl['start_session']}..S{cl['end_session']}",
            "length": cl["length"],
        }
        for cl in clusters
    ]

    artifact = {
        "frontier": "F-SP3",
        "experiment": "viterbi-burst-alignment",
        "session": "S376",
        "date": "2026-03-01",
        "description": "Tests whether 3-state HMM from S370 recovers known burst windows via Viterbi decode",
        "hmm_source": "f-sp3-hmm-phase-s370.json",
        "emission_formula": "lessons + 0.5 * principles",
        "n_sessions_total": T,
        "session_range": f"S1..S{sessions[-1]['num']}",
        "known_bursts": [f"S{b}" for b in KNOWN_BURSTS],
        "burst_window": BURST_WINDOW,
        "state_counts": {
            state_names_3[i]: state_counts[i] for i in range(3)
        },
        "state_percentages": {
            state_names_3[i]: round(100.0 * state_counts[i] / T, 1) for i in range(3)
        },
        "burst_clusters": cluster_list,
        "n_burst_clusters": len(clusters),
        "burst_recovery": {
            "exact_precision": round(recovery["exact_precision"], 3),
            "window_precision": round(recovery["window_precision"], 3),
            "exact_hits": recovery["exact_hits"],
            "window_hits": recovery["window_hits"],
            "recall_known_over_total_burst": round(recall, 4),
            "details": burst_details,
        },
        "hmm_parameters_used": {
            "n_states": 3,
            "state_names": state_names_3,
            "means": means_3,
            "stds": stds_3,
            "initial_distribution": pi_3,
            "transition_matrix": trans_3,
        },
        "verdict": None,  # filled below
        "interpretation": None,
    }

    # Determine verdict
    exact_p = recovery["exact_precision"]
    window_p = recovery["window_precision"]
    if exact_p >= 0.67:
        verdict = "CONFIRMED"
        interp = (f"HMM recovers {recovery['exact_hits']}/3 known bursts exactly "
                  f"({exact_p:.0%}). Viterbi alignment validates HMM phase structure.")
    elif window_p >= 0.67:
        verdict = "PARTIALLY CONFIRMED"
        interp = (f"HMM recovers {recovery['window_hits']}/3 known bursts within "
                  f"+/-{BURST_WINDOW} sessions ({window_p:.0%}). "
                  f"Phase boundaries are approximately correct but not session-precise.")
    elif exact_p > 0 or window_p > 0:
        verdict = "WEAK"
        interp = (f"HMM recovers {recovery['exact_hits']}/3 exact, "
                  f"{recovery['window_hits']}/3 windowed. "
                  f"Partial alignment suggests model captures some burst structure "
                  f"but not all known events.")
    else:
        verdict = "FALSIFIED"
        interp = ("HMM fails to recover any known burst windows. "
                  "Phase model may not correspond to historical burst events.")

    artifact["verdict"] = verdict
    artifact["interpretation"] = interp

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)
        f.write("\n")

    print(f"\n{'=' * 60}")
    print(f"VERDICT: {verdict}")
    print(f"  {interp}")
    print(f"\nArtifact written: {OUT_JSON.relative_to(REPO)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
