#!/usr/bin/env python3
"""
F-SP4 extension: Agent-level covariates in citation attachment.
Session: S394 | Domain: stochastic-processes | Lane: DOMEX-SP-S394

Extends the F-SP4 joint PA+proximity model with per-agent session attributes
from F-META16. Tests whether the producing agent's profile predicts which
lessons get cited, beyond degree and recency.

Models compared:
  - Baseline (joint):     w = (k+1)^γ * exp(-λ*Δs)
  - +session_type:        w = baseline * exp(β_domex * is_domex)
  - +citation_reach:      w = baseline * exp(β_reach * log1p(reach))
  - +scope:               w = baseline * exp(β_scope * scope)
  - Full agent:           w = baseline * exp(β_domex*is_domex + β_reach*log1p(reach))

Compare via BIC. If agent covariates improve fit (ΔBIC>10), session-level
attributes are a new citation force beyond network topology and recency.
"""

import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path("/mnt/c/Users/canac/REPOSITORIES/swarm")
LESSONS_DIR = REPO / "memory" / "lessons"
OUTPUT_FILE = REPO / "experiments" / "stochastic-processes" / "f-sp4-agent-covariates-s394.json"


# ============================================================================
# Lesson and session parsing (from proximity_pa.py + f_meta16)
# ============================================================================

def parse_lesson(filepath):
    """Parse lesson file for session, domain, cites."""
    lid_m = re.match(r"L-(\d+)", filepath.stem)
    if not lid_m:
        return None
    lid = int(lid_m.group(1))
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    # Session
    sm = re.search(r"[Ss]ession:\s*S?(\d+)", text, re.IGNORECASE)
    session = int(sm.group(1)) if sm else None

    # Domain
    dm = re.search(r"Domain:\s*(\S+)", text, re.IGNORECASE)
    domain = dm.group(1).lower().rstrip(",;") if dm else "unknown"

    # Cites (header only — same as proximity_pa.py)
    cites = []
    for line in text.split("\n"):
        if line.startswith("Cites:"):
            cites = [int(x) for x in re.findall(r"\bL-(\d+)\b", line)]
            break

    return {
        "id": lid,
        "session": session,
        "domain": domain,
        "cites": [c for c in cites if c < lid],  # prior only
    }


def load_all_lessons():
    """Load and parse all lesson files."""
    lessons = {}
    for lf in sorted(LESSONS_DIR.glob("L-*.md")):
        parsed = parse_lesson(lf)
        if parsed:
            lessons[parsed["id"]] = parsed
    return lessons


def compute_session_attributes(lessons):
    """Compute per-session attributes (from F-META16 methodology)."""
    # Group lessons by session
    session_lessons = defaultdict(list)
    for lid, ldata in lessons.items():
        if ldata["session"]:
            session_lessons[ldata["session"]].append(lid)

    # Compute attributes
    attrs = {}
    for s, lids in session_lessons.items():
        # Production
        n_lessons = len(lids)

        # Citation reach: unique existing lessons cited by this session's outputs
        citation_reach = set()
        for lid in lids:
            for cited in lessons[lid]["cites"]:
                if cited in lessons:
                    citation_reach.add(cited)

        # Knowledge scope: distinct domains
        domains = set(lessons[lid]["domain"] for lid in lids)

        # Session type (from commit messages — approximate from lesson domains)
        # We don't have commits here, so use lesson-level proxy
        has_meta = "meta" in domains
        is_diverse = len(domains) > 3

        attrs[s] = {
            "n_lessons": n_lessons,
            "citation_reach": len(citation_reach),
            "knowledge_scope": len(domains),
            "domains": sorted(domains),
            "is_focused": len(domains) <= 2,
        }

    return attrs


def classify_session_from_commits():
    """Classify sessions as DOMEX/mixed/maintenance from git log."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO), "log", "--oneline", "--all", "--no-merges"],
            capture_output=True, text=True, timeout=30
        )
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
    except Exception:
        return {}

    session_msgs = defaultdict(list)
    for line in lines:
        m = re.match(r"[0-9a-f]+ (.+)$", line)
        if not m:
            continue
        msg = m.group(1)
        sm = re.search(r"\[S(\d+)\]", msg)
        if sm:
            session_msgs[int(sm.group(1))].append(msg.lower())

    session_types = {}
    for s, msgs in session_msgs.items():
        has_domex = any("domex" in m for m in msgs)
        has_maintenance = any(kw in " ".join(msgs) for kw in [
            "handoff", "state-sync", "trim", "maintenance", "harvest"
        ])
        if has_domex:
            session_types[s] = "domex"
        elif has_maintenance:
            session_types[s] = "maintenance"
        else:
            session_types[s] = "mixed"

    return session_types


# ============================================================================
# Citation model with agent covariates
# ============================================================================

def compute_ll(lessons, session_attrs, session_types,
               gamma, lam, beta_domex=0, beta_reach=0, model="baseline"):
    """Conditional log-likelihood with optional agent covariates.

    For each citation event (src cites target):
      P(target | pool) = w(target) / sum(w(i) for i in pool)

    Weight models:
      baseline:  (k+1)^γ * exp(-λ*Δs)
      +domex:    baseline * exp(β_domex * is_domex(producing_session))
      +reach:    baseline * exp(β_reach * log1p(reach))
      full:      baseline * exp(β_domex * is_domex + β_reach * log1p(reach))
    """
    degree = defaultdict(int)
    all_nodes = set()
    ll = 0.0
    n_events = 0

    for src in sorted(lessons.keys()):
        all_nodes.add(src)
        src_sess = lessons[src]["session"]
        cites = lessons[src]["cites"]

        if not cites:
            continue

        pool = [nd for nd in all_nodes if nd < src]
        if not pool:
            continue

        for target in cites:
            if target not in all_nodes:
                continue

            # Compute target weight
            w_target = _weight(target, src, lessons, session_attrs, session_types,
                               degree, gamma, lam, beta_domex, beta_reach, model)

            # Pool sum
            w_sum = 0.0
            for nd in pool:
                w_nd = _weight(nd, src, lessons, session_attrs, session_types,
                               degree, gamma, lam, beta_domex, beta_reach, model)
                w_sum += w_nd

            if w_sum > 0 and w_target > 0:
                ll += math.log(w_target / w_sum)
                n_events += 1

            degree[target] += 1

    return ll, n_events


def _weight(nd, src, lessons, session_attrs, session_types,
            degree, gamma, lam, beta_domex, beta_reach, model):
    """Compute weight for a pool member."""
    k = degree[nd]

    # Session gap
    src_sess = lessons[src]["session"]
    nd_sess = lessons[nd]["session"]
    if src_sess is not None and nd_sess is not None:
        ds = abs(src_sess - nd_sess)
    else:
        ds = abs(src - nd) / 2.0

    # Base weight (PA + proximity)
    w = ((k + 1) ** gamma) * math.exp(-lam * ds)

    if model == "baseline":
        return w

    # Agent covariate: look up the SESSION that produced this lesson
    producing_session = lessons[nd]["session"]
    if producing_session is None:
        return w

    if model in ("domex", "full"):
        is_domex = 1.0 if session_types.get(producing_session) == "domex" else 0.0
        w *= math.exp(beta_domex * is_domex)

    if model in ("reach", "full"):
        attrs = session_attrs.get(producing_session, {})
        reach = attrs.get("citation_reach", 0)
        w *= math.exp(beta_reach * math.log1p(reach))

    return w


def bic(ll, k_params, n_events):
    if n_events <= 0:
        return float("inf")
    return -2 * ll + k_params * math.log(n_events)


def grid_search_agent(lessons, session_attrs, session_types, model,
                      gamma_base=0.72, lam_base=0.016):
    """Grid search for agent covariate parameters.

    Strategy: Fix γ, λ at baseline optimum for agent-covariate models
    (only search β parameters). This is valid because agent covariates
    are orthogonal to degree/proximity — they describe the PRODUCER,
    not the CITATION EVENT.
    """
    best_ll = -float("inf")
    best_params = {}

    # For baseline: search γ, λ normally
    if model == "baseline":
        gamma_range = [gamma_base + x * 0.04 for x in range(-3, 4)]
        lam_range = [lam_base + x * 0.002 for x in range(-3, 4)]
        for g in gamma_range:
            for l in lam_range:
                if l <= 0:
                    continue
                ll, n = compute_ll(lessons, session_attrs, session_types,
                                   g, l, model="baseline")
                if ll > best_ll:
                    best_ll = ll
                    best_params = {"gamma": round(g, 3), "lambda": round(l, 4),
                                   "ll": ll, "n_events": n}
        return best_params

    # For agent models: fix γ, λ at baseline optimum and search β only
    g_fixed = gamma_base
    l_fixed = lam_base

    if model == "domex":
        for bd in [x * 0.1 for x in range(-15, 25)]:
            ll, n = compute_ll(lessons, session_attrs, session_types,
                               g_fixed, l_fixed, beta_domex=bd, model="domex")
            if ll > best_ll:
                best_ll = ll
                best_params = {"gamma": g_fixed, "lambda": l_fixed,
                               "beta_domex": round(bd, 2), "ll": ll, "n_events": n}
        # Refine
        bd0 = best_params["beta_domex"]
        for bd in [bd0 + x * 0.02 for x in range(-5, 6)]:
            ll, n = compute_ll(lessons, session_attrs, session_types,
                               g_fixed, l_fixed, beta_domex=bd, model="domex")
            if ll > best_ll:
                best_ll = ll
                best_params = {"gamma": g_fixed, "lambda": l_fixed,
                               "beta_domex": round(bd, 3), "ll": ll, "n_events": n}
        return best_params

    if model == "reach":
        for br in [x * 0.05 for x in range(-15, 25)]:
            ll, n = compute_ll(lessons, session_attrs, session_types,
                               g_fixed, l_fixed, beta_reach=br, model="reach")
            if ll > best_ll:
                best_ll = ll
                best_params = {"gamma": g_fixed, "lambda": l_fixed,
                               "beta_reach": round(br, 3), "ll": ll, "n_events": n}
        # Refine
        br0 = best_params["beta_reach"]
        for br in [br0 + x * 0.01 for x in range(-5, 6)]:
            ll, n = compute_ll(lessons, session_attrs, session_types,
                               g_fixed, l_fixed, beta_reach=br, model="reach")
            if ll > best_ll:
                best_ll = ll
                best_params = {"gamma": g_fixed, "lambda": l_fixed,
                               "beta_reach": round(br, 3), "ll": ll, "n_events": n}
        return best_params

    if model == "full":
        # Search β_domex and β_reach jointly but with coarser grid
        for bd in [x * 0.2 for x in range(-8, 13)]:
            for br in [x * 0.1 for x in range(-8, 13)]:
                ll, n = compute_ll(lessons, session_attrs, session_types,
                                   g_fixed, l_fixed, beta_domex=bd, beta_reach=br, model="full")
                if ll > best_ll:
                    best_ll = ll
                    best_params = {
                        "gamma": g_fixed, "lambda": l_fixed,
                        "beta_domex": round(bd, 2), "beta_reach": round(br, 3),
                        "ll": ll, "n_events": n
                    }
        # Refine
        bd0 = best_params["beta_domex"]
        br0 = best_params["beta_reach"]
        for bd in [bd0 + x * 0.04 for x in range(-5, 6)]:
            for br in [br0 + x * 0.02 for x in range(-5, 6)]:
                ll, n = compute_ll(lessons, session_attrs, session_types,
                                   g_fixed, l_fixed, beta_domex=bd, beta_reach=br, model="full")
                if ll > best_ll:
                    best_ll = ll
                    best_params = {
                        "gamma": g_fixed, "lambda": l_fixed,
                        "beta_domex": round(bd, 3), "beta_reach": round(br, 3),
                        "ll": ll, "n_events": n
                    }
        return best_params

    return best_params


# ============================================================================
# Main
# ============================================================================

def main():
    print("F-SP4 Extension: Agent-Level Covariates in Citation Attachment")
    print("=" * 70)

    # Load data
    print("Loading lessons...")
    lessons = load_all_lessons()
    print(f"  {len(lessons)} lessons")

    print("Computing session attributes (F-META16 methodology)...")
    session_attrs = compute_session_attributes(lessons)
    print(f"  {len(session_attrs)} sessions profiled")

    print("Classifying session types from git...")
    session_types = classify_session_from_commits()
    domex_count = sum(1 for t in session_types.values() if t == "domex")
    print(f"  {len(session_types)} sessions classified ({domex_count} DOMEX)")

    # Fit models
    print("\nFitting baseline (joint PA+proximity)...")
    baseline = grid_search_agent(lessons, session_attrs, session_types, "baseline")
    print(f"  γ={baseline['gamma']}, λ={baseline['lambda']}, LL={baseline['ll']:.2f}")

    print("Fitting +domex...")
    domex_model = grid_search_agent(lessons, session_attrs, session_types, "domex")
    print(f"  γ={domex_model['gamma']}, λ={domex_model['lambda']}, "
          f"β_domex={domex_model.get('beta_domex', 0)}, LL={domex_model['ll']:.2f}")

    print("Fitting +reach...")
    reach_model = grid_search_agent(lessons, session_attrs, session_types, "reach")
    print(f"  γ={reach_model['gamma']}, λ={reach_model['lambda']}, "
          f"β_reach={reach_model.get('beta_reach', 0)}, LL={reach_model['ll']:.2f}")

    print("Fitting full agent model...")
    full_model = grid_search_agent(lessons, session_attrs, session_types, "full")
    print(f"  γ={full_model['gamma']}, λ={full_model['lambda']}, "
          f"β_domex={full_model.get('beta_domex', 0)}, β_reach={full_model.get('beta_reach', 0)}, "
          f"LL={full_model['ll']:.2f}")

    n = baseline["n_events"]

    # BIC comparison
    bic_baseline = bic(baseline["ll"], 2, n)
    bic_domex = bic(domex_model["ll"], 3, n)
    bic_reach = bic(reach_model["ll"], 3, n)
    bic_full = bic(full_model["ll"], 4, n)

    print(f"\n{'='*70}")
    print("MODEL COMPARISON (BIC, lower=better)")
    print(f"{'='*70}")
    models = [
        ("baseline (PA+prox)", 2, baseline, bic_baseline),
        ("+domex", 3, domex_model, bic_domex),
        ("+reach", 3, reach_model, bic_reach),
        ("full (domex+reach)", 4, full_model, bic_full),
    ]

    best_bic = min(b for _, _, _, b in models)
    for name, k, fit, b in models:
        marker = " <-- BEST" if b == best_bic else ""
        print(f"  {name:25s}: BIC={b:10.2f}  LL={fit['ll']:10.2f}  k={k}{marker}")

    # Deltas
    delta_domex = bic_baseline - bic_domex
    delta_reach = bic_baseline - bic_reach
    delta_full = bic_baseline - bic_full

    print(f"\n  ΔBIC(+domex vs baseline):     {delta_domex:+.2f}")
    print(f"  ΔBIC(+reach vs baseline):     {delta_reach:+.2f}")
    print(f"  ΔBIC(full vs baseline):       {delta_full:+.2f}")

    # Interpretation
    def interpret_delta(d, name):
        if d > 10:
            return f"{name}: STRONG improvement (ΔBIC={d:+.1f})"
        elif d > 2:
            return f"{name}: MODERATE improvement (ΔBIC={d:+.1f})"
        elif d > -2:
            return f"{name}: INCONCLUSIVE (ΔBIC={d:+.1f})"
        else:
            return f"{name}: WORSE (ΔBIC={d:+.1f}, extra parameter not justified)"

    interp_domex = interpret_delta(delta_domex, "+domex")
    interp_reach = interpret_delta(delta_reach, "+reach")
    interp_full = interpret_delta(delta_full, "full")

    print(f"\n  {interp_domex}")
    print(f"  {interp_reach}")
    print(f"  {interp_full}")

    # Effect sizes
    print(f"\n{'='*70}")
    print("EFFECT SIZES")
    print(f"{'='*70}")

    beta_d = domex_model.get("beta_domex", 0)
    beta_r = reach_model.get("beta_reach", 0)
    print(f"  β_domex = {beta_d:.3f} → DOMEX lessons have exp({beta_d:.3f}) = {math.exp(beta_d):.2f}x citation probability")
    print(f"  β_reach = {beta_r:.3f} → each e-fold in citation_reach multiplies probability by exp({beta_r:.3f}) = {math.exp(beta_r):.2f}x")

    # Session type distribution of most-cited lessons
    print(f"\n{'='*70}")
    print("DESCRIPTIVE: Citation counts by session type")
    print(f"{'='*70}")

    # Build in-degree map
    in_degree = defaultdict(int)
    for lid, ldata in lessons.items():
        for cited in ldata["cites"]:
            in_degree[cited] += 1

    type_degrees = defaultdict(list)
    for lid, ldata in lessons.items():
        s = ldata["session"]
        if s is None:
            continue
        t = session_types.get(s, "unknown")
        type_degrees[t].append(in_degree.get(lid, 0))

    for t in sorted(type_degrees.keys()):
        degs = type_degrees[t]
        avg = sum(degs) / len(degs) if degs else 0
        nonzero = sum(1 for d in degs if d > 0)
        print(f"  {t:12s}: n={len(degs):3d}  avg_citations={avg:.2f}  "
              f"cited_pct={nonzero/len(degs):.0%}  max={max(degs) if degs else 0}")

    # Expectation check
    print(f"\n{'='*70}")
    print("EXPECTATION CHECK")
    print(f"{'='*70}")

    expectations = {
        "domex_improves_bic_gt10": delta_domex > 10,
        "reach_positive_beta": beta_r > 0,
        "full_model_best": bic_full == best_bic,
    }

    for name, result in expectations.items():
        status = "CONFIRMED" if result else "FALSIFIED"
        print(f"  [{status}] {name}")

    # Build output
    result = {
        "experiment": "F-SP4 extension: Agent-level covariates in citation attachment",
        "session": "S394",
        "lane": "DOMEX-SP-S394",
        "date": "2026-03-01",
        "method": "Extend F-SP4 joint PA+proximity model with per-session attributes (is_domex, citation_reach). Grid search over γ, λ, β_domex, β_reach. Compare 4 models via BIC.",
        "data": {
            "n_lessons": len(lessons),
            "n_sessions_profiled": len(session_attrs),
            "n_sessions_typed": len(session_types),
            "n_domex_sessions": domex_count,
            "n_events": n,
        },
        "models": {
            "baseline": {"params": {k: v for k, v in baseline.items() if k not in ("ll", "n_events")},
                         "ll": round(baseline["ll"], 2), "bic": round(bic_baseline, 2), "k": 2},
            "domex": {"params": {k: v for k, v in domex_model.items() if k not in ("ll", "n_events")},
                      "ll": round(domex_model["ll"], 2), "bic": round(bic_domex, 2), "k": 3},
            "reach": {"params": {k: v for k, v in reach_model.items() if k not in ("ll", "n_events")},
                      "ll": round(reach_model["ll"], 2), "bic": round(bic_reach, 2), "k": 3},
            "full": {"params": {k: v for k, v in full_model.items() if k not in ("ll", "n_events")},
                     "ll": round(full_model["ll"], 2), "bic": round(bic_full, 2), "k": 4},
        },
        "bic_deltas": {
            "domex_vs_baseline": round(delta_domex, 2),
            "reach_vs_baseline": round(delta_reach, 2),
            "full_vs_baseline": round(delta_full, 2),
        },
        "effect_sizes": {
            "beta_domex": round(beta_d, 3),
            "domex_multiplier": round(math.exp(beta_d), 3),
            "beta_reach": round(beta_r, 3),
            "reach_multiplier": round(math.exp(beta_r), 3),
        },
        "interpretation": {
            "domex": interp_domex,
            "reach": interp_reach,
            "full": interp_full,
        },
        "expectations": expectations,
        "descriptive": {t: {"n": len(degs), "avg_citations": round(sum(degs)/len(degs), 2) if degs else 0,
                           "cited_pct": round(sum(1 for d in degs if d > 0)/len(degs), 3) if degs else 0}
                       for t, degs in type_degrees.items()},
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n  Output: {OUTPUT_FILE}")

    return result


if __name__ == "__main__":
    main()
