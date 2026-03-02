#!/usr/bin/env python3
"""
reach_map.py — Measure how far the swarm reaches.

"Swarm has to swarm everywhere." This tool measures WHERE the swarm is active
vs dormant, across four dimensions:

  1. Tool reach:    How many bridge files are fresh and synced?
  2. Domain reach:  How many domains have active DOMEX lanes / recent lessons?
  3. Knowledge reach: How evenly distributed is knowledge across domains?
  4. Protocol reach: How many domains follow orient→act→compress cycle?

Usage:
  python3 tools/reach_map.py              # full reach report
  python3 tools/reach_map.py --json       # JSON output for experiments
  python3 tools/reach_map.py --gaps       # show only dormant/unreached areas
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOMAINS_DIR = ROOT / "domains"
LESSONS_DIR = ROOT / "memory" / "lessons"
LANES_FILE = ROOT / "tasks" / "SWARM-LANES.md"

# Bridge files that make the swarm accessible from each tool
BRIDGE_FILES = {
    "claude-code": ROOT / "CLAUDE.md",
    "codex-copilot": ROOT / "AGENTS.md",
    "cursor": ROOT / ".cursorrules",
    "gemini": ROOT / "GEMINI.md",
    "windsurf": ROOT / ".windsurfrules",
    "copilot": ROOT / ".github" / "copilot-instructions.md",
}


def _current_session() -> int:
    """Get current session number from git log."""
    try:
        r = subprocess.run(
            ["git", "log", "--oneline", "-20"],
            capture_output=True, text=True, cwd=ROOT,
        )
        for line in r.stdout.splitlines():
            m = re.search(r"\[S(\d+)\]", line)
            if m:
                return int(m.group(1))
    except Exception:
        pass
    return 0


def measure_tool_reach() -> dict:
    """Check bridge file existence, freshness, and SWARM.md loading."""
    results = {}
    for tool, path in BRIDGE_FILES.items():
        entry = {"exists": False, "loads_swarm": False, "has_expert_dispatch": False}
        if path.exists():
            entry["exists"] = True
            content = path.read_text(errors="ignore")
            entry["loads_swarm"] = "SWARM.md" in content
            entry["has_expert_dispatch"] = "dispatch_optimizer" in content
            # Check git last-modified session
            try:
                r = subprocess.run(
                    ["git", "log", "--oneline", "-1", "--", str(path.relative_to(ROOT))],
                    capture_output=True, text=True, cwd=ROOT,
                )
                m = re.search(r"\[S(\d+)\]", r.stdout)
                if m:
                    entry["last_session"] = int(m.group(1))
            except Exception:
                pass
        results[tool] = entry

    total = len(BRIDGE_FILES)
    active = sum(1 for v in results.values() if v["exists"] and v["loads_swarm"])
    return {
        "bridges": results,
        "score": round(active / total, 3) if total else 0,
        "active": active,
        "total": total,
    }


def measure_domain_reach() -> dict:
    """Check domain activation: COLONY.md, FRONTIER.md, recent DOMEX lanes, lessons."""
    current_session = _current_session()
    domains = {}

    if not DOMAINS_DIR.exists():
        return {"domains": {}, "score": 0, "active": 0, "dormant": 0, "total": 0}

    for d in sorted(DOMAINS_DIR.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        entry = {
            "has_colony": (d / "COLONY.md").exists(),
            "has_frontier": (d / "tasks" / "FRONTIER.md").exists(),
            "has_domain_md": (d / "DOMAIN.md").exists(),
            "has_index": (d / "INDEX.md").exists(),
            "lesson_count": 0,
            "active_lanes": 0,
            "last_domex_session": 0,
            "status": "dormant",
        }

        # Count lessons mentioning this domain
        domain_pattern = name.lower().replace("-", "[ -]?")
        if LESSONS_DIR.exists():
            for lf in LESSONS_DIR.glob("L-*.md"):
                try:
                    text = lf.read_text(errors="ignore")
                    if re.search(rf"(?i)domain:\s*{domain_pattern}", text):
                        entry["lesson_count"] += 1
                except Exception:
                    pass

        # Check SWARM-LANES for active DOMEX lanes
        if LANES_FILE.exists():
            lanes_text = LANES_FILE.read_text(errors="ignore")
            domain_short = name.upper().replace("-", "")[:5]
            for line in lanes_text.splitlines():
                if f"DOMEX-{domain_short}" in line.upper() or name in line.lower():
                    if "ACTIVE" in line.upper():
                        entry["active_lanes"] += 1
                    m = re.search(r"S(\d+)", line)
                    if m:
                        s = int(m.group(1))
                        entry["last_domex_session"] = max(entry["last_domex_session"], s)

        # Classify status
        staleness = current_session - entry["last_domex_session"] if entry["last_domex_session"] else 999
        if entry["active_lanes"] > 0:
            entry["status"] = "active"
        elif staleness <= 10:
            entry["status"] = "recent"
        elif entry["lesson_count"] > 0 or entry["has_frontier"]:
            entry["status"] = "dormant"
        else:
            entry["status"] = "empty"

        domains[name] = entry

    total = len(domains)
    active = sum(1 for v in domains.values() if v["status"] in ("active", "recent"))
    dormant = sum(1 for v in domains.values() if v["status"] == "dormant")
    empty = sum(1 for v in domains.values() if v["status"] == "empty")

    return {
        "domains": domains,
        "score": round(active / total, 3) if total else 0,
        "active": active,
        "dormant": dormant,
        "empty": empty,
        "total": total,
    }


def measure_knowledge_reach() -> dict:
    """Measure how evenly knowledge is distributed across domains."""
    domain_lessons = defaultdict(int)
    total_lessons = 0
    untagged = 0

    if LESSONS_DIR.exists():
        for lf in sorted(LESSONS_DIR.glob("L-*.md")):
            try:
                text = lf.read_text(errors="ignore")
                total_lessons += 1
                m = re.search(r"(?i)domain:\s*(.+)", text)
                if m:
                    domain = m.group(1).strip().split("|")[0].strip().split(",")[0].strip()
                    domain_lessons[domain.lower()] += 1
                else:
                    untagged += 1
            except Exception:
                pass

    counts = list(domain_lessons.values())
    if not counts:
        return {"distribution": {}, "gini": 1.0, "score": 0, "untagged": untagged}

    # Gini coefficient: 0 = perfect equality, 1 = all in one domain
    n = len(counts)
    mean_c = sum(counts) / n
    if mean_c == 0:
        gini = 1.0
    else:
        abs_diffs = sum(abs(counts[i] - counts[j]) for i in range(n) for j in range(n))
        gini = abs_diffs / (2 * n * n * mean_c)

    # Top and bottom domains
    sorted_domains = sorted(domain_lessons.items(), key=lambda x: -x[1])

    return {
        "total_lessons": total_lessons,
        "tagged_domains": len(domain_lessons),
        "untagged": untagged,
        "gini": round(gini, 4),
        "score": round(1 - gini, 3),  # higher = more even distribution = better reach
        "top_5": sorted_domains[:5],
        "bottom_5": sorted_domains[-5:] if len(sorted_domains) > 5 else sorted_domains,
    }


def measure_protocol_reach() -> dict:
    """Check which domains have full protocol penetration (COLONY + FRONTIER + INDEX)."""
    protocol_complete = 0
    protocol_partial = 0
    protocol_none = 0
    details = {}

    if not DOMAINS_DIR.exists():
        return {"score": 0, "complete": 0, "partial": 0, "none": 0}

    for d in sorted(DOMAINS_DIR.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        checks = {
            "colony": (d / "COLONY.md").exists(),
            "frontier": (d / "tasks" / "FRONTIER.md").exists(),
            "index": (d / "INDEX.md").exists(),
            "domain_md": (d / "DOMAIN.md").exists(),
        }
        score = sum(checks.values())
        if score == 4:
            protocol_complete += 1
            status = "complete"
        elif score >= 2:
            protocol_partial += 1
            status = "partial"
        else:
            protocol_none += 1
            status = "none"
        details[name] = {"checks": checks, "status": status, "score": score}

    total = protocol_complete + protocol_partial + protocol_none
    return {
        "score": round(protocol_complete / total, 3) if total else 0,
        "complete": protocol_complete,
        "partial": protocol_partial,
        "none": protocol_none,
        "total": total,
        "details": details,
    }


def composite_reach_score(tool, domain, knowledge, protocol) -> dict:
    """Compute composite reach score across all dimensions."""
    weights = {"tool": 0.15, "domain": 0.35, "knowledge": 0.20, "protocol": 0.30}
    scores = {
        "tool": tool["score"],
        "domain": domain["score"],
        "knowledge": knowledge["score"],
        "protocol": protocol["score"],
    }
    composite = sum(scores[k] * weights[k] for k in weights)
    return {
        "composite": round(composite, 4),
        "components": scores,
        "weights": weights,
    }


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    gaps_only = "--gaps" in args

    tool = measure_tool_reach()
    domain = measure_domain_reach()
    knowledge = measure_knowledge_reach()
    protocol = measure_protocol_reach()
    composite = composite_reach_score(tool, domain, knowledge, protocol)

    if as_json:
        print(json.dumps({
            "tool_reach": tool,
            "domain_reach": domain,
            "knowledge_reach": knowledge,
            "protocol_reach": protocol,
            "composite": composite,
            "session": f"S{_current_session()}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, indent=2, default=str))
        return

    print(f"=== REACH MAP (S{_current_session()}) ===")
    print(f"  Composite reach: {composite['composite']:.1%}")
    print()

    # Tool reach
    print(f"  Tool reach: {tool['score']:.0%} ({tool['active']}/{tool['total']} bridges active)")
    if not gaps_only:
        for name, info in tool["bridges"].items():
            marker = "OK" if info["exists"] and info["loads_swarm"] else "GAP"
            session = f"S{info.get('last_session', '?')}" if info.get("last_session") else "?"
            print(f"    [{marker}] {name}: {session}")
    print()

    # Domain reach
    print(f"  Domain reach: {domain['score']:.0%} ({domain['active']}/{domain['total']} active)")
    print(f"    Active: {domain['active']} | Dormant: {domain['dormant']} | Empty: {domain['empty']}")
    if gaps_only:
        dormant_list = [k for k, v in domain["domains"].items() if v["status"] in ("dormant", "empty")]
        if dormant_list:
            print(f"    Dormant/empty: {', '.join(dormant_list[:15])}{'...' if len(dormant_list) > 15 else ''}")
    else:
        for name, info in sorted(domain["domains"].items(), key=lambda x: x[1]["status"]):
            marker = {"active": "+", "recent": "~", "dormant": "-", "empty": " "}[info["status"]]
            lessons = info["lesson_count"]
            lanes = info["active_lanes"]
            print(f"    [{marker}] {name}: {lessons}L {lanes} active lanes (last DOMEX S{info['last_domex_session'] or '?'})")
    print()

    # Knowledge reach
    print(f"  Knowledge reach: {knowledge['score']:.0%} (Gini={knowledge['gini']:.3f}, {knowledge['tagged_domains']} domains)")
    if knowledge.get("top_5"):
        top = ", ".join(f"{d}({n})" for d, n in knowledge["top_5"])
        print(f"    Top-5: {top}")
    if knowledge.get("bottom_5") and not gaps_only:
        bottom = ", ".join(f"{d}({n})" for d, n in knowledge["bottom_5"])
        print(f"    Bottom-5: {bottom}")
    if knowledge["untagged"]:
        print(f"    Untagged lessons: {knowledge['untagged']}")
    print()

    # Protocol reach
    print(f"  Protocol reach: {protocol['score']:.0%} ({protocol['complete']}/{protocol['total']} full protocol)")
    if gaps_only:
        partial = [k for k, v in protocol["details"].items() if v["status"] != "complete"]
        if partial:
            print(f"    Incomplete: {', '.join(partial[:10])}{'...' if len(partial) > 10 else ''}")
    print()

    # Overall assessment
    score = composite["composite"]
    if score >= 0.8:
        verdict = "STRONG"
    elif score >= 0.5:
        verdict = "MODERATE"
    elif score >= 0.3:
        verdict = "WEAK"
    else:
        verdict = "CRITICAL"
    print(f"  Verdict: {verdict} — swarm {'reaches' if score >= 0.5 else 'does NOT reach'} everywhere")

    if score < 0.8:
        print()
        print("  Priority gaps:")
        if domain["score"] < 0.3:
            print(f"    - Domain activation: {domain['dormant']} dormant domains need DOMEX lanes")
        if knowledge["gini"] > 0.5:
            print(f"    - Knowledge concentration: Gini {knowledge['gini']:.3f} — lessons cluster in few domains")
        if tool["score"] < 1.0:
            print(f"    - Tool coverage: {tool['total'] - tool['active']} bridge files missing or broken")
        if protocol["score"] < 0.9:
            print(f"    - Protocol gaps: {protocol['partial'] + protocol['none']} domains lack full protocol files")


if __name__ == "__main__":
    main()
