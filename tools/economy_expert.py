#!/usr/bin/env python3
"""
economy_expert.py — Swarm Economy Analyst

Models two economic systems:
  1. Internal economy: knowledge production (L+P), resource consumption (Proxy-K),
     yield ratios, Sharpe-quality filtering, capital depreciation via compaction.
  2. Helper economy: delegation cost vs stall-recovery value, capacity planning,
     helper-spawn ROI.

Usage:
  python3 tools/economy_expert.py          # human-readable report
  python3 tools/economy_expert.py --json   # machine-readable JSON
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Internal economy: production
# ---------------------------------------------------------------------------

def _parse_session_log() -> list[dict]:
    """Extract per-session L+P production from SESSION-LOG.md."""
    log_path = ROOT / "memory" / "SESSION-LOG.md"
    if not log_path.exists():
        return []
    sessions: list[dict] = []
    pat = re.compile(r"S(\d+)\s*[\t|].*?\+(\d+)L.*?\+(\d+)P")
    for line in log_path.read_text(encoding="utf-8").splitlines():
        m = pat.search(line)
        if m:
            sessions.append(
                {
                    "session": int(m.group(1)),
                    "lessons": int(m.group(2)),
                    "principles": int(m.group(3)),
                }
            )
    return sessions


def compute_production(sessions: list[dict]) -> dict:
    """Knowledge production velocity and acceleration."""
    if not sessions:
        return {}
    total_l = sum(s["lessons"] for s in sessions)
    total_p = sum(s["principles"] for s in sessions)
    n = len(sessions)
    avg_l = total_l / n
    avg_p = total_p / n
    recent = sessions[-10:]
    recent_l = sum(s["lessons"] for s in recent) / len(recent)
    recent_p = sum(s["principles"] for s in recent) / len(recent)
    productive = sum(1 for s in sessions if s["lessons"] + s["principles"] > 0)
    accel = round(recent_l / avg_l, 3) if avg_l > 0 else None
    return {
        "total_lessons": total_l,
        "total_principles": total_p,
        "sessions_sampled": n,
        "avg_lessons_per_session": round(avg_l, 3),
        "avg_principles_per_session": round(avg_p, 3),
        "recent_lessons_per_session": round(recent_l, 3),
        "recent_principles_per_session": round(recent_p, 3),
        "productivity_rate": round(productive / n, 3),
        "acceleration": accel,
    }


# ---------------------------------------------------------------------------
# Internal economy: resource (Proxy-K)
# ---------------------------------------------------------------------------

def _load_proxy_k_floor_from_log() -> tuple[int | None, dict]:
    log_path = ROOT / "experiments" / "proxy-k-log.json"
    if not log_path.exists():
        return None, {}
    try:
        entries = json.loads(log_path.read_text(encoding="utf-8"))
    except Exception:
        return None, {}
    if not entries:
        return None, {}

    schema = entries[-1].get("tier_schema")
    if schema:
        schema_entries = [e for e in entries if e.get("tier_schema") == schema]
        if len(schema_entries) >= 2:
            entries = schema_entries
        else:
            return None, {}
    if len(entries) < 2:
        return None, {}

    floor_idx = 0
    for i in range(1, len(entries)):
        if entries[i].get("total", 0) < entries[i - 1].get("total", 0):
            floor_idx = i
    floor_entry = entries[floor_idx]
    floor_val = floor_entry.get("total")
    if not isinstance(floor_val, int) or floor_val <= 0:
        return None, {}

    meta = {
        "floor_session": floor_entry.get("session"),
        "floor_date": floor_entry.get("date"),
        "floor_dirty": floor_entry.get("dirty_tree"),
    }
    return floor_val, meta


def read_proxy_k() -> dict:
    """Read Proxy-K current total and floor; compute drift."""
    import subprocess

    # Get current token count from proxy_k.py
    current: int | None = None
    try:
        result = subprocess.run(
            ["python3", str(ROOT / "tools" / "proxy_k.py")],
            capture_output=True, text=True, cwd=ROOT, timeout=30
        )
        m = re.search(r"TOTAL\s+([\d,]+)\s+tokens", result.stdout)
        if m:
            current = int(m.group(1).replace(",", ""))
    except Exception:
        pass

    floor: int | None = None
    floor_source: str | None = None
    floor_meta: dict = {}
    log_floor, log_meta = _load_proxy_k_floor_from_log()
    if log_floor:
        floor = log_floor
        floor_source = "proxy-k-log"
        floor_meta = log_meta

    # Fallback: session log (most recent "floor NNNt" on a proxy-K line)
    if floor is None:
        log_path = ROOT / "memory" / "SESSION-LOG.md"
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8")
            # Look for lines explicitly about proxy-K with a floor value
            for line in reversed(text.splitlines()):
                if "proxy" in line.lower() and "floor" in line.lower():
                    m = re.search(r"floor[= ]?(\d[\d,]+)t", line)
                    if m:
                        floor = int(m.group(1).replace(",", ""))
                        floor_source = "session-log"
                        break

    drift: float | None = None
    if current is not None and floor and floor > 0:
        drift = round((current - floor) / floor * 100, 2)

    status = (
        "URGENT" if drift is not None and drift > 10
        else "DUE" if drift is not None and drift > 6
        else "HEALTHY" if drift is not None
        else "UNKNOWN"
    )
    return {
        "floor_tokens": floor,
        "current_tokens": current,
        "drift_pct": drift,
        "status": status,
        "floor_source": floor_source,
        **floor_meta,
    }


# ---------------------------------------------------------------------------
# Internal economy: knowledge quality (Sharpe)
# ---------------------------------------------------------------------------

def compute_sharpe() -> dict:
    """Lesson Sharpe ratio: citations / lines — quality density of capital stock."""
    lessons_dir = ROOT / "memory" / "lessons"
    if not lessons_dir.exists():
        return {}

    # Build citation corpus (everything except lessons themselves)
    all_docs = []
    for f in ROOT.rglob("*.md"):
        if "lessons" not in str(f):
            try:
                all_docs.append(f.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                pass
    corpus = "\n".join(all_docs)

    scores: list[float] = []
    zero_count = 0
    for lf in sorted(lessons_dir.glob("L-*.md")):
        if lf.stem == "TEMPLATE":
            continue
        try:
            lines = len(
                [ln for ln in lf.read_text(encoding="utf-8").splitlines() if ln.strip()]
            )
            cites = corpus.count(lf.stem)
            sharpe = cites / max(lines, 1)
            scores.append(sharpe)
            if cites == 0:
                zero_count += 1
        except Exception:
            continue

    if not scores:
        return {}
    mean = sum(scores) / len(scores)
    return {
        "lessons_analyzed": len(scores),
        "zero_sharpe_count": zero_count,
        "zero_sharpe_rate": round(zero_count / len(scores), 3),
        "mean_sharpe": round(mean, 6),
        "compaction_candidates": zero_count,
        "capital_rot_warning": zero_count / len(scores) > 0.6,
    }


# ---------------------------------------------------------------------------
# Task economy: lane throughput
# ---------------------------------------------------------------------------

def read_lanes() -> dict:
    """Parse SWARM-LANES.md for task flow metrics."""
    lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
    if not lanes_path.exists():
        return {}
    text = lanes_path.read_text(encoding="utf-8")
    # Extract Status from the ACTUAL Status column, not by regex matching
    # the whole row (which false-positives on Etc metadata like
    # "progress=active").  The table format ends: ... | Etc | Status | Notes |
    # so Status is always the third-from-last pipe-delimited field (cols[-3]),
    # which is robust even if Etc contains extra '|' characters.
    statuses: list[str] = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
            continue
        cols = line.split("|")
        # Minimum: | ... | Status | Notes | → at least 4 parts (empty, ..., Status, Notes, empty)
        if len(cols) < 4:
            continue
        statuses.append(cols[-3].strip())
    active = sum(1 for s in statuses if s == "ACTIVE" or s == "CLAIMED")
    ready = sum(1 for s in statuses if s == "READY")
    done = sum(1 for s in statuses if s == "MERGED")
    abandoned = sum(1 for s in statuses if s == "ABANDONED")
    blocked = sum(1 for s in statuses if s == "BLOCKED")
    total = active + ready + done + abandoned + blocked
    return {
        "active": active,
        "ready": ready,
        "done": done,
        "abandoned": abandoned,
        "blocked": blocked,
        "total": total,
        "throughput_rate": round(done / total, 3) if total else 0,
        "blockage_rate": round(blocked / total, 3) if total else 0,
    }


def read_frontiers() -> dict:
    """Frontier open/close ratio = knowledge backlog pressure."""
    fp = ROOT / "tasks" / "FRONTIER.md"
    ap = ROOT / "tasks" / "FRONTIER-ARCHIVE.md"
    open_count = 0
    resolved = 0
    if fp.exists():
        text = fp.read_text(encoding="utf-8")
        open_count = len(re.findall(r"^\s*-\s*\*\*F\d+\*\*", text, re.MULTILINE))
    if ap.exists():
        text = ap.read_text(encoding="utf-8")
        resolved = max(0, len(re.findall(r"^\|", text, re.MULTILINE)) - 2)
    total = open_count + resolved
    return {
        "open": open_count,
        "resolved": resolved,
        "resolution_rate": round(resolved / total, 3) if total else 0,
        "backlog_pressure": round(open_count / max(1, resolved), 3),
    }


# ---------------------------------------------------------------------------
# Helper economy: delegation ROI
# ---------------------------------------------------------------------------

# Economic constants (empirically derived from swarm history)
_SPAWN_OVERHEAD_FRACTION = 0.15   # fraction of a session consumed by spawning a helper
_STALL_COST_PER_LANE = 0.5        # L+P lost per blocked lane per session
_RECOVERY_SESSIONS = 3.0          # sessions of stall a helper rescues
_MAX_HELPER_SLOTS = 3             # beyond 3 helpers, coordination overhead dominates


def analyze_helper_economy(lanes: dict) -> dict:
    """
    Model helper-swarm delegation economics.

    ROI model:
      recovery_value = stall_cost_per_lane × recovery_sessions
      delegation_cost = spawn_overhead_fraction (≈15% session)
      net_roi = (recovery_value - delegation_cost) / delegation_cost
    """
    blocked = lanes.get("blocked", 0)
    recovery_value = _STALL_COST_PER_LANE * _RECOVERY_SESSIONS
    net_roi = (recovery_value - _SPAWN_OVERHEAD_FRACTION) / _SPAWN_OVERHEAD_FRACTION
    recommended = min(blocked, _MAX_HELPER_SLOTS)
    return {
        "blocked_lanes": blocked,
        "recovery_value_per_helper": round(recovery_value, 2),
        "spawn_overhead_fraction": _SPAWN_OVERHEAD_FRACTION,
        "helper_roi": round(net_roi, 2),
        "recommended_helpers": recommended,
        "delegation_triggered": blocked >= 2,
        "trigger_threshold": 2,
        "max_helper_slots": _MAX_HELPER_SLOTS,
        "capacity_note": (
            f"Spawn {recommended} helper(s) to recover {recommended * _RECOVERY_SESSIONS:.0f} sessions of stall"
            if blocked >= 2
            else "No delegation needed — no blocked lanes or only 1"
        ),
        "roi_status": "POSITIVE" if net_roi > 0 else "NEGATIVE",
    }


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def recommendations(production: dict, proxy: dict, sharpe: dict,
                    lanes: dict, frontiers: dict, helper: dict) -> list[str]:
    recs: list[str] = []

    # Production trend
    accel = production.get("acceleration")
    if accel is not None:
        if accel < 0.7:
            recs.append(
                f"WARN: production deceleration ({accel:.2f}x) — recent sessions below historical L+P average"
            )
        elif accel > 1.5:
            recs.append(f"INFO: production accelerating ({accel:.2f}x above historical average)")

    prod_rate = production.get("productivity_rate", 1.0)
    if prod_rate < 0.4:
        recs.append(
            f"WARN: only {prod_rate:.0%} of sessions generate L or P — low productive yield"
        )

    # Proxy-K resource
    status = proxy.get("status", "UNKNOWN")
    drift = proxy.get("drift_pct")
    if status == "URGENT":
        recs.append(f"URGENT: proxy-K drift {drift}% exceeds 10% — run compact.py immediately")
    elif status == "DUE":
        recs.append(f"DUE: proxy-K drift {drift}% exceeds 6% threshold — schedule compaction")

    # Knowledge quality
    zero_rate = sharpe.get("zero_sharpe_rate", 0)
    if zero_rate > 0.6:
        recs.append(
            f"WARN: {sharpe.get('zero_sharpe_count')} lessons ({zero_rate:.0%}) have zero Sharpe"
            " — capital rot; run compact.py"
        )
    elif zero_rate > 0.4:
        recs.append(
            f"INFO: {sharpe.get('zero_sharpe_count')} zero-Sharpe lessons ({zero_rate:.0%})"
            " — approaching compaction threshold"
        )

    # Task flow
    blockage = lanes.get("blockage_rate", 0)
    if blockage > 0.3:
        recs.append(
            f"WARN: blockage rate {blockage:.0%} — consider helper spawns for stalled lanes"
        )

    throughput = lanes.get("throughput_rate", 1.0)
    if throughput < 0.4:
        recs.append(
            f"WARN: task throughput rate {throughput:.0%} — low delivery; audit ACTIVE lanes"
        )

    # Frontier backlog
    pressure = frontiers.get("backlog_pressure", 0)
    if pressure > 3.0:
        recs.append(
            f"WARN: frontier backlog pressure {pressure:.1f} — close before opening new frontiers"
        )

    # Helper delegation
    if helper.get("delegation_triggered"):
        n = helper["recommended_helpers"]
        roi = helper["helper_roi"]
        recs.append(
            f"TRIGGER: {n} helper spawn(s) recommended (ROI={roi}x, {helper['capacity_note']})"
        )

    if not recs:
        recs.append("OK: swarm economy healthy — no urgent economic interventions needed")

    return recs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run() -> dict:
    sessions = _parse_session_log()
    prod = compute_production(sessions)
    proxy = read_proxy_k()
    sharpe = compute_sharpe()
    lanes = read_lanes()
    frontiers = read_frontiers()
    helper = analyze_helper_economy(lanes)
    recs = recommendations(prod, proxy, sharpe, lanes, frontiers, helper)
    return {
        "internal_economy": {
            "production": prod,
            "resource": proxy,
            "knowledge_quality": sharpe,
        },
        "task_economy": {
            "lanes": lanes,
            "frontiers": frontiers,
        },
        "helper_economy": helper,
        "recommendations": recs,
    }


def _fmt(report: dict) -> None:
    prod = report["internal_economy"]["production"]
    proxy = report["internal_economy"]["resource"]
    sharpe = report["internal_economy"]["knowledge_quality"]
    lanes = report["task_economy"]["lanes"]
    frontiers = report["task_economy"]["frontiers"]
    helper = report["helper_economy"]
    recs = report["recommendations"]

    print("=== SWARM ECONOMY REPORT ===\n")

    print("--- Internal Economy ---")
    if prod:
        avg_l = prod.get("avg_lessons_per_session", 0)
        avg_p = prod.get("avg_principles_per_session", 0)
        rec_l = prod.get("recent_lessons_per_session", 0)
        rec_p = prod.get("recent_principles_per_session", 0)
        pr = prod.get("productivity_rate", 0)
        accel = prod.get("acceleration")
        print(f"  Production (avg):  {avg_l:.2f}L + {avg_p:.2f}P / session")
        print(f"  Production (10s):  {rec_l:.2f}L + {rec_p:.2f}P / session (recent)")
        print(f"  Productivity rate: {pr:.0%} of sessions generate L or P")
        if accel is not None:
            trend = "↑ accel" if accel > 1.1 else ("↓ decel" if accel < 0.9 else "→ stable")
            print(f"  Velocity trend:    {accel:.2f}x ({trend})")
    if sharpe:
        print(
            f"  Lesson Sharpe:     mean={sharpe.get('mean_sharpe', 0):.5f}"
            f"  |  zero-Sharpe={sharpe.get('zero_sharpe_count', 0)}"
            f" ({sharpe.get('zero_sharpe_rate', 0):.0%})"
        )
    if proxy.get("floor_tokens"):
        current = proxy.get("current_tokens", "?")
        current_fmt = f"{current:,}" if isinstance(current, int) else current
        source = proxy.get("floor_source")
        source_note = f" ({source})" if source else ""
        print(
            f"  Proxy-K:           floor={proxy['floor_tokens']:,}t{source_note}"
            f"  current={current_fmt}t"
            f"  drift={proxy.get('drift_pct', '?')}%"
            f"  [{proxy.get('status', '?')}]"
        )

    print("\n--- Task Economy ---")
    if lanes:
        print(
            f"  Lanes: {lanes['active']} active | {lanes['ready']} ready"
            f" | {lanes['done']} done | {lanes.get('abandoned', 0)} abandoned"
            f" | {lanes['blocked']} blocked"
        )
        print(
            f"  Throughput:  {lanes['throughput_rate']:.0%}"
            f"   Blockage: {lanes['blockage_rate']:.0%}"
        )
    if frontiers:
        print(
            f"  Frontiers: {frontiers['open']} open | {frontiers['resolved']} resolved"
            f" | resolution={frontiers['resolution_rate']:.0%}"
            f"  pressure={frontiers['backlog_pressure']:.2f}"
        )

    print("\n--- Helper Economy ---")
    print(f"  Blocked lanes:  {helper['blocked_lanes']}")
    print(f"  Helper ROI:     {helper['helper_roi']}x  (spawn cost={helper['spawn_overhead_fraction']:.0%} session)")
    print(f"  Delegation:     {'TRIGGERED' if helper['delegation_triggered'] else 'CLEAR'}")
    if helper["delegation_triggered"]:
        print(f"  Action:         {helper['capacity_note']}")

    print("\n--- Recommendations ---")
    for r in recs:
        print(f"  {r}")
    print()


def main() -> None:
    report = run()
    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        _fmt(report)


if __name__ == "__main__":
    main()
