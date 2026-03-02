#!/usr/bin/env python3
"""F-SP4: Out-of-sample validation of joint PA+proximity model.

Splits citation data temporally (train S1-S370, test S371+).
Fits models on training data, evaluates on held-out test data.
Tests whether the joint model generalizes beyond its training set.

Usage:
    python3 experiments/stochastic-processes/f_sp4_oos_validation.py
    python3 experiments/stochastic-processes/f_sp4_oos_validation.py --json
    python3 experiments/stochastic-processes/f_sp4_oos_validation.py --split 380
"""

import argparse
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def extract_lesson_number(filename: str):
    m = re.match(r"L-(\d+)\.md", filename)
    return int(m.group(1)) if m else None


def parse_session(filepath: Path):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read(2000)
    m = re.search(r"session:\s*S?(\d+)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"\*{0,2}Session\*{0,2}:\s*S?(\d+)", text)
    if m:
        return int(m.group(1))
    return None


def parse_cites(filepath: Path):
    refs = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("Cites:"):
                refs.extend(int(x) for x in re.findall(r"\bL-(\d+)\b", line))
                break
    return refs


def parse_sharpe(filepath: Path):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.search(r"Sharpe:\s*(\d+(?:\.\d+)?)", line)
            if m:
                return float(m.group(1))
    return None


def build_citation_dag(lessons_dir: Path):
    dag = {}
    sessions = {}
    sharpe_scores = {}
    for fname in sorted(os.listdir(lessons_dir)):
        num = extract_lesson_number(fname)
        if num is None:
            continue
        fpath = lessons_dir / fname
        cites = parse_cites(fpath)
        prior_cites = [c for c in cites if c < num]
        dag[num] = prior_cites
        sess = parse_session(fpath)
        if sess is not None:
            sessions[num] = sess
        sh = parse_sharpe(fpath)
        if sh is not None:
            sharpe_scores[num] = sh
    return dag, sessions, sharpe_scores


def _session_gap(src, nd, src_sess, nd_sess):
    if src_sess is not None and nd_sess is not None:
        return abs(src_sess - nd_sess)
    return abs(src - nd) / 2.0


def _weight(k, src, nd, src_sess, nd_sess, sessions, gamma, lam, model):
    if model == "pa":
        return (k + 1) ** gamma
    elif model == "proximity":
        ds = _session_gap(src, nd, src_sess, nd_sess)
        return math.exp(-lam * ds)
    elif model == "joint":
        ds = _session_gap(src, nd, src_sess, nd_sess)
        return ((k + 1) ** gamma) * math.exp(-lam * ds)
    elif model == "uniform":
        return 1.0
    return 1.0


def conditional_log_likelihood(dag, sessions, gamma, lam, model,
                               lesson_filter=None):
    """Compute conditional LL, optionally restricted to citing lessons in filter."""
    degree = defaultdict(int)
    all_nodes = set()
    ll = 0.0
    n_events = 0

    for src in sorted(dag.keys()):
        all_nodes.add(src)
        src_sess = sessions.get(src)

        if not dag[src]:
            # Still update degrees for targets
            for target in dag[src]:
                degree[target] += 1
            continue

        # Skip if src not in evaluation set (but still track degrees)
        if lesson_filter is not None and src not in lesson_filter:
            for target in dag[src]:
                degree[target] += 1
            continue

        pool = [nd for nd in all_nodes if nd < src]
        if not pool:
            for target in dag[src]:
                degree[target] += 1
            continue

        for target in dag[src]:
            if target not in all_nodes:
                continue

            k_t = degree[target]
            w_target = _weight(k_t, src, target, src_sess,
                               sessions.get(target), sessions, gamma, lam,
                               model)

            w_sum = 0.0
            for nd in pool:
                k_nd = degree[nd]
                w_nd = _weight(k_nd, src, nd, src_sess, sessions.get(nd),
                               sessions, gamma, lam, model)
                w_sum += w_nd

            if w_sum > 0 and w_target > 0:
                ll += math.log(w_target / w_sum)
                n_events += 1

        for target in dag[src]:
            degree[target] += 1

    return ll, n_events


def grid_search(dag, sessions, model, lesson_filter=None):
    best_ll = -float("inf")
    best_params = {}

    if model == "uniform":
        ll, n = conditional_log_likelihood(dag, sessions, 0, 0, "uniform",
                                           lesson_filter)
        return {"ll": ll, "n_events": n, "params": {}}

    if model == "pa":
        gamma_range = [x * 0.1 for x in range(-5, 25)]
        for g in gamma_range:
            ll, n = conditional_log_likelihood(dag, sessions, g, 0, "pa",
                                               lesson_filter)
            if ll > best_ll:
                best_ll = ll
                best_params = {"gamma": g, "ll": ll, "n_events": n}
        g0 = best_params.get("gamma", 0)
        for g in [g0 + x * 0.02 for x in range(-5, 6)]:
            ll, n = conditional_log_likelihood(dag, sessions, g, 0, "pa",
                                               lesson_filter)
            if ll > best_ll:
                best_ll = ll
                best_params = {"gamma": round(g, 3), "ll": ll, "n_events": n}
        return best_params

    if model == "proximity":
        lam_range = [x * 0.005 for x in range(1, 40)]
        for l in lam_range:
            ll, n = conditional_log_likelihood(dag, sessions, 0, l,
                                               "proximity", lesson_filter)
            if ll > best_ll:
                best_ll = ll
                best_params = {"lambda": l, "ll": ll, "n_events": n}
        l0 = best_params.get("lambda", 0.01)
        for l in [l0 + x * 0.001 for x in range(-5, 6)]:
            if l > 0:
                ll, n = conditional_log_likelihood(dag, sessions, 0, l,
                                                   "proximity", lesson_filter)
                if ll > best_ll:
                    best_ll = ll
                    best_params = {"lambda": round(l, 4), "ll": ll,
                                   "n_events": n}
        return best_params

    if model == "joint":
        gamma_range = [x * 0.1 for x in range(-5, 20)]
        lam_range = [x * 0.01 for x in range(1, 30)]
        for g in gamma_range:
            for l in lam_range:
                ll, n = conditional_log_likelihood(dag, sessions, g, l,
                                                   "joint", lesson_filter)
                if ll > best_ll:
                    best_ll = ll
                    best_params = {"gamma": g, "lambda": l, "ll": ll,
                                   "n_events": n}
        g0 = best_params.get("gamma", 0)
        l0 = best_params.get("lambda", 0.01)
        for g in [g0 + x * 0.02 for x in range(-5, 6)]:
            for l in [l0 + x * 0.002 for x in range(-5, 6)]:
                if l > 0:
                    ll, n = conditional_log_likelihood(dag, sessions, g, l,
                                                       "joint", lesson_filter)
                    if ll > best_ll:
                        best_ll = ll
                        best_params = {"gamma": round(g, 3),
                                       "lambda": round(l, 4),
                                       "ll": ll, "n_events": n}
        return best_params

    return best_params


def compute_bic(ll, k_params, n_events):
    if n_events <= 0:
        return float("inf")
    return -2 * ll + k_params * math.log(n_events)


def evaluate_with_params(dag, sessions, gamma, lam, model, lesson_filter=None):
    """Evaluate a model with fixed parameters on a subset of data."""
    ll, n = conditional_log_likelihood(dag, sessions, gamma, lam, model,
                                       lesson_filter)
    return {"ll": ll, "n_events": n}


def main():
    parser = argparse.ArgumentParser(
        description="F-SP4: Out-of-sample validation")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--split", type=int, default=370,
                        help="Session split point (train <= split, test > split)")
    parser.add_argument("--lessons-dir", default="memory/lessons")
    args = parser.parse_args()

    lessons_dir = REPO_ROOT / args.lessons_dir
    if not lessons_dir.is_dir():
        print(f"ERROR: {lessons_dir} not found", file=sys.stderr)
        sys.exit(1)

    split_session = args.split

    # Build full DAG
    dag, sessions, sharpe_scores = build_citation_dag(lessons_dir)
    total_lessons = len(dag)
    total_edges = sum(len(v) for v in dag.values())
    session_coverage = sum(1 for v in sessions.values() if v is not None)

    # Split lessons by session
    train_lessons = set()
    test_lessons = set()
    no_session = set()
    for num in dag:
        sess = sessions.get(num)
        if sess is None:
            no_session.add(num)
            train_lessons.add(num)  # assign no-session to train
        elif sess <= split_session:
            train_lessons.add(num)
        else:
            test_lessons.add(num)

    train_edges = sum(len(dag[n]) for n in train_lessons if n in dag)
    test_edges = sum(len(dag[n]) for n in test_lessons if n in dag)

    print(f"=== F-SP4: OUT-OF-SAMPLE VALIDATION (split=S{split_session}) ===",
          file=sys.stderr)
    print(f"Total: {total_lessons} lessons, {total_edges} edges",
          file=sys.stderr)
    print(f"Train (≤S{split_session}): {len(train_lessons)} lessons, "
          f"{train_edges} edges", file=sys.stderr)
    print(f"Test (>S{split_session}): {len(test_lessons)} lessons, "
          f"{test_edges} edges", file=sys.stderr)
    print(f"No session: {len(no_session)} (assigned to train)", file=sys.stderr)

    # === PHASE 1: Fit on training set ===
    print("\n--- Phase 1: Training ---", file=sys.stderr)
    print("Fitting models on training data...", file=sys.stderr)

    train_uniform = grid_search(dag, sessions, "uniform", train_lessons)
    train_pa = grid_search(dag, sessions, "pa", train_lessons)
    train_prox = grid_search(dag, sessions, "proximity", train_lessons)
    train_joint = grid_search(dag, sessions, "joint", train_lessons)

    train_n = train_pa.get("n_events", 1)

    print(f"  Uniform:   LL={train_uniform['ll']:.2f} (n={train_uniform['n_events']})",
          file=sys.stderr)
    print(f"  PA:        LL={train_pa['ll']:.2f}, γ={train_pa.get('gamma')}",
          file=sys.stderr)
    print(f"  Proximity: LL={train_prox['ll']:.2f}, λ={train_prox.get('lambda')}",
          file=sys.stderr)
    print(f"  Joint:     LL={train_joint['ll']:.2f}, γ={train_joint.get('gamma')}, "
          f"λ={train_joint.get('lambda')}", file=sys.stderr)

    # === PHASE 2: Evaluate on test set with TRAIN parameters ===
    print("\n--- Phase 2: Test (train params) ---", file=sys.stderr)

    test_uniform = evaluate_with_params(dag, sessions, 0, 0, "uniform",
                                         test_lessons)
    test_pa = evaluate_with_params(dag, sessions, train_pa.get("gamma", 0), 0,
                                    "pa", test_lessons)
    test_prox = evaluate_with_params(dag, sessions, 0,
                                      train_prox.get("lambda", 0.01),
                                      "proximity", test_lessons)
    test_joint = evaluate_with_params(dag, sessions,
                                       train_joint.get("gamma", 0),
                                       train_joint.get("lambda", 0.01),
                                       "joint", test_lessons)

    test_n = test_pa.get("n_events", 1)

    print(f"  Uniform:   LL={test_uniform['ll']:.2f} (n={test_uniform['n_events']})",
          file=sys.stderr)
    print(f"  PA:        LL={test_pa['ll']:.2f}", file=sys.stderr)
    print(f"  Proximity: LL={test_prox['ll']:.2f}", file=sys.stderr)
    print(f"  Joint:     LL={test_joint['ll']:.2f}", file=sys.stderr)

    # === PHASE 3: Re-fit on test set (oracle comparison) ===
    print("\n--- Phase 3: Test (oracle refit) ---", file=sys.stderr)

    oracle_pa = grid_search(dag, sessions, "pa", test_lessons)
    oracle_prox = grid_search(dag, sessions, "proximity", test_lessons)
    oracle_joint = grid_search(dag, sessions, "joint", test_lessons)

    print(f"  PA oracle:        LL={oracle_pa['ll']:.2f}, γ={oracle_pa.get('gamma')}",
          file=sys.stderr)
    print(f"  Proximity oracle: LL={oracle_prox['ll']:.2f}, "
          f"λ={oracle_prox.get('lambda')}", file=sys.stderr)
    print(f"  Joint oracle:     LL={oracle_joint['ll']:.2f}, "
          f"γ={oracle_joint.get('gamma')}, λ={oracle_joint.get('lambda')}",
          file=sys.stderr)

    # === Compute generalization metrics ===
    # LL improvement over uniform baseline
    def ll_improvement(model_ll, uniform_ll):
        if uniform_ll == 0:
            return 0
        return (model_ll - uniform_ll) / abs(uniform_ll) * 100

    train_improvements = {
        "pa": ll_improvement(train_pa["ll"], train_uniform["ll"]),
        "proximity": ll_improvement(train_prox["ll"], train_uniform["ll"]),
        "joint": ll_improvement(train_joint["ll"], train_uniform["ll"]),
    }

    test_improvements = {
        "pa": ll_improvement(test_pa["ll"], test_uniform["ll"]),
        "proximity": ll_improvement(test_prox["ll"], test_uniform["ll"]),
        "joint": ll_improvement(test_joint["ll"], test_uniform["ll"]),
    }

    oracle_improvements = {
        "pa": ll_improvement(oracle_pa["ll"], test_uniform["ll"]),
        "proximity": ll_improvement(oracle_prox["ll"], test_uniform["ll"]),
        "joint": ll_improvement(oracle_joint["ll"], test_uniform["ll"]),
    }

    # Transfer efficiency: how much of oracle improvement does train achieve?
    transfer_efficiency = {}
    for m in ["pa", "proximity", "joint"]:
        if oracle_improvements[m] > 0:
            transfer_efficiency[m] = round(
                test_improvements[m] / oracle_improvements[m] * 100, 1)
        else:
            transfer_efficiency[m] = None

    # Parameter stability
    param_stability = {
        "gamma": {
            "train": train_joint.get("gamma"),
            "oracle": oracle_joint.get("gamma"),
            "delta": round(abs((train_joint.get("gamma", 0) -
                                oracle_joint.get("gamma", 0))), 4),
        },
        "lambda": {
            "train": train_joint.get("lambda"),
            "oracle": oracle_joint.get("lambda"),
            "delta": round(abs((train_joint.get("lambda", 0) -
                                oracle_joint.get("lambda", 0))), 4),
        },
    }

    # Per-lesson LL (normalized)
    per_lesson_ll = {
        "train": {
            "uniform": round(train_uniform["ll"] / max(train_n, 1), 4),
            "pa": round(train_pa["ll"] / max(train_n, 1), 4),
            "proximity": round(train_prox["ll"] / max(train_n, 1), 4),
            "joint": round(train_joint["ll"] / max(train_n, 1), 4),
        },
        "test_transfer": {
            "uniform": round(test_uniform["ll"] / max(test_n, 1), 4),
            "pa": round(test_pa["ll"] / max(test_n, 1), 4),
            "proximity": round(test_prox["ll"] / max(test_n, 1), 4),
            "joint": round(test_joint["ll"] / max(test_n, 1), 4),
        },
        "test_oracle": {
            "pa": round(oracle_pa["ll"] / max(test_n, 1), 4),
            "proximity": round(oracle_prox["ll"] / max(test_n, 1), 4),
            "joint": round(oracle_joint["ll"] / max(test_n, 1), 4),
        },
    }

    # BIC on test set
    test_bic = {
        "uniform": round(compute_bic(test_uniform["ll"], 0, test_n), 2),
        "pa_transfer": round(compute_bic(test_pa["ll"], 1, test_n), 2),
        "proximity_transfer": round(compute_bic(test_prox["ll"], 1, test_n), 2),
        "joint_transfer": round(compute_bic(test_joint["ll"], 2, test_n), 2),
        "pa_oracle": round(compute_bic(oracle_pa["ll"], 1, test_n), 2),
        "proximity_oracle": round(compute_bic(oracle_prox["ll"], 1, test_n), 2),
        "joint_oracle": round(compute_bic(oracle_joint["ll"], 2, test_n), 2),
    }

    # Proximity magnitude check at test time
    # Compute ratio of near (0-5) vs far (50+) citation rates in test set
    degree = defaultdict(int)
    all_nodes = set()
    near_cites = 0
    far_cites = 0
    near_exposure = 0
    far_exposure = 0

    for src in sorted(dag.keys()):
        all_nodes.add(src)
        src_sess = sessions.get(src)
        if src not in test_lessons or not dag[src]:
            for t in dag[src]:
                degree[t] += 1
            continue
        pool = [nd for nd in all_nodes if nd < src]
        if not pool:
            for t in dag[src]:
                degree[t] += 1
            continue
        for nd in pool:
            gap = _session_gap(src, nd, src_sess, sessions.get(nd))
            if gap <= 5:
                near_exposure += len(dag[src])
            elif gap >= 50:
                far_exposure += len(dag[src])
        for target in dag[src]:
            if target in all_nodes:
                gap = _session_gap(src, target, src_sess,
                                   sessions.get(target))
                if gap <= 5:
                    near_cites += 1
                elif gap >= 50:
                    far_cites += 1
        for t in dag[src]:
            degree[t] += 1

    near_rate = near_cites / max(near_exposure, 1)
    far_rate = far_cites / max(far_exposure, 1)
    proximity_ratio = near_rate / max(far_rate, 1e-10)

    proximity_check = {
        "near_cites": near_cites,
        "near_exposure": near_exposure,
        "near_rate": round(near_rate, 6),
        "far_cites": far_cites,
        "far_exposure": far_exposure,
        "far_rate": round(far_rate, 6),
        "proximity_ratio": round(proximity_ratio, 1),
    }

    # === Verdict ===
    joint_test_vs_uniform = test_improvements["joint"]
    joint_transfer_eff = transfer_efficiency.get("joint", 0)
    gamma_stable = param_stability["gamma"]["delta"] < 0.3
    lambda_stable = param_stability["lambda"]["delta"] < 0.01

    verdict_parts = []
    if joint_test_vs_uniform > 50:
        verdict_parts.append(f"Joint OOS LL improvement: {joint_test_vs_uniform:.1f}% over uniform (STRONG)")
    elif joint_test_vs_uniform > 20:
        verdict_parts.append(f"Joint OOS LL improvement: {joint_test_vs_uniform:.1f}% over uniform (MODERATE)")
    else:
        verdict_parts.append(f"Joint OOS LL improvement: {joint_test_vs_uniform:.1f}% over uniform (WEAK)")

    if joint_transfer_eff and joint_transfer_eff > 80:
        verdict_parts.append(f"Transfer efficiency: {joint_transfer_eff:.0f}% (excellent generalization)")
    elif joint_transfer_eff and joint_transfer_eff > 50:
        verdict_parts.append(f"Transfer efficiency: {joint_transfer_eff:.0f}% (good generalization)")
    else:
        verdict_parts.append(f"Transfer efficiency: {joint_transfer_eff}% (poor generalization)")

    verdict_parts.append(f"γ stable: {'YES' if gamma_stable else 'NO'} "
                         f"(Δ={param_stability['gamma']['delta']:.3f})")
    verdict_parts.append(f"λ stable: {'YES' if lambda_stable else 'NO'} "
                         f"(Δ={param_stability['lambda']['delta']:.4f})")
    verdict_parts.append(f"Proximity ratio (test): {proximity_ratio:.1f}×")

    overall = "CONFIRMED" if (joint_test_vs_uniform > 20 and
                              (joint_transfer_eff or 0) > 50 and
                              gamma_stable) else "PARTIAL"

    results = {
        "metadata": {
            "experiment": "f-sp4-oos-validation",
            "session": "S393",
            "frontier": "F-SP4",
            "split_session": split_session,
            "total_lessons": total_lessons,
            "train_lessons": len(train_lessons),
            "test_lessons": len(test_lessons),
            "no_session_lessons": len(no_session),
            "total_edges": total_edges,
            "train_edges": train_edges,
            "test_edges": test_edges,
            "session_coverage": round(session_coverage / total_lessons, 4),
        },
        "training": {
            "uniform": {"ll": round(train_uniform["ll"], 2),
                        "n_events": train_uniform["n_events"]},
            "pa": {"ll": round(train_pa["ll"], 2),
                   "gamma": train_pa.get("gamma"),
                   "n_events": train_pa.get("n_events")},
            "proximity": {"ll": round(train_prox["ll"], 2),
                          "lambda": train_prox.get("lambda"),
                          "n_events": train_prox.get("n_events")},
            "joint": {"ll": round(train_joint["ll"], 2),
                      "gamma": train_joint.get("gamma"),
                      "lambda": train_joint.get("lambda"),
                      "n_events": train_joint.get("n_events")},
        },
        "test_transfer": {
            "uniform": {"ll": round(test_uniform["ll"], 2),
                        "n_events": test_uniform["n_events"]},
            "pa": {"ll": round(test_pa["ll"], 2),
                   "n_events": test_pa["n_events"]},
            "proximity": {"ll": round(test_prox["ll"], 2),
                          "n_events": test_prox["n_events"]},
            "joint": {"ll": round(test_joint["ll"], 2),
                      "n_events": test_joint["n_events"]},
        },
        "test_oracle": {
            "pa": {"ll": round(oracle_pa["ll"], 2),
                   "gamma": oracle_pa.get("gamma"),
                   "n_events": oracle_pa.get("n_events")},
            "proximity": {"ll": round(oracle_prox["ll"], 2),
                          "lambda": oracle_prox.get("lambda"),
                          "n_events": oracle_prox.get("n_events")},
            "joint": {"ll": round(oracle_joint["ll"], 2),
                      "gamma": oracle_joint.get("gamma"),
                      "lambda": oracle_joint.get("lambda"),
                      "n_events": oracle_joint.get("n_events")},
        },
        "improvements_pct": {
            "train": {k: round(v, 2) for k, v in train_improvements.items()},
            "test_transfer": {k: round(v, 2) for k, v in test_improvements.items()},
            "test_oracle": {k: round(v, 2) for k, v in oracle_improvements.items()},
        },
        "transfer_efficiency_pct": transfer_efficiency,
        "param_stability": param_stability,
        "per_event_ll": per_lesson_ll,
        "test_bic": test_bic,
        "proximity_check": proximity_check,
        "verdict": "; ".join(verdict_parts),
        "overall": overall,
    }

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n{'='*65}")
        print(f"F-SP4: OUT-OF-SAMPLE VALIDATION (split=S{split_session})")
        print(f"{'='*65}")
        print(f"\nData: {total_lessons} lessons, {total_edges} edges")
        print(f"Train (≤S{split_session}): {len(train_lessons)} lessons, "
              f"{train_edges} edges")
        print(f"Test  (>S{split_session}): {len(test_lessons)} lessons, "
              f"{test_edges} edges")

        print(f"\n--- Training Fit ---")
        print(f"  Uniform:   LL={train_uniform['ll']:.2f}")
        print(f"  PA:        LL={train_pa['ll']:.2f}, "
              f"γ={train_pa.get('gamma')}")
        print(f"  Proximity: LL={train_prox['ll']:.2f}, "
              f"λ={train_prox.get('lambda')}")
        print(f"  Joint:     LL={train_joint['ll']:.2f}, "
              f"γ={train_joint.get('gamma')}, λ={train_joint.get('lambda')}")

        print(f"\n--- Test: Train Params (transfer) ---")
        print(f"  Uniform:   LL={test_uniform['ll']:.2f} "
              f"(n={test_uniform['n_events']})")
        print(f"  PA:        LL={test_pa['ll']:.2f} "
              f"({test_improvements['pa']:+.1f}% vs uniform)")
        print(f"  Proximity: LL={test_prox['ll']:.2f} "
              f"({test_improvements['proximity']:+.1f}% vs uniform)")
        print(f"  Joint:     LL={test_joint['ll']:.2f} "
              f"({test_improvements['joint']:+.1f}% vs uniform)")

        print(f"\n--- Test: Oracle Refit ---")
        print(f"  PA oracle:        LL={oracle_pa['ll']:.2f}, "
              f"γ={oracle_pa.get('gamma')}")
        print(f"  Proximity oracle: LL={oracle_prox['ll']:.2f}, "
              f"λ={oracle_prox.get('lambda')}")
        print(f"  Joint oracle:     LL={oracle_joint['ll']:.2f}, "
              f"γ={oracle_joint.get('gamma')}, λ={oracle_joint.get('lambda')}")

        print(f"\n--- Transfer Efficiency ---")
        for m in ["pa", "proximity", "joint"]:
            eff = transfer_efficiency.get(m, "N/A")
            print(f"  {m:12s}: {eff}%")

        print(f"\n--- Parameter Stability ---")
        for p in ["gamma", "lambda"]:
            ps = param_stability[p]
            print(f"  {p}: train={ps['train']}, oracle={ps['oracle']}, "
                  f"Δ={ps['delta']}")

        print(f"\n--- Per-Event LL ---")
        for split_name in ["train", "test_transfer", "test_oracle"]:
            pe = per_lesson_ll[split_name]
            print(f"  {split_name}:")
            for m, v in pe.items():
                print(f"    {m:12s}: {v:.4f}")

        print(f"\n--- Proximity Check (test set) ---")
        pc = proximity_check
        print(f"  Near (≤5):  {pc['near_cites']} cites / "
              f"{pc['near_exposure']} exposure = {pc['near_rate']:.6f}")
        print(f"  Far (≥50):  {pc['far_cites']} cites / "
              f"{pc['far_exposure']} exposure = {pc['far_rate']:.6f}")
        print(f"  Ratio:      {pc['proximity_ratio']}×")

        print(f"\n--- Test BIC ---")
        for k, v in test_bic.items():
            print(f"  {k:25s}: {v:.2f}")

        print(f"\n{'='*65}")
        print(f"VERDICT: {results['verdict']}")
        print(f"OVERALL: {overall}")
        print(f"{'='*65}")

    return results


if __name__ == "__main__":
    main()
