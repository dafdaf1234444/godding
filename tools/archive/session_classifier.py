#!/usr/bin/env python3
"""
session_classifier.py — Accurate session-type classification (SIG-44 fix)

SESSION-LOG undercounts DOMEX sessions (36/198 unique vs 74 DOMEX rows in SWARM-LANES).
This tool joins SESSION-LOG + SWARM-LANES.md to produce accurate per-session labels.

Usage:
    python3 tools/session_classifier.py [--json] [--csv] [--session S402]
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent

SESSION_LOG = ROOT / "memory" / "SESSION-LOG.md"
SWARM_LANES = ROOT / "tasks" / "SWARM-LANES.md"


def parse_session_log():
    """Parse SESSION-LOG.md → {session_id: {lines, has_domex, lesson_count, principle_count}}"""
    sessions = {}
    if not SESSION_LOG.exists():
        return sessions
    with open(SESSION_LOG) as f:
        content = f.read()
    for line in content.split("\n"):
        m = re.match(r"^(S\d+[a-z]?)\s*\|(.+)$", line)
        if not m:
            continue
        sid = m.group(1)
        rest = m.group(2)
        # Normalize to base session number (S401a → S401)
        base = re.sub(r"[a-z]+$", "", sid)
        entry = sessions.setdefault(base, {
            "session": base,
            "log_lines": [],
            "log_has_domex": False,
            "lesson_delta": 0,
            "principle_delta": 0,
        })
        entry["log_lines"].append(rest.strip())
        if "DOMEX" in rest:
            entry["log_has_domex"] = True
        # Extract +NL and +NP
        lm = re.search(r"\+(\d+)L", rest)
        if lm:
            entry["lesson_delta"] += int(lm.group(1))
        pm = re.search(r"\+(\d+)P", rest)
        if pm:
            entry["principle_delta"] += int(pm.group(1))
    return sessions


def parse_swarm_lanes():
    """Parse SWARM-LANES.md → {session_id: {lane_ids, domains, statuses}}

    Extracts session ID from lane name (DOMEX-DOMAIN-SXXX) because the session
    column uses inconsistent formats (plain number vs S-prefixed). Lane name is
    authoritative — it encodes the session the lane was opened.
    """
    sessions = {}
    if not SWARM_LANES.exists():
        return sessions
    with open(SWARM_LANES) as f:
        content = f.read()
    for line in content.split("\n"):
        # Match any line containing a DOMEX lane reference
        m = re.search(r"(DOMEX-(\w+)-(S\d+))", line)
        if not m:
            continue
        lane_id = m.group(1)
        domain = m.group(2)
        sid = m.group(3)

        # Extract status from line
        status = "UNKNOWN"
        for s in ("MERGED", "ACTIVE", "ABANDONED", "STALE"):
            if s in line:
                status = s
                break

        entry = sessions.setdefault(sid, {
            "session": sid,
            "lanes": [],
            "domains": set(),
            "has_domex": True,
            "merged_count": 0,
            "active_count": 0,
            "abandoned_count": 0,
        })
        # Avoid duplicate lane entries (same lane_id can appear multiple times for updates)
        if not any(l["lane_id"] == lane_id for l in entry["lanes"]):
            entry["lanes"].append({"lane_id": lane_id, "domain": domain, "status": status})
        entry["domains"].add(domain)
        if status == "MERGED":
            entry["merged_count"] += 1
        elif status == "ACTIVE":
            entry["active_count"] += 1
        elif status == "ABANDONED":
            entry["abandoned_count"] += 1
    # Convert domain sets to lists for JSON serialization
    for v in sessions.values():
        v["domains"] = sorted(v["domains"])
    return sessions


def classify_session(log_entry, lane_entry):
    """Return session type: DOMEX, HARVEST, MAINTENANCE, META, or MIXED"""
    has_domex = (log_entry and log_entry.get("log_has_domex")) or (lane_entry is not None)
    if has_domex:
        if lane_entry and len(lane_entry["domains"]) > 1:
            return "DOMEX_MULTI"
        return "DOMEX"
    if log_entry:
        text = " ".join(log_entry["log_lines"]).lower()
        if any(w in text for w in ("harvest", "citation sprint", "citation_sprint")):
            return "HARVEST"
        if any(w in text for w in ("maintenance", "sync", "compaction", "compact")):
            return "MAINTENANCE"
        if any(w in text for w in ("meta", "orient", "bridge")):
            return "META"
    return "OTHER"


def build_classifications(log_sessions, lane_sessions, filter_session=None):
    """Join log + lanes, produce per-session classification records."""
    all_sids = set(log_sessions.keys()) | set(lane_sessions.keys())
    if filter_session:
        all_sids = {s for s in all_sids if s == filter_session}

    results = []
    for sid in sorted(all_sids, key=lambda s: int(re.sub(r"\D", "", s) or 0)):
        log_e = log_sessions.get(sid)
        lane_e = lane_sessions.get(sid)
        session_type = classify_session(log_e, lane_e)
        lane_count = len(lane_e["lanes"]) if lane_e else 0
        domains = lane_e["domains"] if lane_e else []
        merged = lane_e["merged_count"] if lane_e else 0
        results.append({
            "session": sid,
            "type": session_type,
            "in_log": log_e is not None,
            "in_lanes": lane_e is not None,
            "lane_count": lane_count,
            "domains": domains,
            "merged_lanes": merged,
            "lesson_delta": log_e["lesson_delta"] if log_e else 0,
            "principle_delta": log_e["principle_delta"] if log_e else 0,
            "log_summary": log_e["log_lines"][0][:80] if log_e else "",
        })
    return results


def print_summary(results):
    """Print coverage summary and type distribution."""
    from collections import Counter
    types = Counter(r["type"] for r in results)
    in_log = sum(1 for r in results if r["in_log"])
    in_lanes = sum(1 for r in results if r["in_lanes"])
    in_both = sum(1 for r in results if r["in_log"] and r["in_lanes"])
    domex_total = sum(1 for r in results if r["type"].startswith("DOMEX"))

    print(f"=== SESSION CLASSIFIER REPORT ===")
    print(f"Total unique sessions (union): {len(results)}")
    print(f"  In SESSION-LOG:  {in_log}")
    print(f"  In SWARM-LANES:  {in_lanes}")
    print(f"  In both:         {in_both}")
    print(f"  LOG-only gap:    {in_log - in_both} sessions lost if only using LANES")
    print(f"  LANES-only gap:  {in_lanes - in_both} sessions lost if only using LOG")
    print()
    print("Session type distribution (union source):")
    for t, c in types.most_common():
        pct = 100 * c / len(results)
        print(f"  {t:<15} {c:>4}  ({pct:.1f}%)")
    print()
    print(f"DOMEX sessions (total, both sources): {domex_total}")
    print(f"SIG-44 fix: SESSION-LOG DOMEX count would be {sum(1 for r in results if r['in_log'] and r['type'].startswith('DOMEX'))} vs union {domex_total}")


def main():
    parser = argparse.ArgumentParser(description="Accurate session-type classification (SIG-44 fix)")
    parser.add_argument("--json", action="store_true", help="Output full JSON records")
    parser.add_argument("--csv", action="store_true", help="Output CSV")
    parser.add_argument("--session", help="Filter to single session, e.g. S402")
    parser.add_argument("--type", help="Filter by session type, e.g. DOMEX")
    args = parser.parse_args()

    log_sessions = parse_session_log()
    lane_sessions = parse_swarm_lanes()
    results = build_classifications(log_sessions, lane_sessions, args.session)

    if args.type:
        results = [r for r in results if args.type in r["type"]]

    if args.json:
        print(json.dumps(results, indent=2))
    elif args.csv:
        if results:
            writer = csv.DictWriter(sys.stdout, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    else:
        print_summary(results)


if __name__ == "__main__":
    main()
