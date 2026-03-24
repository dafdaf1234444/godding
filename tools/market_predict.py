#!/usr/bin/env python3
"""Market prediction registry — pre-register, track, and score investment predictions.

Usage:
    python3 tools/market_predict.py register --asset SPY --direction BEAR --target "-3%" \
        --timeframe 1m --confidence 0.65 --thesis "..." --domains "physics,control-theory"
    python3 tools/market_predict.py resolve --id PRED-0001 --outcome-price 5600
    python3 tools/market_predict.py resolve --id PRED-0001 --outcome-price 5600 --result CORRECT
    python3 tools/market_predict.py score
    python3 tools/market_predict.py update --id PRED-0004 --confidence 0.50 --note "S513: downgrade"
    python3 tools/market_predict.py list [--open | --resolved]
    python3 tools/market_predict.py due
    python3 tools/market_predict.py portfolio
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

PRED_DIR = Path("experiments/finance/predictions")
REGISTRY = PRED_DIR / "registry.json"
FORECAST_DIR = Path("experiments/forecasting")

TIMEFRAME_DAYS = {"1w": 7, "2w": 14, "1m": 30, "3m": 90, "6m": 180, "1y": 365}

INTERIM_DEFINITE_CORRECT = {
    "WITH",
    "WITHIN",
    "ON_TRACK",
    "ON_TARGET",
    "STRONGLY_ON_TARGET",
}
INTERIM_DIRECTIONAL_CORRECT = INTERIM_DEFINITE_CORRECT | {
    "EARLY",
    "WEAK_TRENDING",
    "LIKELY_ON_TARGET",
    "WEAKENING",
}
INTERIM_PARTIAL = {"EARLY", "WEAK_TRENDING", "LIKELY_ON_TARGET", "WEAKENING", "FLAT"}
INTERIM_INCORRECT = {"AGAINST", "STRONGLY_AGAINST"}


def load_registry():
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text())
    return {"predictions": [], "next_id": 1, "metadata": {"created": datetime.now().isoformat()}}


def save_registry(reg):
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    reg["metadata"]["updated"] = datetime.now().isoformat()
    REGISTRY.write_text(json.dumps(reg, indent=2) + "\n")


def _artifact_session(path):
    stem = path.stem
    parts = stem.rsplit("-s", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    return -1


def _prediction_id_from_artifact_key(key):
    if key.startswith("PRED-"):
        return key.split("_", 1)[0]
    return key


def _load_latest_interim_artifact():
    if not FORECAST_DIR.exists():
        return None

    latest = None
    latest_sort = (-1, 0.0)
    for path in FORECAST_DIR.glob("f-fore1*scoring*.json"):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        actual = data.get("actual", {})
        predictions = actual.get("predictions_scored") if isinstance(actual, dict) else None
        if not isinstance(predictions, dict) or not predictions:
            continue
        sort_key = (_artifact_session(path), path.stat().st_mtime)
        if sort_key > latest_sort:
            latest = (path, data)
            latest_sort = sort_key
    return latest


def _interim_score_class(status):
    status = (status or "").upper()
    if status in INTERIM_DEFINITE_CORRECT:
        return "CORRECT"
    if status in INTERIM_PARTIAL:
        return "PARTIAL"
    if status in INTERIM_INCORRECT:
        return "INCORRECT"
    return None


def _interim_directional_hit(status):
    return (status or "").upper() in INTERIM_DIRECTIONAL_CORRECT


def _compute_interim_scorecard(reg, artifact_data):
    actual = artifact_data.get("actual", {})
    predictions = actual.get("predictions_scored") if isinstance(actual, dict) else {}
    registry_by_id = {p["id"]: p for p in reg["predictions"]}

    rows = []
    for key, snapshot in predictions.items():
        if not isinstance(snapshot, dict):
            continue
        pred_id = _prediction_id_from_artifact_key(key)
        pred = registry_by_id.get(pred_id)
        if not pred or pred.get("status") != "OPEN":
            continue
        status = str(snapshot.get("status", "")).upper()
        score_class = _interim_score_class(status)
        if score_class is None:
            continue
        conf = snapshot.get("conf", pred.get("confidence"))
        if conf is None:
            continue
        conf = float(conf)
        if score_class == "CORRECT":
            actual_value = 1.0
            pseudo_score = (1 - conf) ** 2
        elif score_class == "INCORRECT":
            actual_value = 0.0
            pseudo_score = conf ** 2
        else:
            actual_value = 0.5
            pseudo_score = (0.5 - conf) ** 2 + 0.125
        rows.append({
            "id": pred_id,
            "status": status,
            "confidence": conf,
            "actual_value": actual_value,
            "pseudo_score": round(pseudo_score, 4),
            "directional_hit": _interim_directional_hit(status),
        })

    if not rows:
        return None

    n = len(rows)
    directional_hits = sum(1 for row in rows if row["directional_hit"])
    brier = sum(row["pseudo_score"] for row in rows) / n
    buckets = {}
    for row in rows:
        bucket = round(row["confidence"] * 10) / 10
        entry = buckets.setdefault(bucket, {"total": 0, "actual_sum": 0.0})
        entry["total"] += 1
        entry["actual_sum"] += row["actual_value"]
    ece = 0.0
    for conf, data in buckets.items():
        actual_mean = data["actual_sum"] / data["total"]
        ece += abs(actual_mean - conf) * (data["total"] / n)

    return {
        "n": n,
        "directional_hits": directional_hits,
        "direction_acc": directional_hits / n,
        "brier": brier,
        "ece": ece,
        "status_counts": dict(sorted(
            ((status, sum(1 for row in rows if row["status"] == status))
             for status in {row["status"] for row in rows}),
            key=lambda item: (-item[1], item[0]),
        )),
    }


def _print_interim_scorecard(reg, path, artifact_data, summary):
    open_preds = [p for p in reg["predictions"] if p["status"] == "OPEN"]
    print("No resolved predictions yet.")
    print(f"  Open predictions: {len(open_preds)}")
    print()
    print("=== SWARM INVESTOR SCORECARD (INTERIM) ===")
    print(f"  Interim fallback: {path}")
    session = artifact_data.get("session", "unknown")
    data_date = artifact_data.get("data_date", artifact_data.get("date", "unknown"))
    print(f"  Artifact session: {session} | data date: {data_date}")
    print(f"  Scored open predictions: {summary['n']}/{len(open_preds)}")
    print(f"  Direction accuracy: {summary['direction_acc']:.1%} "
          f"({summary['directional_hits']}/{summary['n']})")
    print(f"  Interim Brier-like score: {summary['brier']:.4f} (confidence-weighted, lower=better)")
    print(f"  Interim ECE: {summary['ece']:.4f} (lower=better)")
    print()
    print("  Status mix:")
    for status, count in summary["status_counts"].items():
        print(f"    {status}: {count}")


def register(args):
    reg = load_registry()
    pred_id = f"PRED-{reg['next_id']:04d}"
    tf = args.timeframe
    if tf not in TIMEFRAME_DAYS:
        print(f"ERROR: timeframe must be one of {list(TIMEFRAME_DAYS.keys())}")
        sys.exit(1)
    if args.direction not in ("BULL", "BEAR", "NEUTRAL"):
        print("ERROR: direction must be BULL, BEAR, or NEUTRAL")
        sys.exit(1)
    conf = float(args.confidence)
    if not 0.0 <= conf <= 1.0:
        print("ERROR: confidence must be 0.0-1.0")
        sys.exit(1)
    if conf < 0.20:
        print("ERROR: confidence must be >= 0.20. Below 0.20, failure is already expected — the prediction is evidence-immunized (L-1498). Express low-confidence views as observations, not predictions.")
        sys.exit(1)

    # P-FORE1 (L-1461): geopolitical predictions need explicit exit triggers
    geopolitical_keywords = ["war", "conflict", "iran", "china", "tariff", "sanction", "geopolit",
                             "escalat", "de-escalat", "military", "hormuz", "invasion"]
    thesis_lower = (args.thesis or "").lower()
    is_geopolitical = any(kw in thesis_lower for kw in geopolitical_keywords)
    if is_geopolitical and not args.exit_trigger:
        print("WARN (P-FORE1): thesis appears geopolitical but no --exit-trigger provided. "
              "Geopolitical predictions are 0/6 correct without exit triggers (L-1461). "
              "Add --exit-trigger 'event that invalidates thesis'.")

    # P-FORE2 (L-1548): neutral predictions are portfolio's strongest type but underconfident
    if args.direction == "NEUTRAL" and conf < 0.55:
        print(f"WARN (P-FORE2): neutral predictions are underconfident at conf={conf}. "
              "Calibration data shows neutrals are strongest type — consider conf >= 0.55 (L-1548).")

    # P-FORE3 (L-1461): narrative-based bear predictions on broad indices are overconfident
    broad_indices = {"SPY", "QQQ", "IWM", "DIA", "VTI"}
    if args.direction == "BEAR" and args.asset.upper() in broad_indices and conf > 0.30:
        print(f"WARN (P-FORE3): bear prediction on broad index {args.asset.upper()} with conf={conf} > 0.30. "
              "Geopolitical/narrative bear theses are 0/6 correct (L-1461). Consider lowering confidence.")

    resolve_date = (datetime.now() + timedelta(days=TIMEFRAME_DAYS[tf])).strftime("%Y-%m-%d")

    pred = {
        "id": pred_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "session": args.session or "unknown",
        "asset": args.asset.upper(),
        "direction": args.direction,
        "target": args.target,
        "timeframe": tf,
        "confidence": conf,
        "thesis": args.thesis,
        "domains_applied": [d.strip() for d in args.domains.split(",")],
        "key_risk": args.key_risk or "",
        "exit_trigger": args.exit_trigger or "",
        "resolve_by": resolve_date,
        "status": "OPEN",
        "outcome_date": None,
        "outcome_price": None,
        "result": None,
        "score": None,
    }
    reg["predictions"].append(pred)
    reg["next_id"] += 1
    save_registry(reg)
    print(f"Registered {pred_id}: {args.direction} {args.asset} ({tf}, conf={conf})")
    print(f"  Target: {args.target}")
    print(f"  Resolve by: {resolve_date}")
    print(f"  Domains: {pred['domains_applied']}")
    return pred_id


def _parse_target_range(target_str):
    """Extract min/max % from target like '-5% to -10%' or '+3% to +8%'."""
    import re
    pcts = re.findall(r'[+-]?\d+(?:\.\d+)?%', target_str)
    if len(pcts) >= 2:
        vals = sorted(float(p.replace('%', '')) for p in pcts)
        return vals[0], vals[-1]
    if len(pcts) == 1:
        v = float(pcts[0].replace('%', ''))
        return (v, v)
    return None, None


def _auto_determine_result(pred, outcome_price):
    """Determine CORRECT/INCORRECT/PARTIAL from direction + price change."""
    baseline = pred.get("baseline_price")
    if not baseline or baseline <= 0:
        return None
    pct = ((outcome_price - baseline) / baseline) * 100
    direction = pred["direction"]
    target_min, target_max = _parse_target_range(pred.get("target", ""))

    # Direction check
    if direction == "BULL":
        direction_correct = pct > 0
    elif direction == "BEAR":
        direction_correct = pct < 0
    else:  # NEUTRAL
        # Correct if within target range or small move
        if target_min is not None and target_max is not None:
            direction_correct = target_min <= pct <= target_max
        else:
            direction_correct = abs(pct) < 5  # default: <5% move = neutral correct

    # Target range check (if available)
    if target_min is not None and target_max is not None:
        in_range = target_min <= pct <= target_max
        if in_range:
            return "CORRECT"
        elif direction_correct:
            return "PARTIAL"  # right direction, wrong magnitude
        else:
            return "INCORRECT"

    return "CORRECT" if direction_correct else "INCORRECT"


def resolve(args):
    reg = load_registry()
    pred = next((p for p in reg["predictions"] if p["id"] == args.id), None)
    if not pred:
        print(f"ERROR: {args.id} not found")
        sys.exit(1)
    if pred["status"] != "OPEN":
        print(f"WARNING: {args.id} already resolved as {pred['result']}")

    pred["outcome_date"] = datetime.now().strftime("%Y-%m-%d")
    pred["outcome_price"] = float(args.outcome_price)
    pred["status"] = "RESOLVED"

    # Auto-determine result if not manually specified
    if args.result:
        pred["result"] = args.result
        pred["result_source"] = "manual"
    else:
        auto_result = _auto_determine_result(pred, pred["outcome_price"])
        if auto_result:
            pred["result"] = auto_result
            pred["result_source"] = "auto"
            print(f"  Auto-determined: {auto_result}")
        else:
            print("ERROR: Cannot auto-determine result (missing baseline). Use --result.")
            sys.exit(1)

    # Compute % change from baseline
    baseline = pred.get("baseline_price")
    if baseline and baseline > 0:
        pct_change = ((pred["outcome_price"] - baseline) / baseline) * 100
        pred["pct_change"] = round(pct_change, 2)
        print(f"  Baseline: ${baseline} → Outcome: ${pred['outcome_price']} ({pct_change:+.2f}%)")

    # Compute Brier score component
    if pred["result"] == "CORRECT":
        pred["score"] = round((1 - pred["confidence"]) ** 2, 4)
    elif pred["result"] == "INCORRECT":
        pred["score"] = round(pred["confidence"] ** 2, 4)
    else:  # PARTIAL
        pred["score"] = round((0.5 - pred["confidence"]) ** 2 + 0.125, 4)

    save_registry(reg)
    print(f"Resolved {args.id}: {pred['result']} (Brier component: {pred['score']})")


def score(_args):
    reg = load_registry()
    resolved = [p for p in reg["predictions"] if p["status"] == "RESOLVED"]
    open_preds = [p for p in reg["predictions"] if p["status"] == "OPEN"]

    if not resolved:
        interim = _load_latest_interim_artifact()
        if interim:
            path, artifact_data = interim
            summary = _compute_interim_scorecard(reg, artifact_data)
            if summary:
                _print_interim_scorecard(reg, path, artifact_data, summary)
                return
        print("No resolved predictions yet.")
        print(f"  Open predictions: {len(open_preds)}")
        return

    n = len(resolved)
    correct = sum(1 for p in resolved if p["result"] == "CORRECT")
    incorrect = sum(1 for p in resolved if p["result"] == "INCORRECT")
    partial = sum(1 for p in resolved if p["result"] == "PARTIAL")

    direction_acc = correct / n if n > 0 else 0
    brier = sum(p["score"] for p in resolved) / n if n > 0 else 0

    # Calibration buckets
    buckets = {}
    for p in resolved:
        bucket = round(p["confidence"] * 10) / 10  # Round to nearest 0.1
        if bucket not in buckets:
            buckets[bucket] = {"total": 0, "correct": 0}
        buckets[bucket]["total"] += 1
        if p["result"] == "CORRECT":
            buckets[bucket]["correct"] += 1

    ece = 0
    for conf, data in sorted(buckets.items()):
        acc = data["correct"] / data["total"]
        ece += abs(acc - conf) * (data["total"] / n)

    print(f"=== SWARM INVESTOR SCORECARD ===")
    print(f"  Total predictions: {len(reg['predictions'])} ({len(open_preds)} open, {n} resolved)")
    print(f"  Correct: {correct} | Incorrect: {incorrect} | Partial: {partial}")
    print(f"  Direction accuracy: {direction_acc:.1%} (benchmark: 50%)")
    print(f"  Brier score: {brier:.4f} (benchmark: 0.25, lower=better)")
    print(f"  ECE: {ece:.4f} (lower=better)")
    print()
    if direction_acc > 0.60:
        print("  VERDICT: Strong evidence of skill")
    elif direction_acc > 0.55:
        print("  VERDICT: Weak evidence of skill")
    elif n >= 20:
        print("  VERDICT: No evidence of skill (yet)")
    else:
        print(f"  VERDICT: Too few predictions ({n}/50 minimum for statistical significance)")

    print()
    print("  Calibration:")
    for conf, data in sorted(buckets.items()):
        acc = data["correct"] / data["total"]
        print(f"    {conf:.0%} confidence → {acc:.0%} actual ({data['total']} predictions)")

    # Domain breakdown
    domain_stats = {}
    for p in resolved:
        for d in p.get("domains_applied", []):
            if d not in domain_stats:
                domain_stats[d] = {"total": 0, "correct": 0}
            domain_stats[d]["total"] += 1
            if p["result"] == "CORRECT":
                domain_stats[d]["correct"] += 1

    if domain_stats:
        print()
        print("  Domain hit rates:")
        for d, s in sorted(domain_stats.items(), key=lambda x: -x[1]["total"]):
            acc = s["correct"] / s["total"] if s["total"] > 0 else 0
            print(f"    {d}: {acc:.0%} ({s['total']} predictions)")


def update(args):
    """Update confidence and/or add note to an existing prediction."""
    reg = load_registry()
    pred = next((p for p in reg["predictions"] if p["id"] == args.id), None)
    if not pred:
        print(f"ERROR: {args.id} not found")
        sys.exit(1)
    if pred["status"] != "OPEN":
        print(f"WARNING: {args.id} already {pred['status']}")

    changes = []
    if args.confidence is not None:
        old_conf = pred["confidence"]
        pred["confidence"] = args.confidence
        # Track confidence history
        if "confidence_history" not in pred:
            pred["confidence_history"] = [{"value": old_conf, "session": "original"}]
        pred["confidence_history"].append({
            "value": args.confidence,
            "session": args.session or "unknown",
            "date": datetime.now().strftime("%Y-%m-%d"),
        })
        changes.append(f"confidence {old_conf:.2f}→{args.confidence:.2f}")

    if args.note:
        pred.setdefault("notes", []).append(args.note)
        changes.append("note added")

    if not changes:
        print("Nothing to update. Use --confidence and/or --note.")
        return

    save_registry(reg)
    print(f"Updated {args.id}: {', '.join(changes)}")


def due(_args):
    """Show predictions approaching or past their resolution date."""
    reg = load_registry()
    today = datetime.now().date()
    open_preds = [p for p in reg["predictions"] if p["status"] == "OPEN"]

    if not open_preds:
        print("No open predictions.")
        return

    # Sort by resolve_by date
    dated = []
    for p in open_preds:
        rb = p.get("resolve_by")
        if rb:
            resolve_date = datetime.strptime(rb, "%Y-%m-%d").date()
            days_left = (resolve_date - today).days
            dated.append((days_left, resolve_date, p))
    dated.sort(key=lambda x: x[0])

    overdue = [d for d in dated if d[0] < 0]
    due_soon = [d for d in dated if 0 <= d[0] <= 7]
    upcoming = [d for d in dated if 7 < d[0] <= 30]
    later = [d for d in dated if d[0] > 30]

    if overdue:
        print("=== OVERDUE ===")
        for days, dt, p in overdue:
            print(f"  ⚠ {p['id']} {p['direction']} {p['asset']} (conf={p['confidence']}) "
                  f"— {abs(days)}d overdue (was {dt})")
        print()

    if due_soon:
        print("=== DUE THIS WEEK ===")
        for days, dt, p in due_soon:
            label = "TODAY" if days == 0 else f"in {days}d"
            print(f"  → {p['id']} {p['direction']} {p['asset']} (conf={p['confidence']}) "
                  f"— {label} ({dt})")
        print()

    if upcoming:
        print(f"=== UPCOMING (next 30d): {len(upcoming)} predictions ===")
        for days, dt, p in upcoming:
            print(f"    {p['id']} {p['direction']} {p['asset']} — in {days}d ({dt})")
        print()

    if later:
        print(f"=== LATER (>30d): {len(later)} predictions ===")
        for days, dt, p in later:
            print(f"    {p['id']} {p['direction']} {p['asset']} — in {days}d ({dt})")

    print(f"\nTotal: {len(open_preds)} open | {len(overdue)} overdue | "
          f"{len(due_soon)} due this week | {len(upcoming)} upcoming")


def portfolio(_args):
    """Portfolio-level meta-analysis of all predictions."""
    reg = load_registry()
    preds = reg["predictions"]
    open_p = [p for p in preds if p["status"] == "OPEN"]
    resolved = [p for p in preds if p["status"] == "RESOLVED"]

    print(f"=== PREDICTION PORTFOLIO (n={len(preds)}) ===")
    print(f"  Open: {len(open_p)} | Resolved: {len(resolved)}")
    print()

    # Confidence distribution
    confs = [p["confidence"] for p in preds]
    avg_conf = sum(confs) / len(confs) if confs else 0
    print(f"  Avg confidence: {avg_conf:.2f}")

    # Direction breakdown
    dirs = {}
    for p in preds:
        d = p["direction"]
        dirs[d] = dirs.get(d, 0) + 1
    print(f"  Direction mix: {', '.join(f'{k}={v}' for k, v in sorted(dirs.items()))}")

    # Domain coverage
    domain_counts = {}
    for p in preds:
        for d in p.get("domains_applied", []):
            domain_counts[d] = domain_counts.get(d, 0) + 1
    top_domains = sorted(domain_counts.items(), key=lambda x: -x[1])[:5]
    print(f"  Top domains: {', '.join(f'{d}({n})' for d, n in top_domains)}")

    # Asset concentration
    asset_counts = {}
    for p in preds:
        a = p.get("asset", "?")
        asset_counts[a] = asset_counts.get(a, 0) + 1
    unique_assets = len(asset_counts)
    max_asset = max(asset_counts.items(), key=lambda x: x[1]) if asset_counts else ("?", 0)
    print(f"  Assets: {unique_assets} unique | most concentrated: {max_asset[0]} ({max_asset[1]})")

    # Confidence adjustments (how much did we update?)
    adjusted = [p for p in preds if p.get("confidence_history") and len(p["confidence_history"]) > 1]
    if adjusted:
        deltas = []
        for p in adjusted:
            orig = p["confidence_history"][0]["value"]
            curr = p["confidence"]
            deltas.append(curr - orig)
        avg_delta = sum(deltas) / len(deltas)
        print(f"  Adjustments: {len(adjusted)}/{len(preds)} predictions updated "
              f"(avg Δ={avg_delta:+.2f})")

    # Resolved stats
    if resolved:
        print()
        n = len(resolved)
        correct = sum(1 for p in resolved if p["result"] == "CORRECT")
        brier = sum(p.get("score", 0) for p in resolved) / n
        print(f"  --- Resolved Performance ---")
        print(f"  Direction accuracy: {correct}/{n} ({correct/n:.0%})")
        print(f"  Mean Brier score: {brier:.4f} (benchmark: 0.25)")
        verdict = "SKILL" if brier < 0.20 else "CALIBRATED" if brier < 0.25 else "OVERCONFIDENT"
        print(f"  Verdict: {verdict} (n={n}, need ≥20 for statistical power)")

    # Risk: correlated predictions
    print()
    corr_groups = {}
    for p in preds:
        a = p.get("asset", "?")
        if a in ("SPY", "QQQ", "IWM"):
            corr_groups.setdefault("US_EQUITY", []).append(p["id"])
        elif a in ("GLD",):
            corr_groups.setdefault("GOLD", []).append(p["id"])
        elif a in ("TLT",):
            corr_groups.setdefault("BONDS", []).append(p["id"])
    multi = {k: v for k, v in corr_groups.items() if len(v) > 1}
    if multi:
        print(f"  Correlation risk: {len(multi)} correlated groups")
        for group, ids in multi.items():
            print(f"    {group}: {', '.join(ids)}")


def list_preds(args):
    reg = load_registry()
    preds = reg["predictions"]
    if args.open:
        preds = [p for p in preds if p["status"] == "OPEN"]
    elif args.resolved:
        preds = [p for p in preds if p["status"] == "RESOLVED"]

    if not preds:
        print("No predictions found.")
        return

    for p in preds:
        status = p["status"]
        result_str = f" → {p['result']}" if p["result"] else ""
        baseline = p.get("baseline_price")
        base_str = f" base=${baseline}" if baseline else ""
        print(f"  {p['id']} [{status}{result_str}] {p['direction']} {p['asset']}"
              f"{base_str} ({p['timeframe']}, conf={p['confidence']}) target={p['target']} "
              f"by {p.get('resolve_by', '?')}")
        if p.get("thesis"):
            # Show first 100 chars of thesis
            thesis = p["thesis"][:100] + ("..." if len(p["thesis"]) > 100 else "")
            print(f"         {thesis}")
        if p.get("confidence_history"):
            orig = p["confidence_history"][0]["value"]
            curr = p["confidence"]
            if orig != curr:
                print(f"         [confidence adjusted: {orig:.0%} → {curr:.0%} after backtest]")


def main():
    parser = argparse.ArgumentParser(description="Swarm market prediction registry")
    sub = parser.add_subparsers(dest="command")

    reg_p = sub.add_parser("register", help="Register a new prediction")
    reg_p.add_argument("--asset", required=True)
    reg_p.add_argument("--direction", required=True, choices=["BULL", "BEAR", "NEUTRAL"])
    reg_p.add_argument("--target", required=True, help="Price target or % change")
    reg_p.add_argument("--timeframe", required=True, choices=list(TIMEFRAME_DAYS.keys()))
    reg_p.add_argument("--confidence", required=True, type=float)
    reg_p.add_argument("--thesis", required=True)
    reg_p.add_argument("--domains", required=True, help="Comma-separated domain list")
    reg_p.add_argument("--key-risk", default="")
    reg_p.add_argument("--exit-trigger", default="",
                        help="P-FORE1: event that invalidates thesis (required for geopolitical predictions)")
    reg_p.add_argument("--session", default=None)

    res_p = sub.add_parser("resolve", help="Resolve a prediction with outcome")
    res_p.add_argument("--id", required=True)
    res_p.add_argument("--outcome-price", required=True)
    res_p.add_argument("--result", required=False, choices=["CORRECT", "INCORRECT", "PARTIAL"],
                        help="Override auto-determination (default: auto from direction+price)")

    sub.add_parser("score", help="Show scorecard")

    upd_p = sub.add_parser("update", help="Update confidence/notes for a prediction")
    upd_p.add_argument("--id", required=True)
    upd_p.add_argument("--confidence", type=float, help="New confidence (0.0-1.0)")
    upd_p.add_argument("--note", help="Note to append")
    upd_p.add_argument("--session", default=None)

    list_p = sub.add_parser("list", help="List predictions")
    list_p.add_argument("--open", action="store_true")
    list_p.add_argument("--resolved", action="store_true")

    sub.add_parser("due", help="Show predictions approaching resolution date")
    sub.add_parser("portfolio", help="Portfolio-level meta-analysis")

    args = parser.parse_args()
    if args.command == "register":
        register(args)
    elif args.command == "resolve":
        resolve(args)
    elif args.command == "score":
        score(args)
    elif args.command == "update":
        update(args)
    elif args.command == "list":
        list_preds(args)
    elif args.command == "due":
        due(args)
    elif args.command == "portfolio":
        portfolio(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
