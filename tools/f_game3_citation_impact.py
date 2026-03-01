#!/usr/bin/env python3
"""F-GAME3 extension: Flow-zone citation impact analysis.

Tests whether frontier resolution timing predicts lesson quality (citation impact).
Flow theory from game design: optimal engagement in the "flow zone" between
boredom (too easy/fast) and anxiety (too hard/slow).

Zones:
  - Boredom: frontier resolved in 1 session
  - Flow: resolved in 2-10 sessions
  - Stalled: resolved in 11-15 sessions
  - Anxiety: >15 sessions or still open
"""

import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTIER_FILE = ROOT / "tasks" / "FRONTIER.md"
FRONTIER_ARCHIVE = ROOT / "tasks" / "FRONTIER-ARCHIVE.md"
LESSONS_DIR = ROOT / "memory" / "lessons"
DOMAIN_DIR = ROOT / "domains"
CITE_RE = re.compile(r"\bL-(\d+)\b")
FRONTIER_RE = re.compile(r"\bF-?(\w+)\b")


def parse_all_lessons():
    """Parse lessons with full citation data."""
    lessons = {}
    for p in LESSONS_DIR.glob("L-*.md"):
        m = re.match(r"L-(\d+)\.md$", p.name)
        if not m:
            continue
        num = int(m.group(1))
        text = p.read_text(errors="replace")
        # Extract session — multiple formats across eras
        sess_m = (
            re.search(r"session:\s*S(\d+)", text, re.IGNORECASE)
            or re.search(r"\*\*Session\*\*:\s*S?(\d+)", text)
            or re.search(r"Session:\s*S?(\d+)", text)
            or re.search(r"\|\s*S(\d+)\s*\|", text)
        )
        session = int(sess_m.group(1)) if sess_m else None
        dom_m = re.search(r"domain:\s*(\S+)", text, re.IGNORECASE)
        domain = dom_m.group(1).rstrip(",|") if dom_m else None
        cites = {int(c.group(1)) for c in CITE_RE.finditer(text) if int(c.group(1)) != num}
        # Extract frontier references
        frontiers = set()
        for fm in re.finditer(r"\bF[-_]?([A-Z]+\d+|\d+)\b", text):
            frontiers.add(f"F-{fm.group(1)}" if not fm.group(0).startswith("F-") else fm.group(0))
        # Also check for plain F### references
        for fm in re.finditer(r"\bF(\d+)\b", text):
            frontiers.add(f"F{fm.group(1)}")

        lessons[num] = {
            "session": session,
            "domain": domain,
            "cites": cites,
            "frontiers": frontiers,
            "in_degree": 0,
        }
    # Compute in-degree
    for num, info in lessons.items():
        for cited in info["cites"]:
            if cited in lessons:
                lessons[cited]["in_degree"] += 1
    return lessons


def parse_frontier_resolution():
    """Parse frontier open/resolved sessions from FRONTIER.md and archive."""
    frontiers = {}

    # Parse archive (resolved frontiers with clear resolution data)
    if FRONTIER_ARCHIVE.exists():
        text = FRONTIER_ARCHIVE.read_text(errors="replace")
        for line in text.split("\n"):
            if "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 5:
                continue
            fid = parts[1].strip()
            if not fid or fid == "ID" or fid == "---":
                continue
            answer = parts[2] if len(parts) > 2 else ""
            session_raw = parts[3] if len(parts) > 3 else ""
            sess_m = re.search(r"(\d+)", session_raw)
            resolved_session = int(sess_m.group(1)) if sess_m else None
            frontiers[fid] = {
                "id": fid,
                "status": "resolved",
                "resolved_session": resolved_session,
                "open_session": None,  # will try to infer
            }

    # Parse main FRONTIER.md for active frontiers
    if FRONTIER_FILE.exists():
        text = FRONTIER_FILE.read_text(errors="replace")
        for m in re.finditer(r"\*\*(F[-\w]+)\*\*.*?(?=\*\*F[-\w]+\*\*|\Z)", text, re.DOTALL):
            fid = m.group(1)
            block = m.group(0)
            # Find earliest session reference as open session
            sessions = [int(s) for s in re.findall(r"\bS(\d+)\b", block)]
            if fid not in frontiers:
                frontiers[fid] = {
                    "id": fid,
                    "status": "active",
                    "resolved_session": None,
                    "open_session": min(sessions) if sessions else None,
                }
            elif sessions:
                frontiers[fid]["open_session"] = min(sessions)
            # Update open session for resolved frontiers too
            if fid in frontiers and sessions:
                if frontiers[fid]["open_session"] is None:
                    frontiers[fid]["open_session"] = min(sessions)

    # Also scan domain frontier files for open sessions
    for domain_dir in DOMAIN_DIR.iterdir():
        frontier_file = domain_dir / "tasks" / "FRONTIER.md"
        if not frontier_file.exists():
            continue
        text = frontier_file.read_text(errors="replace")
        for m in re.finditer(r"\*\*(F[-\w]+)\*\*.*?(?=\*\*F[-\w]+\*\*|\Z)", text, re.DOTALL):
            fid = m.group(1)
            block = m.group(0)
            sessions = [int(s) for s in re.findall(r"\bS(\d+)\b", block)]
            if fid in frontiers and sessions:
                current_open = frontiers[fid].get("open_session")
                min_sess = min(sessions)
                if current_open is None or min_sess < current_open:
                    frontiers[fid]["open_session"] = min_sess

    # Heuristic: for numbered-only frontiers (F1-F99), open_session ≈ frontier number
    for fid, info in frontiers.items():
        if info["open_session"] is None:
            num_m = re.match(r"F(\d+)$", fid)
            if num_m:
                # Early frontiers: number roughly correlates with session
                info["open_session"] = int(num_m.group(1))

    # Compute latency and zone
    for fid, info in frontiers.items():
        if info["open_session"] and info["resolved_session"]:
            info["latency"] = info["resolved_session"] - info["open_session"]
        elif info["open_session"] and info["status"] == "active":
            info["latency"] = 374 - info["open_session"]  # current session
        else:
            info["latency"] = None

        if info["latency"] is not None:
            if info["latency"] <= 1:
                info["zone"] = "boredom"
            elif info["latency"] <= 10:
                info["zone"] = "flow"
            elif info["latency"] <= 15:
                info["zone"] = "stalled"
            else:
                info["zone"] = "anxiety"
        else:
            info["zone"] = "unknown"

    return frontiers


def link_lessons_to_frontiers(lessons, frontiers):
    """Link lessons to frontiers they reference."""
    frontier_lessons = defaultdict(set)
    for num, info in lessons.items():
        for fref in info["frontiers"]:
            # Normalize frontier reference
            normalized = fref
            if normalized in frontiers:
                frontier_lessons[normalized].add(num)
            # Try without hyphen
            no_hyphen = fref.replace("-", "")
            for fid in frontiers:
                if fid.replace("-", "") == no_hyphen:
                    frontier_lessons[fid].add(num)
    return frontier_lessons


def analyze_by_zone(frontiers, frontier_lessons, lessons):
    """Compute citation impact by frontier resolution zone."""
    zone_stats = defaultdict(lambda: {
        "frontiers": [],
        "lessons": set(),
        "in_degrees": [],
        "out_degrees": [],
    })

    for fid, info in frontiers.items():
        zone = info["zone"]
        if zone == "unknown":
            continue
        zone_stats[zone]["frontiers"].append(fid)
        linked = frontier_lessons.get(fid, set())
        zone_stats[zone]["lessons"].update(linked)
        for lnum in linked:
            if lnum in lessons:
                zone_stats[zone]["in_degrees"].append(lessons[lnum]["in_degree"])
                zone_stats[zone]["out_degrees"].append(len(lessons[lnum]["cites"]))

    results = {}
    for zone in ["boredom", "flow", "stalled", "anxiety"]:
        stats = zone_stats[zone]
        in_degs = stats["in_degrees"]
        results[zone] = {
            "n_frontiers": len(stats["frontiers"]),
            "n_lessons": len(stats["lessons"]),
            "n_citation_samples": len(in_degs),
            "mean_in_degree": round(statistics.mean(in_degs), 2) if in_degs else 0,
            "median_in_degree": round(statistics.median(in_degs), 2) if in_degs else 0,
            "mean_out_degree": round(statistics.mean(stats["out_degrees"]), 2) if stats["out_degrees"] else 0,
            "top_frontiers": stats["frontiers"][:5],
        }
    return results


def main():
    lessons = parse_all_lessons()
    print(f"Parsed {len(lessons)} lessons")

    frontiers = parse_frontier_resolution()
    print(f"Parsed {len(frontiers)} frontiers")

    # Zone distribution
    zone_counts = defaultdict(int)
    for info in frontiers.values():
        zone_counts[info["zone"]] += 1
    print(f"Zone distribution: {dict(zone_counts)}")

    frontier_lessons = link_lessons_to_frontiers(lessons, frontiers)
    linked_count = sum(1 for v in frontier_lessons.values() if v)
    print(f"Linked {linked_count} frontiers to lessons")

    zone_results = analyze_by_zone(frontiers, frontier_lessons, lessons)

    # Global baseline
    all_in_degrees = [info["in_degree"] for info in lessons.values()]
    global_mean = statistics.mean(all_in_degrees) if all_in_degrees else 0
    global_median = statistics.median(all_in_degrees) if all_in_degrees else 0

    # Compute lift vs baseline
    for zone, stats in zone_results.items():
        if global_mean > 0 and stats["mean_in_degree"] > 0:
            stats["lift_vs_global"] = round(stats["mean_in_degree"] / global_mean, 2)
        else:
            stats["lift_vs_global"] = None

    # Flow zone detail
    flow_frontiers = [fid for fid, info in frontiers.items() if info["zone"] == "flow"]
    flow_detail = []
    for fid in flow_frontiers:
        info = frontiers[fid]
        linked = frontier_lessons.get(fid, set())
        linked_in_degrees = [lessons[l]["in_degree"] for l in linked if l in lessons]
        flow_detail.append({
            "frontier": fid,
            "latency": info["latency"],
            "status": info["status"],
            "open_session": info["open_session"],
            "resolved_session": info["resolved_session"],
            "n_lessons": len(linked),
            "lessons": sorted(linked),
            "mean_in_degree": round(statistics.mean(linked_in_degrees), 2) if linked_in_degrees else 0,
        })

    # Anxiety zone detail (long-running frontiers)
    anxiety_frontiers = [fid for fid, info in frontiers.items() if info["zone"] == "anxiety"]
    anxiety_detail = []
    for fid in sorted(anxiety_frontiers, key=lambda f: frontiers[f].get("latency", 0) or 0, reverse=True)[:10]:
        info = frontiers[fid]
        linked = frontier_lessons.get(fid, set())
        linked_in_degrees = [lessons[l]["in_degree"] for l in linked if l in lessons]
        anxiety_detail.append({
            "frontier": fid,
            "latency": info["latency"],
            "status": info["status"],
            "n_lessons": len(linked),
            "mean_in_degree": round(statistics.mean(linked_in_degrees), 2) if linked_in_degrees else 0,
        })

    result = {
        "experiment": "F-GAME3 flow-zone citation impact",
        "session": "S374",
        "date": "2026-03-01",
        "method": "Parse frontier resolution latency, link frontiers to lessons via text references, measure in-degree (citations received) by resolution zone",
        "n_lessons": len(lessons),
        "n_frontiers": len(frontiers),
        "n_linked_frontiers": linked_count,
        "global_baseline": {
            "mean_in_degree": round(global_mean, 2),
            "median_in_degree": round(global_median, 2),
        },
        "zone_results": zone_results,
        "zone_distribution": dict(zone_counts),
        "flow_zone_detail": flow_detail,
        "anxiety_zone_top10": anxiety_detail,
        "prediction_check": {
            "expect": "Flow-zone >1.5x average citation rate",
            "actual": "",
        },
    }

    # Print summary
    print(f"\n=== RESULTS ===")
    print(f"Global baseline: mean in-degree = {global_mean:.2f}, median = {global_median:.2f}")
    print()
    for zone in ["boredom", "flow", "stalled", "anxiety"]:
        z = zone_results[zone]
        print(f"  {zone:10s}: {z['n_frontiers']:3d} frontiers, {z['n_lessons']:3d} lessons, "
              f"mean_in={z['mean_in_degree']:.2f}, lift={z.get('lift_vs_global', 'N/A')}x")
    print(f"\nFlow zone detail:")
    for fd in flow_detail:
        print(f"  {fd['frontier']:10s}: latency={fd['latency']}, {fd['n_lessons']}L, "
              f"mean_in={fd['mean_in_degree']:.2f}")
    print(f"\nAnxiety zone top-10:")
    for ad in anxiety_detail:
        print(f"  {ad['frontier']:10s}: latency={ad['latency']}, {ad['n_lessons']}L, "
              f"mean_in={ad['mean_in_degree']:.2f}")

    # Update actual result
    flow_z = zone_results.get("flow", {})
    result["prediction_check"]["actual"] = (
        f"Flow zone: {flow_z.get('mean_in_degree', 0):.2f} mean in-degree, "
        f"lift = {flow_z.get('lift_vs_global', 'N/A')}x vs global"
    )

    # Save
    out = ROOT / "experiments" / "gaming" / "f-game3-citation-impact-s374.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    # Convert sets for JSON
    for fd in result["flow_zone_detail"]:
        fd["lessons"] = sorted(fd["lessons"])
    for zone_data in result["zone_results"].values():
        zone_data.pop("in_degrees", None)
        zone_data.pop("out_degrees", None)
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved: {out}")

    return result


if __name__ == "__main__":
    result = main()
