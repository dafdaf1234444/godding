#!/usr/bin/env python3
"""Market prediction status dashboard — shows days remaining, urgency, portfolio concentration.

Usage:
    python3 tools/market_check.py           # Full status dashboard
    python3 tools/market_check.py --urgent  # Only overdue/due-soon predictions

Structural enforcement for F-COMP1 (L-1312): without periodic checking,
prediction resolution decays to zero per L-601. Wire into orient.py or periodics.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

REGISTRY = Path("experiments/finance/predictions/registry.json")


def main():
    if not REGISTRY.exists():
        print("No prediction registry found.")
        sys.exit(0)

    reg = json.loads(REGISTRY.read_text())
    open_preds = [p for p in reg["predictions"] if p["status"] == "OPEN"]
    if not open_preds:
        print("No open predictions.")
        return

    urgent_only = "--urgent" in sys.argv
    today = datetime.now()
    print(f"=== PREDICTION STATUS CHECK ===")
    print(f"  Date: {today.strftime('%Y-%m-%d')} | Open: {len(open_preds)}\n")

    open_preds.sort(key=lambda p: p.get("resolve_by", "9999"))

    overdue, due_soon = [], []

    for p in open_preds:
        resolve_by = p.get("resolve_by", "")
        baseline = p.get("baseline_price")
        days_left = None
        urgency = ""

        if resolve_by:
            try:
                resolve_date = datetime.strptime(resolve_by, "%Y-%m-%d")
                days_left = (resolve_date - today).days
                if days_left < 0:
                    urgency = "OVERDUE"
                    overdue.append(p["id"])
                elif days_left <= 7:
                    urgency = "DUE SOON"
                    due_soon.append(p["id"])
                elif days_left <= 14:
                    urgency = "APPROACHING"
                else:
                    urgency = f"{days_left}d remaining"
            except ValueError:
                urgency = "?"

        if urgent_only and urgency not in ("OVERDUE", "DUE SOON", "APPROACHING"):
            continue

        base_str = f"${baseline:.2f}" if baseline else "?"
        print(f"  {p['id']} {p['direction']} {p['asset']} | base={base_str} | "
              f"conf={p['confidence']:.0%} | {urgency}")
        print(f"    Target: {p['target']}")
        print(f"    Resolve by: {resolve_by}")
        if p.get("key_risk"):
            print(f"    Key risk: {p['key_risk']}")
        print()

    print("--- Action Required ---")
    if overdue:
        print(f"  OVERDUE ({len(overdue)}): {', '.join(overdue)}")
        print("    -> python3 tools/market_predict.py resolve --id <ID> "
              "--outcome-price <PRICE> --result CORRECT|INCORRECT|PARTIAL")
    if due_soon:
        print(f"  DUE SOON ({len(due_soon)}): {', '.join(due_soon)}")
    if not overdue and not due_soon:
        next_resolve = open_preds[0].get("resolve_by", "?")
        print(f"  No urgent actions. Next resolve: {next_resolve}")

    # Portfolio concentration (L-1289 Sanhedrin pattern)
    directions = {}
    for p in open_preds:
        d = p["direction"]
        directions[d] = directions.get(d, 0) + 1
    print(f"\n  Portfolio: {directions}")
    if len(open_preds) >= 3 and max(directions.values()) / len(open_preds) > 0.6:
        dominant = max(directions, key=directions.get)
        print(f"  WARNING: {dominant}-concentrated ({directions[dominant]}/{len(open_preds)}). "
              "Consider contrarian position (L-1289).")


if __name__ == "__main__":
    main()
