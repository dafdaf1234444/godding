#!/usr/bin/env python3
"""Market prediction registry — pre-register, track, and score investment predictions.

Usage:
    python3 tools/market_predict.py register --asset SPY --direction BEAR --target "-3%" \
        --timeframe 1m --confidence 0.65 --thesis "..." --domains "physics,control-theory"
    python3 tools/market_predict.py resolve --id PRED-0001 --outcome-price 5600 --result CORRECT
    python3 tools/market_predict.py score
    python3 tools/market_predict.py update --id PRED-0004 --confidence 0.50 --note "S513: downgrade"
    python3 tools/market_predict.py list [--open | --resolved]
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

PRED_DIR = Path("experiments/finance/predictions")
REGISTRY = PRED_DIR / "registry.json"

TIMEFRAME_DAYS = {"1w": 7, "2w": 14, "1m": 30, "3m": 90, "6m": 180, "1y": 365}


def load_registry():
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text())
    return {"predictions": [], "next_id": 1, "metadata": {"created": datetime.now().isoformat()}}


def save_registry(reg):
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    reg["metadata"]["updated"] = datetime.now().isoformat()
    REGISTRY.write_text(json.dumps(reg, indent=2) + "\n")


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
    pred["result"] = args.result
    pred["status"] = "RESOLVED"

    # Compute % change from baseline
    baseline = pred.get("baseline_price")
    if baseline and baseline > 0:
        pct_change = ((pred["outcome_price"] - baseline) / baseline) * 100
        pred["pct_change"] = round(pct_change, 2)
        print(f"  Baseline: ${baseline} → Outcome: ${pred['outcome_price']} ({pct_change:+.2f}%)")

    # Compute Brier score component
    if args.result == "CORRECT":
        pred["score"] = round((1 - pred["confidence"]) ** 2, 4)
    elif args.result == "INCORRECT":
        pred["score"] = round(pred["confidence"] ** 2, 4)
    else:  # PARTIAL
        pred["score"] = round((0.5 - pred["confidence"]) ** 2 + 0.125, 4)

    save_registry(reg)
    print(f"Resolved {args.id}: {args.result} (Brier component: {pred['score']})")


def score(_args):
    reg = load_registry()
    resolved = [p for p in reg["predictions"] if p["status"] == "RESOLVED"]
    open_preds = [p for p in reg["predictions"] if p["status"] == "OPEN"]

    if not resolved:
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
    reg_p.add_argument("--session", default=None)

    res_p = sub.add_parser("resolve", help="Resolve a prediction with outcome")
    res_p.add_argument("--id", required=True)
    res_p.add_argument("--outcome-price", required=True)
    res_p.add_argument("--result", required=True, choices=["CORRECT", "INCORRECT", "PARTIAL"])

    sub.add_parser("score", help="Show scorecard")

    upd_p = sub.add_parser("update", help="Update confidence/notes for a prediction")
    upd_p.add_argument("--id", required=True)
    upd_p.add_argument("--confidence", type=float, help="New confidence (0.0-1.0)")
    upd_p.add_argument("--note", help="Note to append")
    upd_p.add_argument("--session", default=None)

    list_p = sub.add_parser("list", help="List predictions")
    list_p.add_argument("--open", action="store_true")
    list_p.add_argument("--resolved", action="store_true")

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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
