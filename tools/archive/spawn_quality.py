#!/usr/bin/env python3
"""
spawn_quality.py - Analyze spawn event log to track what makes a good spawn.

Usage:
  python3 tools/spawn_quality.py show          # Summary stats
  python3 tools/spawn_quality.py marginal       # Marginal novelty of Nth agent
  python3 tools/spawn_quality.py size          # F92: aggregate outcomes by colony size
  python3 tools/spawn_quality.py log SE-006 ... # Add a spawn event (interactive)
  python3 tools/spawn_quality.py latest         # Most recent spawn event

Answers F71: What makes a good spawn task? Measure convergence speed and novelty.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

LOG_PATH = Path(__file__).parent.parent / "experiments" / "spawn-quality" / "spawn-log.json"


def load_log():
    with open(LOG_PATH) as f:
        data = json.load(f)
    return data["spawn_events"]


def marginal_novelty(events):
    """Compute average unique findings contributed by Nth agent across all spawn events."""
    by_position = defaultdict(list)  # position -> list of unique findings at that position

    for ev in events:
        per_agent = ev.get("findings_per_agent", [])
        overlap = ev.get("overlap_count", 0)
        n = len(per_agent)
        if n == 0:
            continue

        total = sum(per_agent)
        # Approximate unique findings per agent: subtract distributed overlap
        overlap_per_agent = overlap / n if n > 0 else 0

        for i, raw in enumerate(per_agent):
            unique = max(0, raw - overlap_per_agent)
            by_position[i + 1].append(unique)

    print("=== MARGINAL NOVELTY BY AGENT POSITION ===")
    print(f"{'Pos':>4}  {'Events':>6}  {'Avg Unique':>10}  {'Min':>6}  {'Max':>6}")
    print("-" * 42)
    for pos in sorted(by_position):
        vals = by_position[pos]
        avg = sum(vals) / len(vals)
        print(f"{pos:>4}  {len(vals):>6}  {avg:>10.2f}  {min(vals):>6.1f}  {max(vals):>6.1f}")

    if len(by_position) >= 2:
        pos1 = by_position.get(1, [0])
        pos2 = by_position.get(2, [0])
        avg1 = sum(pos1) / len(pos1) if pos1 else 0
        avg2 = sum(pos2) / len(pos2) if pos2 else 0
        ratio = avg2 / avg1 if avg1 > 0 else 0
        print(f"\n  Agent 2 contributes {ratio:.0%} of what Agent 1 contributes (marginal return)")
        if len(by_position) >= 3:
            pos3 = by_position.get(3, [0])
            avg3 = sum(pos3) / len(pos3) if pos3 else 0
            ratio3 = avg3 / avg1 if avg1 > 0 else 0
            print(f"  Agent 3 contributes {ratio3:.0%} of what Agent 1 contributes")


def show_summary(events):
    """Summary statistics across all spawn events."""
    total = len(events)
    verdicts = defaultdict(int)
    two_phase_count = 0
    partition_types = defaultdict(int)
    total_agents = 0
    total_cross_unique = 0
    total_waste = 0

    for ev in events:
        verdicts[ev.get("verdict", "unknown")] += 1
        if ev.get("two_phase"):
            two_phase_count += 1
        partition_types[ev.get("partition_type", "unknown")] += 1
        total_agents += ev.get("agents_spawned", 0)
        total_cross_unique += ev.get("cross_agent_unique", 0)

    print(f"=== SPAWN QUALITY SUMMARY ({total} events) ===\n")
    print(f"Total agents spawned: {total_agents}")
    print(f"Avg agents per event: {total_agents / total:.1f}")
    print(f"Events using two-phase: {two_phase_count}/{total} ({two_phase_count/total:.0%})")
    print(f"Total cross-agent unique findings: {total_cross_unique}")
    print(f"\nVerdicts:")
    for v, count in sorted(verdicts.items()):
        pct = count / total
        # Keep output ASCII so the tool works on default Windows code pages.
        bar = "#" * count
        print(f"  {v:<22} {count:>2} ({pct:.0%})  {bar}")
    print(f"\nPartition types:")
    for pt, count in sorted(partition_types.items(), key=lambda x: -x[1]):
        print(f"  {pt:<15} {count:>2}")

    # P-119 compliance
    print(f"\nP-119 compliance (two-phase before partition):")
    for ev in events:
        pt = ev.get("partition_type", "?")
        tp = ev.get("two_phase", False)
        verdict = ev.get("verdict", "?")
        marker = "OK" if tp else ("NO" if pt not in ["personality", "ablation"] else "~")
        print(f"  {ev['id']} [{pt}] two_phase={tp} -> {verdict} {marker}")


def show_latest(events):
    if not events:
        print("No events logged.")
        return
    ev = events[-1]
    print(f"=== LATEST SPAWN EVENT: {ev['id']} ===")
    print(f"Session: S{ev['session']} | Date: {ev['date']}")
    print(f"Task: {ev['task_description']}")
    print(f"Agents: {ev['agents_spawned']} ({', '.join(ev.get('agent_roles', []))})")
    print(f"Findings per agent: {ev.get('findings_per_agent', [])}")
    print(f"Overlap: {ev.get('overlap_count', '?')} | Cross-agent unique: {ev.get('cross_agent_unique', '?')}")
    print(f"Verdict: {ev.get('verdict', '?')}")
    print(f"Notes: {ev.get('notes', '')[:120]}...")


def size_summary(events):
    """Aggregate spawn outcomes by colony size (F92 signal view)."""
    by_n = defaultdict(list)
    for ev in events:
        n = ev.get("agents_spawned")
        if isinstance(n, int) and n > 0:
            by_n[n].append(ev)

    if not by_n:
        print("No spawn events with agents_spawned found.")
        return

    print("=== COLONY SIZE SNAPSHOT (F92) ===")
    print(f"{'N':>3}  {'Events':>6}  {'Justified':>9}  {'Avg Cross-U':>11}  {'Avg Findings':>12}  {'Speedup':>8}")
    print("-" * 68)

    for n in sorted(by_n):
        rows = by_n[n]
        count = len(rows)

        justified = sum(1 for ev in rows if ev.get("verdict") == "spawn_justified")
        justified_pct = (justified / count) * 100 if count else 0

        cross_unique = [ev.get("cross_agent_unique", 0) for ev in rows]
        avg_cross = sum(cross_unique) / len(cross_unique) if cross_unique else 0

        findings = [sum(ev.get("findings_per_agent", [])) for ev in rows]
        avg_findings = sum(findings) / len(findings) if findings else 0

        speedups = [ev.get("wall_time_speedup") for ev in rows if isinstance(ev.get("wall_time_speedup"), (int, float))]
        speedup_str = f"{(sum(speedups)/len(speedups)):.2f}x" if speedups else "n/a"

        print(f"{n:>3}  {count:>6}  {justified_pct:>8.0f}%  {avg_cross:>11.2f}  {avg_findings:>12.2f}  {speedup_str:>8}")

    print("\nDetails by N:")
    for n in sorted(by_n):
        rows = by_n[n]
        ids = ", ".join(ev.get("id", "?") for ev in rows)
        ptypes = sorted({ev.get("partition_type", "?") for ev in rows})
        two_phase_yes = sum(1 for ev in rows if ev.get("two_phase"))
        print(f"  N={n}: {ids} | partition={','.join(ptypes)} | two_phase={two_phase_yes}/{len(rows)}")

    print("\nNote: This is observational log data, not controlled same-task A/B runs.")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    events = load_log()

    if cmd == "show":
        show_summary(events)
    elif cmd == "marginal":
        marginal_novelty(events)
    elif cmd in ("size", "f92"):
        size_summary(events)
    elif cmd == "latest":
        show_latest(events)
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: spawn_quality.py [show|marginal|size|f92|latest]")
        sys.exit(1)


if __name__ == "__main__":
    main()
