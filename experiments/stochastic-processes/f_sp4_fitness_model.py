#!/usr/bin/env python3
"""F-SP4 extension: Bianconi-Barabási fitness model for citation attachment.

Tests whether lesson-level covariates (Sharpe score, domain tag) explain
residual citation variance after controlling for PA (degree) and proximity
(session gap).

Models compared via conditional log-likelihood + BIC:
  A: Joint PA+Proximity:                w ∝ (k+1)^γ * exp(-λΔs)
  B: Joint + Sharpe fitness:            w ∝ (k+1)^γ * exp(-λΔs) * exp(β_s * sharpe)
  C: Joint + Sharpe + Domain indicator: w ∝ (k+1)^γ * exp(-λΔs) * exp(β_s * sharpe + β_d * has_domain)

Usage:
    python3 experiments/stochastic-processes/f_sp4_fitness_model.py
    python3 experiments/stochastic-processes/f_sp4_fitness_model.py --json
"""

import argparse
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


def extract_lesson_number(filename: str) -> int | None:
    m = re.match(r"L-(\d+)\.md", filename)
    return int(m.group(1)) if m else None


def parse_lesson_metadata(filepath: Path) -> dict:
    """Extract session, Sharpe, domain, and citations from a lesson file."""
    meta = {"session": None, "sharpe": None, "domain": None, "cites": []}
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read(3000)

    m = re.search(r"\*{0,2}Session\*{0,2}:\s*S?(\d+)", text)
    if not m:
        m = re.search(r"session:\s*S?(\d+)", text, re.IGNORECASE)
    if m:
        meta["session"] = int(m.group(1))

    m = re.search(r"\*{0,2}Sharpe\*{0,2}:\s*(\d+(?:\.\d+)?)", text)
    if not m:
        m = re.search(r"sharpe:\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if m:
        meta["sharpe"] = float(m.group(1))

    m = re.search(r"\*{0,2}Domain\*{0,2}:\s*(\S+)", text)
    if not m:
        m = re.search(r"domain:\s*(\S+)", text, re.IGNORECASE)
    if m:
        meta["domain"] = m.group(1).strip().rstrip("|").strip()

    for line in text.split("\n"):
        if line.startswith("Cites:"):
            meta["cites"] = [int(x) for x in re.findall(r"\bL-(\d+)\b", line)]
            break

    return meta


def build_enriched_dag(lessons_dir: Path):
    """Build DAG with session, Sharpe, and domain metadata."""
    dag = {}
    sessions = {}
    sharpes = {}
    domains = {}

    for fname in sorted(os.listdir(lessons_dir)):
        num = extract_lesson_number(fname)
        if num is None:
            continue
        meta = parse_lesson_metadata(lessons_dir / fname)
        prior_cites = [c for c in meta["cites"] if c < num]
        dag[num] = prior_cites
        if meta["session"] is not None:
            sessions[num] = meta["session"]
        if meta["sharpe"] is not None:
            sharpes[num] = meta["sharpe"]
        if meta["domain"] is not None:
            domains[num] = meta["domain"]

    return dag, sessions, sharpes, domains


def precompute_events(dag, sessions, sharpes, domains, mean_sharpe):
    """Precompute all citation events with pool data for fast LL evaluation.

    Returns list of events, each: {
        target_k_at_event, target_gap, target_sharpe, target_domain,
        pool: [(k, gap, sharpe, domain), ...]
    }
    """
    degree = defaultdict(int)
    all_nodes = []
    all_nodes_set = set()
    events = []

    for src in sorted(dag.keys()):
        all_nodes.append(src)
        all_nodes_set.add(src)
        src_sess = sessions.get(src)

        if not dag[src]:
            for target in dag[src]:
                degree[target] += 1
            continue

        pool = [nd for nd in all_nodes if nd < src]
        if not pool:
            for target in dag[src]:
                degree[target] += 1
            continue

        # Precompute pool data
        pool_data = []
        for nd in pool:
            if src_sess is not None and sessions.get(nd) is not None:
                gap = abs(src_sess - sessions[nd])
            else:
                gap = abs(src - nd) / 2.0
            s = sharpes.get(nd, mean_sharpe) - mean_sharpe
            d = 1.0 if nd in domains else 0.0
            pool_data.append((degree[nd], gap, s, d, nd))

        for target in dag[src]:
            if target not in all_nodes_set:
                continue

            # Find target in pool_data
            t_k = degree[target]
            if src_sess is not None and sessions.get(target) is not None:
                t_gap = abs(src_sess - sessions[target])
            else:
                t_gap = abs(src - target) / 2.0
            t_s = sharpes.get(target, mean_sharpe) - mean_sharpe
            t_d = 1.0 if target in domains else 0.0

            events.append({
                "t_k": t_k, "t_gap": t_gap, "t_s": t_s, "t_d": t_d,
                "pool": pool_data,
            })

            degree[target] += 1

    return events


def fast_ll(events, gamma, lam, beta_s=0.0, beta_d=0.0):
    """Fast conditional LL using precomputed events."""
    ll = 0.0
    n = 0
    for ev in events:
        # Target weight
        w_t = ((ev["t_k"] + 1) ** gamma
               * math.exp(-lam * ev["t_gap"]
                          + beta_s * ev["t_s"]
                          + beta_d * ev["t_d"]))

        # Pool sum
        w_sum = 0.0
        for k, gap, s, d, _ in ev["pool"]:
            w_sum += ((k + 1) ** gamma
                      * math.exp(-lam * gap + beta_s * s + beta_d * d))

        if w_sum > 0 and w_t > 0:
            ll += math.log(w_t / w_sum)
            n += 1

    return ll, n


def compute_bic(ll, k_params, n_events):
    if n_events <= 0:
        return float("inf")
    return -2 * ll + k_params * math.log(n_events)


def main():
    parser = argparse.ArgumentParser(
        description="F-SP4: Fitness-extended citation model (Bianconi-Barabási)"
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--lessons-dir", default="memory/lessons")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    lessons_dir = repo_root / args.lessons_dir

    if not lessons_dir.is_dir():
        print(f"ERROR: {lessons_dir} not found", file=sys.stderr)
        sys.exit(1)

    # Build enriched DAG
    dag, sessions, sharpes, domains = build_enriched_dag(lessons_dir)
    total_lessons = len(dag)
    n_with_sessions = sum(1 for v in sessions.values() if v is not None)
    n_with_sharpe = len(sharpes)
    n_with_domain = len(domains)
    total_edges = sum(len(v) for v in dag.values())

    print(f"=== F-SP4: FITNESS-EXTENDED CITATION MODEL ===", file=sys.stderr)
    print(f"Lessons: {total_lessons} ({n_with_sessions} w/session, "
          f"{n_with_sharpe} w/Sharpe, {n_with_domain} w/domain)", file=sys.stderr)
    print(f"Citation events: {total_edges}", file=sys.stderr)

    # Mean Sharpe for centering
    sharpe_vals = list(sharpes.values())
    mean_sharpe = sum(sharpe_vals) / len(sharpe_vals) if sharpe_vals else 5.0
    sharpe_std = (sum((s - mean_sharpe)**2 for s in sharpe_vals)
                  / max(len(sharpe_vals) - 1, 1)) ** 0.5 if len(sharpe_vals) > 1 else 1.0

    print(f"Sharpe: mean={mean_sharpe:.2f}, std={sharpe_std:.2f}, "
          f"coverage={n_with_sharpe/total_lessons*100:.1f}%", file=sys.stderr)

    # Precompute events
    print("Precomputing event structure...", file=sys.stderr)
    events = precompute_events(dag, sessions, sharpes, domains, mean_sharpe)
    print(f"Events precomputed: {len(events)}", file=sys.stderr)

    # --- Model A: Joint PA+Proximity ---
    print("\nModel A: Joint PA+Proximity (2D grid)...", file=sys.stderr)
    best_a = {"ll": -float("inf")}
    for g in [x * 0.15 for x in range(-3, 14)]:
        for l in [x * 0.01 for x in range(1, 25)]:
            ll, n = fast_ll(events, g, l)
            if ll > best_a["ll"]:
                best_a = {"gamma": g, "lambda": l, "ll": ll, "n": n}

    # Refine A
    g0, l0 = best_a["gamma"], best_a["lambda"]
    for g in [g0 + x * 0.025 for x in range(-6, 7)]:
        for l in [l0 + x * 0.002 for x in range(-6, 7)]:
            if l > 0:
                ll, n = fast_ll(events, g, l)
                if ll > best_a["ll"]:
                    best_a = {"gamma": round(g, 4), "lambda": round(l, 4),
                              "ll": ll, "n": n}

    print(f"  A: γ={best_a['gamma']}, λ={best_a['lambda']}, "
          f"LL={best_a['ll']:.2f}", file=sys.stderr)

    # --- Model B: Joint + Sharpe (cascaded: narrow γ,λ around A + β_s search) ---
    print("Model B: + Sharpe fitness (cascaded 3D)...", file=sys.stderr)
    best_b = {"ll": -float("inf")}
    g0_a, l0_a = best_a["gamma"], best_a["lambda"]

    for g in [g0_a + x * 0.05 for x in range(-4, 5)]:
        for l in [l0_a + x * 0.005 for x in range(-4, 5)]:
            if l <= 0:
                continue
            for bs in [x * 0.04 for x in range(-15, 20)]:
                ll, n = fast_ll(events, g, l, beta_s=bs)
                if ll > best_b["ll"]:
                    best_b = {"gamma": g, "lambda": l,
                              "beta_sharpe": bs, "ll": ll, "n": n}

    # Refine B
    g0, l0, bs0 = best_b["gamma"], best_b["lambda"], best_b["beta_sharpe"]
    for g in [g0 + x * 0.015 for x in range(-4, 5)]:
        for l in [l0 + x * 0.001 for x in range(-4, 5)]:
            if l <= 0:
                continue
            for bs in [bs0 + x * 0.008 for x in range(-4, 5)]:
                ll, n = fast_ll(events, g, l, beta_s=bs)
                if ll > best_b["ll"]:
                    best_b = {"gamma": round(g, 4), "lambda": round(l, 4),
                              "beta_sharpe": round(bs, 4), "ll": ll, "n": n}

    print(f"  B: γ={best_b['gamma']}, λ={best_b['lambda']}, "
          f"β_s={best_b['beta_sharpe']}, LL={best_b['ll']:.2f}", file=sys.stderr)

    # --- Model C: Full fitness (cascaded: narrow around B + β_d search) ---
    print("Model C: + Sharpe + Domain (cascaded 4D)...", file=sys.stderr)
    best_c = {"ll": -float("inf")}
    g0_b, l0_b, bs0_b = best_b["gamma"], best_b["lambda"], best_b["beta_sharpe"]

    for g in [g0_b + x * 0.05 for x in range(-3, 4)]:
        for l in [l0_b + x * 0.004 for x in range(-3, 4)]:
            if l <= 0:
                continue
            for bs in [bs0_b + x * 0.03 for x in range(-3, 4)]:
                for bd in [x * 0.08 for x in range(-8, 12)]:
                    ll, n = fast_ll(events, g, l, beta_s=bs, beta_d=bd)
                    if ll > best_c["ll"]:
                        best_c = {"gamma": g, "lambda": l,
                                  "beta_sharpe": bs, "beta_domain": bd,
                                  "ll": ll, "n": n}

    # Refine C
    g0, l0 = best_c["gamma"], best_c["lambda"]
    bs0, bd0 = best_c["beta_sharpe"], best_c["beta_domain"]
    for g in [g0 + x * 0.015 for x in range(-3, 4)]:
        for l in [l0 + x * 0.001 for x in range(-3, 4)]:
            if l <= 0:
                continue
            for bs in [bs0 + x * 0.008 for x in range(-3, 4)]:
                for bd in [bd0 + x * 0.02 for x in range(-3, 4)]:
                    ll, n = fast_ll(events, g, l, beta_s=bs, beta_d=bd)
                    if ll > best_c["ll"]:
                        best_c = {
                            "gamma": round(g, 4), "lambda": round(l, 4),
                            "beta_sharpe": round(bs, 4),
                            "beta_domain": round(bd, 4),
                            "ll": ll, "n": n}

    print(f"  C: γ={best_c['gamma']}, λ={best_c['lambda']}, "
          f"β_s={best_c['beta_sharpe']}, β_d={best_c['beta_domain']}, "
          f"LL={best_c['ll']:.2f}", file=sys.stderr)

    n_events = best_a["n"]
    bic_a = compute_bic(best_a["ll"], 2, n_events)
    bic_b = compute_bic(best_b["ll"], 3, n_events)
    bic_c = compute_bic(best_c["ll"], 4, n_events)

    # Uniform baseline
    ll_uniform, _ = fast_ll(events, 0, 0)

    ll_gain_sharpe = best_b["ll"] - best_a["ll"]
    ll_gain_full = best_c["ll"] - best_a["ll"]
    ll_gain_joint_vs_uniform = best_a["ll"] - ll_uniform

    results = {
        "metadata": {
            "tool": "f_sp4_fitness_model.py",
            "frontier": "F-SP4",
            "session": "S389",
            "total_lessons": total_lessons,
            "n_with_sharpe": n_with_sharpe,
            "n_with_domain": n_with_domain,
            "sharpe_mean": round(mean_sharpe, 2),
            "sharpe_std": round(sharpe_std, 2),
            "total_edges": total_edges,
            "n_events": n_events,
        },
        "models": {
            "A_joint": {
                "params": {"gamma": best_a["gamma"], "lambda": best_a["lambda"]},
                "ll": round(best_a["ll"], 2),
                "bic": round(bic_a, 2),
                "n_params": 2,
            },
            "B_fitness_sharpe": {
                "params": {
                    "gamma": best_b["gamma"], "lambda": best_b["lambda"],
                    "beta_sharpe": best_b["beta_sharpe"],
                },
                "ll": round(best_b["ll"], 2),
                "bic": round(bic_b, 2),
                "n_params": 3,
            },
            "C_fitness_full": {
                "params": {
                    "gamma": best_c["gamma"], "lambda": best_c["lambda"],
                    "beta_sharpe": best_c["beta_sharpe"],
                    "beta_domain": best_c["beta_domain"],
                },
                "ll": round(best_c["ll"], 2),
                "bic": round(bic_c, 2),
                "n_params": 4,
            },
        },
        "comparison": {
            "delta_bic_B_vs_A": round(bic_a - bic_b, 2),
            "delta_bic_C_vs_A": round(bic_a - bic_c, 2),
            "delta_bic_C_vs_B": round(bic_b - bic_c, 2),
            "ll_gain_sharpe_over_joint": round(ll_gain_sharpe, 2),
            "ll_gain_full_over_joint": round(ll_gain_full, 2),
            "ll_gain_joint_vs_uniform": round(ll_gain_joint_vs_uniform, 2),
            "sharpe_share_of_residual": round(
                ll_gain_sharpe / abs(ll_gain_joint_vs_uniform), 4
            ) if ll_gain_joint_vs_uniform != 0 else None,
        },
    }

    # Interpret
    bs = best_b.get("beta_sharpe", 0)
    delta_ba = bic_a - bic_b
    delta_ca = bic_a - bic_c
    delta_cb = bic_b - bic_c

    if bs > 0.05:
        sharpe_interp = f"POSITIVE (β={bs:.3f}): higher Sharpe → more cited"
    elif bs < -0.05:
        sharpe_interp = f"NEGATIVE (β={bs:.3f}): higher Sharpe → LESS cited"
    else:
        sharpe_interp = f"NEGLIGIBLE (β={bs:.3f}): Sharpe does not predict citation"

    def bic_label(d):
        if d > 10:
            return "STRONG"
        elif d > 2:
            return "WEAK"
        elif d > -2:
            return "INCONCLUSIVE"
        else:
            return "REJECTED"

    results["interpretation"] = {
        "sharpe_effect": sharpe_interp,
        "bic_B_vs_A": bic_label(delta_ba),
        "bic_C_vs_A": bic_label(delta_ca),
        "bic_C_vs_B": bic_label(delta_cb),
    }

    if delta_ba > 10:
        verdict = (f"FITNESS CONFIRMED: Sharpe predicts citation beyond PA+proximity "
                   f"(ΔBIC={delta_ba:+.1f}, β_s={bs:.3f})")
    elif delta_ba > 2:
        verdict = (f"FITNESS WEAK: marginal Sharpe effect "
                   f"(ΔBIC={delta_ba:+.1f}, β_s={bs:.3f})")
    elif delta_ba > -2:
        verdict = (f"FITNESS NULL: Sharpe adds nothing "
                   f"(ΔBIC={delta_ba:+.1f}). Two-force model sufficient.")
    else:
        verdict = (f"FITNESS REJECTED: Sharpe overfits "
                   f"(ΔBIC={delta_ba:+.1f}). Two-force model is best.")

    results["verdict"] = verdict

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"F-SP4: FITNESS-EXTENDED CITATION MODEL (S389)")
        print(f"{'='*60}")
        print(f"\nData: {total_lessons}L, {total_edges} citations, "
              f"{n_events} conditional events")
        print(f"Sharpe: {n_with_sharpe}/{total_lessons} "
              f"({n_with_sharpe/total_lessons*100:.0f}%), "
              f"mean={mean_sharpe:.2f} ± {sharpe_std:.2f}")
        print(f"Domain: {n_with_domain}/{total_lessons} "
              f"({n_with_domain/total_lessons*100:.0f}%)")

        print(f"\n--- Models (BIC, lower=better) ---")
        for label, key in [("A: PA+Proximity", "A_joint"),
                           ("B: +Sharpe", "B_fitness_sharpe"),
                           ("C: +Sharpe+Domain", "C_fitness_full")]:
            m = results["models"][key]
            params = ", ".join(f"{k}={v}" for k, v in m["params"].items())
            print(f"  {label:22s}: BIC={m['bic']:10.2f}  LL={m['ll']:10.2f}  "
                  f"[{params}]")

        print(f"\n--- ΔBIC (positive → fitness helps) ---")
        c = results["comparison"]
        print(f"  B vs A (Sharpe):       {c['delta_bic_B_vs_A']:+.2f}  "
              f"[{bic_label(delta_ba)}]")
        print(f"  C vs A (full):         {c['delta_bic_C_vs_A']:+.2f}  "
              f"[{bic_label(delta_ca)}]")
        print(f"  C vs B (domain added): {c['delta_bic_C_vs_B']:+.2f}  "
              f"[{bic_label(delta_cb)}]")

        print(f"\n--- LL decomposition ---")
        print(f"  Joint vs Uniform: {c['ll_gain_joint_vs_uniform']:+.2f}")
        print(f"  Sharpe over Joint: {c['ll_gain_sharpe_over_joint']:+.2f}")
        print(f"  Full over Joint: {c['ll_gain_full_over_joint']:+.2f}")
        if c.get("sharpe_share_of_residual") is not None:
            print(f"  Sharpe share: {c['sharpe_share_of_residual']*100:.1f}% "
                  f"of joint LL gain")

        print(f"\n  Sharpe direction: {sharpe_interp}")

        print(f"\n{'='*60}")
        print(f"VERDICT: {verdict}")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
