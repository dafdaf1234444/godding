#!/usr/bin/env python3
"""F-STR1 Hardening: Dispatch quality measurement post-S384 EAD fix.

Parses SWARM-LANES.md and SWARM-LANES-ARCHIVE.md to compare dispatch quality
metrics between control (pre-S384) and treatment (S384+) groups.

Metrics:
  - EAD compliance rate (expect=, actual=, diff= all non-empty and non-TBD)
  - Merge rate (MERGED / (MERGED + ABANDONED), excluding ACTIVE)
  - Domain diversity (unique domains)
  - Frontier resolution rate (distinct frontiers resolved in treatment)
  - Session-gap analysis (same-session close vs cross-session)

Output: experiments/strategy/f-str1-hardening-s392.json
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
LANES_FILE = REPO / "tasks" / "SWARM-LANES.md"
ARCHIVE_FILE = REPO / "tasks" / "SWARM-LANES-ARCHIVE.md"
OUTPUT_FILE = REPO / "experiments" / "strategy" / "f-str1-hardening-s392.json"
CUTOFF_SESSION = 384  # S384 is the EAD fix session


def extract_session_number(session_str: str) -> int | None:
    """Extract numeric session from strings like 'S384', '384', 'S378'."""
    session_str = session_str.strip()
    m = re.match(r"S?(\d+)", session_str, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def extract_domain_from_lane_id(lane_id: str) -> str:
    """Extract domain abbreviation from lane ID like DOMEX-META-S386."""
    lane_id = lane_id.strip()
    # Pattern: DOMEX-<DOMAIN>-<rest> or DOMEX-<DOMAIN><N>-<rest>
    m = re.match(r"DOMEX-([A-Z]+)\d*-", lane_id)
    if m:
        return m.group(1).lower()
    # Fallback: try L-S<N>-<something>
    m = re.match(r"L-S\d+-(.+)", lane_id)
    if m:
        return m.group(1).lower().split("-")[0]
    # Other patterns
    m = re.match(r"([A-Z]+-[A-Z]+)", lane_id)
    if m:
        return m.group(1).lower()
    return lane_id.lower().split("-")[0]


def parse_etc_field(etc: str) -> dict:
    """Parse Etc column: semicolon-delimited key=value pairs."""
    result = {}
    if not etc:
        return result
    # Split on semicolons and commas that separate key=value pairs
    # The Etc field uses ; primarily, but some entries use , for repeated keys
    parts = re.split(r"[;,]\s*", etc)
    for part in parts:
        part = part.strip()
        if "=" in part:
            key, _, val = part.partition("=")
            key = key.strip()
            val = val.strip()
            # Only store the first occurrence of each key (avoid progress=closed overwriting)
            if key not in result:
                result[key] = val
    return result


def has_ead_compliance(etc_dict: dict) -> bool:
    """Check if lane has full EAD compliance (expect, actual, diff all filled and non-TBD)."""
    for field in ("expect", "actual", "diff"):
        val = etc_dict.get(field, "").strip()
        if not val or val.upper() == "TBD":
            return False
    return True


def extract_frontier(etc_dict: dict) -> str | None:
    """Extract frontier ID from Etc field."""
    frontier = etc_dict.get("frontier", "").strip()
    if frontier:
        return frontier
    return None


def extract_mode(etc_dict: dict) -> str | None:
    """Extract mode from Etc field."""
    mode = etc_dict.get("mode", "").strip()
    if mode:
        return mode
    return None


def parse_lane_row(line: str) -> dict | None:
    """Parse a single pipe-delimited lane row.

    Expected columns (from SWARM-LANES.md header):
    Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes

    But some rows in the archive have slightly different column layouts.
    We identify columns by position and use the Status column (second-to-last)
    and Etc column (third-from-last).
    """
    line = line.strip()
    if not line.startswith("|"):
        return None
    # Split on pipes
    parts = [p.strip() for p in line.split("|")]
    # Remove empty first/last elements from leading/trailing pipes
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]

    if len(parts) < 11:
        return None

    # Skip header/separator rows
    if parts[0].startswith("---") or parts[0] == "Date":
        return None

    # Column mapping (0-indexed):
    # 0=Date, 1=Lane, 2=Session, 3=Agent, 4=Branch, 5=PR,
    # 6=Model, 7=Platform, 8=Scope-Key, 9=Etc, 10=Status, 11=Notes
    date_str = parts[0]
    lane_id = parts[1]
    session_str = parts[2]
    etc_str = parts[9] if len(parts) > 9 else ""
    status = parts[10].strip().upper() if len(parts) > 10 else ""
    notes = parts[11] if len(parts) > 11 else ""

    session_num = extract_session_number(session_str)
    if session_num is None:
        return None

    # Only accept known statuses
    if status not in ("MERGED", "ABANDONED", "ACTIVE", "CLAIMED", "BLOCKED", "READY"):
        return None

    etc_dict = parse_etc_field(etc_str)
    domain = extract_domain_from_lane_id(lane_id)
    frontier = extract_frontier(etc_dict)
    mode = extract_mode(etc_dict)
    ead_compliant = has_ead_compliance(etc_dict)

    return {
        "date": date_str,
        "lane_id": lane_id,
        "session": session_num,
        "status": status,
        "domain": domain,
        "ead_compliant": ead_compliant,
        "frontier": frontier,
        "mode": mode,
        "etc": etc_dict,
        "notes": notes,
    }


def parse_lanes_file(filepath: Path) -> list[dict]:
    """Parse all lane rows from a file."""
    if not filepath.exists():
        print(f"  [WARN] File not found: {filepath}", file=sys.stderr)
        return []
    lanes = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            row = parse_lane_row(line)
            if row:
                lanes.append(row)
    return lanes


def deduplicate_lanes(lanes: list[dict]) -> list[dict]:
    """Keep only the last row per lane_id (append-only log — last row is final state)."""
    seen = {}
    for lane in lanes:
        lid = lane["lane_id"]
        # Keep the row with the highest session number (latest update)
        if lid not in seen or lane["session"] >= seen[lid]["session"]:
            seen[lid] = lane
    return list(seen.values())


def compute_metrics(lanes: list[dict], label: str) -> dict:
    """Compute all metrics for a group of lanes."""
    if not lanes:
        return {
            "label": label,
            "total_lanes": 0,
            "merged": 0,
            "abandoned": 0,
            "active": 0,
            "merge_rate": None,
            "ead_compliant_count": 0,
            "ead_compliance_rate": None,
            "unique_domains": 0,
            "domex_lanes": 0,
            "domex_unique_domains": 0,
            "domain_list": [],
            "domain_distribution": {},
            "frontier_count": 0,
            "frontier_list": [],
            "mode_distribution": {},
            "same_session_close_pct": None,
            "cross_session_close_pct": None,
        }

    total = len(lanes)
    merged = sum(1 for l in lanes if l["status"] == "MERGED")
    abandoned = sum(1 for l in lanes if l["status"] == "ABANDONED")
    active = sum(1 for l in lanes if l["status"] in ("ACTIVE", "CLAIMED", "BLOCKED", "READY"))

    closed = merged + abandoned
    merge_rate = merged / closed if closed > 0 else None

    ead_count = sum(1 for l in lanes if l["ead_compliant"])
    ead_rate = ead_count / total if total > 0 else None

    domains = [l["domain"] for l in lanes]
    domain_counter = Counter(domains)
    unique_domains = len(domain_counter)

    # DOMEX-specific domain diversity (only lanes with DOMEX- prefix)
    domex_lanes = [l for l in lanes if l["lane_id"].startswith("DOMEX-")]
    domex_domains = [l["domain"] for l in domex_lanes]
    domex_domain_counter = Counter(domex_domains)
    domex_unique_domains = len(domex_domain_counter)

    frontiers = set()
    for l in lanes:
        if l["frontier"]:
            # Split on / for multi-frontier lanes like F-LNG1/F-LNG2
            for f in l["frontier"].split("/"):
                frontiers.add(f.strip())

    modes = [l["mode"] for l in lanes if l["mode"]]
    mode_counter = Counter(modes)

    # Session-gap analysis: for closed lanes, check if the opening session
    # matches the closing session (same lane_id may appear multiple times;
    # we use the session field of the final row as closing session)
    # The opening session is embedded in the lane_id (e.g., DOMEX-META-S386 opened in S386)
    same_session = 0
    cross_session = 0
    for l in lanes:
        if l["status"] not in ("MERGED", "ABANDONED"):
            continue
        # Extract opening session from lane_id
        m = re.search(r"S(\d+)", l["lane_id"])
        if m:
            open_session = int(m.group(1))
            close_session = l["session"]
            if open_session == close_session:
                same_session += 1
            else:
                cross_session += 1

    total_closures = same_session + cross_session
    same_pct = (same_session / total_closures * 100) if total_closures > 0 else None
    cross_pct = (cross_session / total_closures * 100) if total_closures > 0 else None

    return {
        "label": label,
        "total_lanes": total,
        "merged": merged,
        "abandoned": abandoned,
        "active": active,
        "merge_rate": round(merge_rate * 100, 1) if merge_rate is not None else None,
        "ead_compliant_count": ead_count,
        "ead_compliance_rate": round(ead_rate * 100, 1) if ead_rate is not None else None,
        "unique_domains": unique_domains,
        "domex_lanes": len(domex_lanes),
        "domex_unique_domains": domex_unique_domains,
        "domex_domain_distribution": dict(domex_domain_counter.most_common()),
        "domain_list": sorted(domain_counter.keys()),
        "domain_distribution": dict(domain_counter.most_common()),
        "frontier_count": len(frontiers),
        "frontier_list": sorted(frontiers),
        "mode_distribution": dict(mode_counter.most_common()),
        "same_session_close_count": same_session,
        "cross_session_close_count": cross_session,
        "same_session_close_pct": round(same_pct, 1) if same_pct is not None else None,
        "cross_session_close_pct": round(cross_pct, 1) if cross_pct is not None else None,
    }


def count_resolved_frontiers(treatment_lanes: list[dict]) -> dict:
    """Count frontiers that went from ACTIVE to RESOLVED in the treatment period.

    We look at lane notes for resolution indicators like 'RESOLVED', 'CONFIRMED',
    'FALSIFIED' (all are forms of frontier closure).
    """
    frontier_resolutions = defaultdict(list)
    for l in treatment_lanes:
        if l["status"] != "MERGED":
            continue
        if not l["frontier"]:
            continue
        notes = l["notes"].upper()
        for indicator in ("RESOLVED", "CONFIRMED", "FALSIFIED", "ADVANCED", "PARTIALLY CONFIRMED"):
            if indicator in notes:
                for f in l["frontier"].split("/"):
                    frontier_resolutions[f.strip()].append({
                        "lane": l["lane_id"],
                        "session": l["session"],
                        "indicator": indicator,
                    })
                break

    # Count distinct frontiers with at least one resolution event
    resolved_frontiers = {f: events for f, events in frontier_resolutions.items()
                          if any(e["indicator"] == "RESOLVED" for e in events)}
    advanced_frontiers = {f: events for f, events in frontier_resolutions.items()
                          if any(e["indicator"] in ("ADVANCED", "CONFIRMED", "PARTIALLY CONFIRMED", "FALSIFIED")
                                 for e in events)}

    return {
        "resolved_count": len(resolved_frontiers),
        "resolved_frontiers": sorted(resolved_frontiers.keys()),
        "advanced_count": len(advanced_frontiers),
        "advanced_frontiers": sorted(advanced_frontiers.keys()),
        "total_distinct_frontiers_with_progress": len(frontier_resolutions),
    }


def main():
    print("=" * 60)
    print("F-STR1 Hardening: Dispatch Quality Post-S384 EAD Fix")
    print("=" * 60)

    # Parse both files
    print(f"\nParsing {LANES_FILE.name}...")
    lanes_main = parse_lanes_file(LANES_FILE)
    print(f"  Found {len(lanes_main)} raw rows")

    print(f"Parsing {ARCHIVE_FILE.name}...")
    lanes_archive = parse_lanes_file(ARCHIVE_FILE)
    print(f"  Found {len(lanes_archive)} raw rows")

    # Combine and deduplicate
    all_lanes = lanes_archive + lanes_main  # archive first, main second (main overwrites)
    print(f"\nTotal raw rows: {len(all_lanes)}")

    deduped = deduplicate_lanes(all_lanes)
    print(f"Deduplicated lanes (unique lane IDs): {len(deduped)}")

    # Split into control and treatment groups
    control = [l for l in deduped if l["session"] < CUTOFF_SESSION]
    treatment = [l for l in deduped if l["session"] >= CUTOFF_SESSION]

    print(f"\nControl (pre-S{CUTOFF_SESSION}): {len(control)} lanes")
    print(f"Treatment (S{CUTOFF_SESSION}+): {len(treatment)} lanes")

    # Compute metrics
    control_metrics = compute_metrics(control, f"control_pre_S{CUTOFF_SESSION}")
    treatment_metrics = compute_metrics(treatment, f"treatment_S{CUTOFF_SESSION}_plus")

    # Frontier resolution in treatment period
    frontier_resolution = count_resolved_frontiers(treatment)

    # Compute deltas
    deltas = {}
    for key in ("merge_rate", "ead_compliance_rate", "unique_domains",
                 "domex_unique_domains", "same_session_close_pct"):
        c = control_metrics.get(key)
        t = treatment_metrics.get(key)
        if c is not None and t is not None:
            deltas[key] = round(t - c, 1)
        else:
            deltas[key] = None

    # Per-session lane counts for treatment period
    session_lane_counts = Counter()
    for l in treatment:
        session_lane_counts[l["session"]] += 1
    sessions_in_treatment = sorted(session_lane_counts.keys())

    # EAD compliance trajectory in treatment
    ead_by_session = {}
    for s in sessions_in_treatment:
        s_lanes = [l for l in treatment if l["session"] == s]
        ead_count = sum(1 for l in s_lanes if l["ead_compliant"])
        total = len(s_lanes)
        ead_by_session[str(s)] = {
            "ead_count": ead_count,
            "total": total,
            "rate": round(ead_count / total * 100, 1) if total > 0 else None,
        }

    # Verdict
    ead_target = 90.0
    merge_target = 75.0
    diversity_target = 15

    ead_pass = (treatment_metrics["ead_compliance_rate"] is not None
                and treatment_metrics["ead_compliance_rate"] >= ead_target)
    merge_pass = (treatment_metrics["merge_rate"] is not None
                  and treatment_metrics["merge_rate"] >= merge_target)
    diversity_pass = treatment_metrics["domex_unique_domains"] >= diversity_target

    passes = sum([ead_pass, merge_pass, diversity_pass])
    if passes == 3:
        verdict = "STRONG"
    elif passes >= 2:
        verdict = "MODERATE"
    elif passes >= 1:
        verdict = "WEAK"
    else:
        verdict = "FAIL"

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print(f"\n{'Metric':<35} {'Control':>12} {'Treatment':>12} {'Delta':>10}")
    print("-" * 70)
    print(f"{'Total lanes':<35} {control_metrics['total_lanes']:>12} {treatment_metrics['total_lanes']:>12}")
    print(f"{'MERGED':<35} {control_metrics['merged']:>12} {treatment_metrics['merged']:>12}")
    print(f"{'ABANDONED':<35} {control_metrics['abandoned']:>12} {treatment_metrics['abandoned']:>12}")
    print(f"{'ACTIVE':<35} {control_metrics['active']:>12} {treatment_metrics['active']:>12}")

    cr = control_metrics['merge_rate']
    tr = treatment_metrics['merge_rate']
    d = deltas['merge_rate']
    print(f"{'Merge rate (%)':<35} {cr if cr is not None else 'N/A':>12} {tr if tr is not None else 'N/A':>12} {d if d is not None else 'N/A':>10}")

    cr = control_metrics['ead_compliance_rate']
    tr = treatment_metrics['ead_compliance_rate']
    d = deltas['ead_compliance_rate']
    print(f"{'EAD compliance (%)':<35} {cr if cr is not None else 'N/A':>12} {tr if tr is not None else 'N/A':>12} {d if d is not None else 'N/A':>10}")

    cr = control_metrics['domex_unique_domains']
    tr = treatment_metrics['domex_unique_domains']
    d = tr - cr if cr is not None and tr is not None else None
    print(f"{'DOMEX unique domains':<35} {cr:>12} {tr:>12} {d if d is not None else 'N/A':>10}")
    print(f"{'DOMEX lanes':<35} {control_metrics['domex_lanes']:>12} {treatment_metrics['domex_lanes']:>12}")

    cr = control_metrics['same_session_close_pct']
    tr = treatment_metrics['same_session_close_pct']
    d = deltas['same_session_close_pct']
    print(f"{'Same-session close (%)':<35} {cr if cr is not None else 'N/A':>12} {tr if tr is not None else 'N/A':>12} {d if d is not None else 'N/A':>10}")

    print(f"\nFrontier resolution (treatment):")
    print(f"  Resolved: {frontier_resolution['resolved_count']} ({', '.join(frontier_resolution['resolved_frontiers'][:10])})")
    print(f"  Advanced: {frontier_resolution['advanced_count']}")
    print(f"  Total with progress: {frontier_resolution['total_distinct_frontiers_with_progress']}")

    print(f"\n{'Criterion':<35} {'Target':>12} {'Actual':>12} {'Pass':>8}")
    print("-" * 70)
    print(f"{'EAD compliance':<35} {'>=' + str(ead_target) + '%':>12} {str(treatment_metrics['ead_compliance_rate']) + '%' if treatment_metrics['ead_compliance_rate'] is not None else 'N/A':>12} {'YES' if ead_pass else 'NO':>8}")
    print(f"{'Merge rate':<35} {'>=' + str(merge_target) + '%':>12} {str(treatment_metrics['merge_rate']) + '%' if treatment_metrics['merge_rate'] is not None else 'N/A':>12} {'YES' if merge_pass else 'NO':>8}")
    print(f"{'DOMEX domain diversity':<35} {'>=' + str(diversity_target):>12} {treatment_metrics['domex_unique_domains']:>12} {'YES' if diversity_pass else 'NO':>8}")

    print(f"\nVERDICT: {verdict} ({passes}/3 criteria pass)")

    # Build output
    result = {
        "experiment": "f-str1-hardening-s392",
        "description": "Dispatch quality measurement post-S384 EAD fix",
        "cutoff_session": CUTOFF_SESSION,
        "source_files": [
            str(LANES_FILE.relative_to(REPO)),
            str(ARCHIVE_FILE.relative_to(REPO)),
        ],
        "total_raw_rows": len(all_lanes),
        "total_deduplicated_lanes": len(deduped),
        "control": control_metrics,
        "treatment": treatment_metrics,
        "deltas": deltas,
        "frontier_resolution": frontier_resolution,
        "ead_by_session_treatment": ead_by_session,
        "session_lane_counts_treatment": {str(k): v for k, v in sorted(session_lane_counts.items())},
        "targets": {
            "ead_compliance_pct": ead_target,
            "merge_rate_pct": merge_target,
            "domain_diversity_min": diversity_target,
        },
        "criteria_pass": {
            "ead_compliance": ead_pass,
            "merge_rate": merge_pass,
            "domain_diversity": diversity_pass,
        },
        "verdict": verdict,
        "verdict_passes": f"{passes}/3",
    }

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\nOutput written to: {OUTPUT_FILE.relative_to(REPO)}")
    return result


if __name__ == "__main__":
    main()
