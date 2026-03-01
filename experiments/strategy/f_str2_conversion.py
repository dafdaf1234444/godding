#!/usr/bin/env python3
"""F-STR2 measurement: plan-to-execution conversion rate.

Parses SWARM-LANES.md and SWARM-LANES-ARCHIVE.md for ALL lane rows.
Measures:
  1. Overall conversion rate (MERGED vs ABANDONED)
  2. Session gap -> abandonment correlation
  3. EAD compliance -> merge correlation
  4. Era analysis (pre-S384 vs post-S384)
  5. Mode tracking (mode diversity -> resolution)
  6. Staleness (same-session vs cross-session)
  7. Domain productivity
  8. Wave-aware conversion (frontier wave count -> resolution)

Output: experiments/strategy/f-str2-conversion-s391.json
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
LANES_ACTIVE = REPO / "tasks" / "SWARM-LANES.md"
LANES_ARCHIVE = REPO / "tasks" / "SWARM-LANES-ARCHIVE.md"
OUTPUT = REPO / "experiments" / "strategy" / "f-str2-conversion-s391.json"

# S384 is the close_lane.py fix session
ERA_BOUNDARY = 384


def parse_session_number(session_str: str) -> int | None:
    """Extract numeric session from strings like 'S384', '384', 'S384a'."""
    m = re.search(r"S?(\d+)", str(session_str).strip())
    if m:
        return int(m.group(1))
    return None


# Known domain codes mapped from directory names to short codes used in lanes
KNOWN_DOMAINS = {
    "ai": "AI", "brain": "BRN", "catastrophic-risks": "CAT",
    "conflict": "CON", "control-theory": "CTL", "cryptocurrency": "CRY",
    "cryptography": "CRYPTO", "distributed-systems": "DS",
    "dream": "DREAM", "economy": "ECO", "empathy": "EMP",
    "evaluation": "EVAL", "evolution": "EVO", "expert-swarm": "EXP",
    "farming": "FARM", "finance": "FIN", "fluid-dynamics": "FLD",
    "fractals": "FRA", "game-theory": "GT", "gaming": "GAM",
    "governance": "GOV", "graph-theory": "GTH", "guesstimates": "GUE",
    "health": "HLT", "helper-swarm": "HLP", "history": "HIS",
    "human-systems": "HS", "information-science": "IS",
    "linguistics": "LNG", "meta": "META", "nk-complexity": "NK",
    "operations-research": "OPS", "physics": "PHY",
    "protocol-engineering": "PRO", "psychology": "PSY",
    "quality": "QC", "security": "SEC", "social-media": "SOC",
    "statistics": "STAT", "stochastic-processes": "SP",
    "strategy": "STR",
}

# Reverse map: short code -> canonical domain name
DOMAIN_CODE_TO_NAME = {v: k for k, v in KNOWN_DOMAINS.items()}

# Also accept lane codes that directly match known short codes
VALID_DOMAIN_CODES = set(KNOWN_DOMAINS.values())

# Additional codes commonly used in lane IDs that map to known domains
LANE_CODE_ALIASES = {
    "FFIN": "FIN", "FAI": "AI", "FCTL": "CTL", "FIS": "IS",
    "FLNG": "LNG", "FEVO": "EVO", "FOPS": "OPS", "FLD": "FLD",
    "FBRN": "BRN", "FGAM": "GAM", "FSTAT": "STAT", "FGT": "GT",
    "FSEC": "SEC", "FECO": "ECO", "FPHY": "PHY", "FHLP": "HLP",
    "FQCJ": "QC", "FQC": "QC", "FSTR": "STR", "FSP": "SP",
    "FMETA": "META", "FNK": "NK", "FGOV": "GOV", "FCAT": "CAT",
    "FPSY": "PSY", "FDREAM": "DREAM", "FHIS": "HIS",
    "FCON": "CON", "FCRY": "CRY", "FEXP": "EXP",
    "FEVAL": "EVAL", "FEMP": "EMP", "FDS": "DS",
    "FGUE": "GUE", "FGTH": "GTH", "FHLT": "HLT",
    "FPRO": "PRO", "FFRA": "FRA", "FFARM": "FARM",
    "FSOC": "SOC", "FHS": "HS",
    # Also plain domain codes without F prefix
    "FIN": "FIN", "CTL": "CTL",
}


def extract_domain_from_lane(lane_id: str) -> str | None:
    """Extract domain code from lane ID like 'DOMEX-META-S322' -> 'META'."""
    # Pattern 1: DOMEX-<DOMAIN>-<rest> (most reliable)
    m = re.match(r"DOMEX-([A-Z]+)\d*-", lane_id)
    if m:
        code = m.group(1)
        if code in VALID_DOMAIN_CODES:
            return code
        # Check aliases
        if code in LANE_CODE_ALIASES:
            return LANE_CODE_ALIASES[code]

    # Pattern 2: L-S<N>-F<DOMAIN><N>-... (frontier-prefixed, e.g., L-S186-FFIN1-...)
    m = re.match(r"L-S\d+-F([A-Z]+)\d*-", lane_id)
    if m:
        code = m.group(1)
        fcode = "F" + code
        if code in VALID_DOMAIN_CODES:
            return code
        if fcode in LANE_CODE_ALIASES:
            return LANE_CODE_ALIASES[fcode]
        if code in LANE_CODE_ALIASES:
            return LANE_CODE_ALIASES[code]

    return None


def extract_domain_from_etc(etc_str: str) -> str | None:
    """Extract domain from focus= field in Etc, e.g. 'focus=domains/meta' -> 'META'."""
    m = re.search(r"focus=domains/([a-z\-]+)", etc_str)
    if m:
        domain_name = m.group(1)
        if domain_name in KNOWN_DOMAINS:
            return KNOWN_DOMAINS[domain_name]
    return None


def extract_frontier_from_etc(etc_str: str) -> str | None:
    """Extract frontier ID from Etc field, e.g. 'frontier=F-META1' -> 'F-META1'."""
    m = re.search(r"frontier=(F-[A-Z]+\d+(?:/F-[A-Z]+\d+)*)", etc_str)
    if m:
        return m.group(1).split("/")[0]  # Take first if multiple
    return None


def extract_frontier_from_lane(lane_id: str) -> str | None:
    """Fallback: extract a rough frontier from the lane ID."""
    domain = extract_domain_from_lane(lane_id)
    if domain:
        return f"F-{domain}"
    return None


def extract_mode_from_etc(etc_str: str) -> str | None:
    """Extract mode= from Etc field."""
    m = re.search(r"mode=([^;,\s]+)", etc_str)
    if m:
        return m.group(1)
    return None


def has_ead_compliance(etc_str: str) -> bool:
    """Check if actual= and diff= are present and non-TBD in Etc."""
    has_actual = bool(re.search(r"actual=[^;,\s]", etc_str)) and "actual=TBD" not in etc_str
    has_diff = bool(re.search(r"diff=[^;,\s]", etc_str)) and "diff=TBD" not in etc_str
    return has_actual and has_diff


def parse_lane_rows(filepath: Path) -> list[dict]:
    """Parse markdown table rows from a SWARM-LANES file."""
    rows = []
    if not filepath.exists():
        return rows

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        # Must start and end with | and have at least 12 fields
        if not line.startswith("|") or not line.endswith("|"):
            continue
        # Skip header/separator rows
        if "---" in line and line.count("---") >= 3:
            continue
        if "Date" in line and "Lane" in line and "Session" in line:
            continue

        parts = [p.strip() for p in line.split("|")]
        # Split produces empty strings at start/end due to leading/trailing |
        parts = parts[1:-1]  # Remove leading/trailing empty

        if len(parts) < 12:
            continue

        date, lane, session, agent, branch, pr, model, platform, scope_key, etc, status, notes = (
            parts[0], parts[1], parts[2], parts[3], parts[4], parts[5],
            parts[6], parts[7], parts[8], parts[9], parts[10],
            parts[11] if len(parts) > 11 else ""
        )

        # Skip empty/blank rows
        if not lane.strip() or lane.strip() == "-":
            continue

        session_num = parse_session_number(session)

        rows.append({
            "date": date,
            "lane": lane,
            "session": session,
            "session_num": session_num,
            "agent": agent,
            "branch": branch,
            "pr": pr,
            "model": model,
            "platform": platform,
            "scope_key": scope_key,
            "etc": etc,
            "status": status.strip().upper(),
            "notes": notes,
        })

    return rows


def deduplicate_lanes(rows: list[dict]) -> dict[str, dict]:
    """
    Group rows by lane ID. For each lane, keep track of all rows
    and use the LAST row's status as the definitive status.
    """
    lane_groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        lane_groups[row["lane"]].append(row)

    lanes = {}
    for lane_id, group in lane_groups.items():
        # Sort by session number then by order of appearance (already in order)
        last_row = group[-1]
        first_row = group[0]

        # Extract session numbers
        open_session = first_row["session_num"]
        last_session = last_row["session_num"]

        # Compute gap
        gap = None
        if open_session is not None and last_session is not None:
            gap = abs(last_session - open_session)

        # Check EAD across ALL rows for this lane
        ead_compliant = any(has_ead_compliance(r["etc"]) for r in group)

        # Extract frontier
        frontier = None
        for r in group:
            frontier = extract_frontier_from_etc(r["etc"])
            if frontier:
                break
        if not frontier:
            frontier = extract_frontier_from_lane(lane_id)

        # Extract mode(s)
        modes = set()
        for r in group:
            m = extract_mode_from_etc(r["etc"])
            if m:
                modes.add(m)

        # Extract domain: try lane ID first, then Etc focus= field
        domain = extract_domain_from_lane(lane_id)
        if not domain:
            for r in group:
                domain = extract_domain_from_etc(r["etc"])
                if domain:
                    break

        lanes[lane_id] = {
            "lane_id": lane_id,
            "status": last_row["status"],
            "open_session": open_session,
            "last_session": last_session,
            "gap": gap,
            "ead_compliant": ead_compliant,
            "frontier": frontier,
            "domain": domain,
            "modes": list(modes),
            "row_count": len(group),
            "first_row": first_row,
            "last_row": last_row,
            "all_rows": group,
        }

    return lanes


def measure_overall_conversion(lanes: dict) -> dict:
    """1. Overall conversion rate."""
    total = len(lanes)
    merged = sum(1 for l in lanes.values() if l["status"] == "MERGED")
    abandoned = sum(1 for l in lanes.values() if l["status"] == "ABANDONED")
    active = sum(1 for l in lanes.values() if l["status"] in ("ACTIVE", "CLAIMED", "BLOCKED", "READY"))
    other = total - merged - abandoned - active

    # Conversion rate = merged / (merged + abandoned) for closed lanes only
    closed = merged + abandoned
    rate = (merged / closed * 100) if closed > 0 else 0

    return {
        "total_lanes": total,
        "merged": merged,
        "abandoned": abandoned,
        "active": active,
        "other": other,
        "closed_total": closed,
        "conversion_rate_pct": round(rate, 1),
    }


def measure_session_gap_abandonment(lanes: dict) -> dict:
    """2. Session gap -> abandonment correlation."""
    buckets = {"gap_0": {"total": 0, "abandoned": 0},
               "gap_1": {"total": 0, "abandoned": 0},
               "gap_gt1": {"total": 0, "abandoned": 0}}

    for l in lanes.values():
        if l["status"] not in ("MERGED", "ABANDONED"):
            continue
        gap = l["gap"]
        if gap is None:
            continue

        if gap == 0:
            bucket = "gap_0"
        elif gap == 1:
            bucket = "gap_1"
        else:
            bucket = "gap_gt1"

        buckets[bucket]["total"] += 1
        if l["status"] == "ABANDONED":
            buckets[bucket]["abandoned"] += 1

    result = {}
    for key, data in buckets.items():
        rate = (data["abandoned"] / data["total"] * 100) if data["total"] > 0 else 0
        result[key] = {
            "total": data["total"],
            "abandoned": data["abandoned"],
            "abandon_rate_pct": round(rate, 1),
        }

    return result


def measure_ead_compliance(lanes: dict) -> dict:
    """3. EAD compliance -> merge correlation."""
    with_ead = {"total": 0, "merged": 0}
    without_ead = {"total": 0, "merged": 0}

    for l in lanes.values():
        if l["status"] not in ("MERGED", "ABANDONED"):
            continue

        if l["ead_compliant"]:
            with_ead["total"] += 1
            if l["status"] == "MERGED":
                with_ead["merged"] += 1
        else:
            without_ead["total"] += 1
            if l["status"] == "MERGED":
                without_ead["merged"] += 1

    ead_rate = (with_ead["merged"] / with_ead["total"] * 100) if with_ead["total"] > 0 else 0
    no_ead_rate = (without_ead["merged"] / without_ead["total"] * 100) if without_ead["total"] > 0 else 0

    # Simple significance: difference and sample sizes
    diff = ead_rate - no_ead_rate

    return {
        "with_ead": {
            "total": with_ead["total"],
            "merged": with_ead["merged"],
            "merge_rate_pct": round(ead_rate, 1),
        },
        "without_ead": {
            "total": without_ead["total"],
            "merged": without_ead["merged"],
            "merge_rate_pct": round(no_ead_rate, 1),
        },
        "difference_pp": round(diff, 1),
        "significance": "large" if abs(diff) > 20 else "moderate" if abs(diff) > 10 else "small",
    }


def measure_era_comparison(lanes: dict) -> dict:
    """4. Era analysis: pre-S384 vs post-S384."""
    pre = {"total": 0, "merged": 0, "abandoned": 0}
    post = {"total": 0, "merged": 0, "abandoned": 0}

    for l in lanes.values():
        if l["status"] not in ("MERGED", "ABANDONED"):
            continue
        session = l["open_session"]
        if session is None:
            continue

        era = pre if session < ERA_BOUNDARY else post
        era["total"] += 1
        if l["status"] == "MERGED":
            era["merged"] += 1
        elif l["status"] == "ABANDONED":
            era["abandoned"] += 1

    pre_rate = (pre["merged"] / pre["total"] * 100) if pre["total"] > 0 else 0
    post_rate = (post["merged"] / post["total"] * 100) if post["total"] > 0 else 0

    return {
        "pre_s384": {
            "total": pre["total"],
            "merged": pre["merged"],
            "abandoned": pre["abandoned"],
            "conversion_rate_pct": round(pre_rate, 1),
        },
        "post_s384": {
            "total": post["total"],
            "merged": post["merged"],
            "abandoned": post["abandoned"],
            "conversion_rate_pct": round(post_rate, 1),
        },
        "delta_pp": round(post_rate - pre_rate, 1),
    }


def measure_staleness(lanes: dict) -> dict:
    """6. Staleness: opened and last-updated in same session = fresh."""
    fresh = {"total": 0, "abandoned": 0}
    stale = {"total": 0, "abandoned": 0}

    for l in lanes.values():
        if l["status"] not in ("MERGED", "ABANDONED"):
            continue

        gap = l["gap"]
        if gap is None:
            continue

        bucket = fresh if gap == 0 else stale
        bucket["total"] += 1
        if l["status"] == "ABANDONED":
            bucket["abandoned"] += 1

    fresh_abandon = (fresh["abandoned"] / fresh["total"] * 100) if fresh["total"] > 0 else 0
    stale_abandon = (stale["abandoned"] / stale["total"] * 100) if stale["total"] > 0 else 0

    return {
        "fresh_same_session": {
            "total": fresh["total"],
            "abandoned": fresh["abandoned"],
            "abandon_rate_pct": round(fresh_abandon, 1),
        },
        "stale_cross_session": {
            "total": stale["total"],
            "abandoned": stale["abandoned"],
            "abandon_rate_pct": round(stale_abandon, 1),
        },
    }


def measure_domain_conversion(lanes: dict) -> dict:
    """7. Domain productivity. Only counts lanes with recognized domain codes."""
    domains: dict[str, dict] = defaultdict(lambda: {"total": 0, "merged": 0, "abandoned": 0})
    unrecognized_count = 0

    for l in lanes.values():
        if l["status"] not in ("MERGED", "ABANDONED"):
            continue
        domain = l["domain"]
        if domain and domain in VALID_DOMAIN_CODES:
            domains[domain]["total"] += 1
            if l["status"] == "MERGED":
                domains[domain]["merged"] += 1
            elif l["status"] == "ABANDONED":
                domains[domain]["abandoned"] += 1
        else:
            unrecognized_count += 1

    per_domain = {}
    for domain, data in sorted(domains.items()):
        rate = (data["merged"] / data["total"] * 100) if data["total"] > 0 else 0
        per_domain[domain] = {
            "total": data["total"],
            "merged": data["merged"],
            "abandoned": data["abandoned"],
            "conversion_rate_pct": round(rate, 1),
        }

    # Sort by rate for top/bottom, require minimum 2 lanes for ranking
    rankable = {d: v for d, v in per_domain.items() if v["total"] >= 2}
    sorted_domains = sorted(rankable.items(), key=lambda x: (-x[1]["conversion_rate_pct"], -x[1]["total"]))
    top5 = [{"domain": d, **v} for d, v in sorted_domains[:5]]
    bottom_sorted = sorted(rankable.items(), key=lambda x: (x[1]["conversion_rate_pct"], -x[1]["total"]))
    bottom5 = [{"domain": d, **v} for d, v in bottom_sorted[:5]]

    return {
        "per_domain": per_domain,
        "top_5_best": top5,
        "bottom_5_worst": bottom5,
        "recognized_domain_lanes": sum(d["total"] for d in per_domain.values()),
        "unrecognized_lanes": unrecognized_count,
    }


def measure_wave_conversion(lanes: dict) -> dict:
    """8. Wave-aware conversion: group by frontier, track waves."""
    # Group lanes by frontier
    frontier_lanes: dict[str, list[dict]] = defaultdict(list)
    for l in lanes.values():
        if l["status"] not in ("MERGED", "ABANDONED"):
            continue
        frontier = l["frontier"]
        if frontier:
            frontier_lanes[frontier].append(l)

    # For each frontier: count waves (distinct lanes) and whether at least one merged
    wave_buckets: dict[str, dict] = {
        "1_wave": {"total": 0, "resolved": 0},
        "2_wave": {"total": 0, "resolved": 0},
        "3_wave": {"total": 0, "resolved": 0},
        "4plus_wave": {"total": 0, "resolved": 0},
    }

    frontier_details = {}
    for frontier, fls in frontier_lanes.items():
        n_waves = len(fls)
        has_merged = any(fl["status"] == "MERGED" for fl in fls)

        frontier_details[frontier] = {
            "waves": n_waves,
            "has_merged": has_merged,
            "merged_count": sum(1 for fl in fls if fl["status"] == "MERGED"),
            "abandoned_count": sum(1 for fl in fls if fl["status"] == "ABANDONED"),
        }

        if n_waves == 1:
            bucket = "1_wave"
        elif n_waves == 2:
            bucket = "2_wave"
        elif n_waves == 3:
            bucket = "3_wave"
        else:
            bucket = "4plus_wave"

        wave_buckets[bucket]["total"] += 1
        if has_merged:
            wave_buckets[bucket]["resolved"] += 1

    result = {}
    for key, data in wave_buckets.items():
        rate = (data["resolved"] / data["total"] * 100) if data["total"] > 0 else 0
        result[key] = {
            "frontiers": data["total"],
            "with_merged": data["resolved"],
            "resolution_rate_pct": round(rate, 1),
        }

    result["frontier_details"] = frontier_details
    return result


def measure_mode_tracking(lanes: dict) -> dict:
    """5. Mode tracking: mode diversity across frontier waves."""
    # Group lanes with modes by frontier
    frontier_modes: dict[str, dict] = defaultdict(lambda: {"modes": set(), "lanes": [], "merged": 0, "total": 0})

    for l in lanes.values():
        if l["status"] not in ("MERGED", "ABANDONED"):
            continue
        frontier = l["frontier"]
        if not frontier:
            continue

        frontier_modes[frontier]["total"] += 1
        if l["status"] == "MERGED":
            frontier_modes[frontier]["merged"] += 1
        for m in l["modes"]:
            frontier_modes[frontier]["modes"].add(m)
        frontier_modes[frontier]["lanes"].append(l["lane_id"])

    # Compare: frontiers with diverse modes vs single mode
    diverse = {"total": 0, "merged": 0}
    single = {"total": 0, "merged": 0}
    no_mode = {"total": 0, "merged": 0}

    for frontier, data in frontier_modes.items():
        n_modes = len(data["modes"])
        has_merged = data["merged"] > 0

        if n_modes >= 2:
            diverse["total"] += 1
            if has_merged:
                diverse["merged"] += 1
        elif n_modes == 1:
            single["total"] += 1
            if has_merged:
                single["merged"] += 1
        else:
            no_mode["total"] += 1
            if has_merged:
                no_mode["merged"] += 1

    def rate(d):
        return round((d["merged"] / d["total"] * 100) if d["total"] > 0 else 0, 1)

    return {
        "diverse_modes": {"frontiers": diverse["total"], "with_merged": diverse["merged"], "resolution_rate_pct": rate(diverse)},
        "single_mode": {"frontiers": single["total"], "with_merged": single["merged"], "resolution_rate_pct": rate(single)},
        "no_mode_tag": {"frontiers": no_mode["total"], "with_merged": no_mode["merged"], "resolution_rate_pct": rate(no_mode)},
        "note": "mode= tag in Etc field; diverse = 2+ distinct modes across frontier's lanes",
    }


def generate_findings(overall, gap, ead, era, staleness, domains, waves) -> tuple[str, str]:
    """Generate key finding and prescription."""
    # Key finding: what's the strongest predictor?
    findings = []

    # Gap signal
    gap0_rate = gap.get("gap_0", {}).get("abandon_rate_pct", 0)
    gapgt1_rate = gap.get("gap_gt1", {}).get("abandon_rate_pct", 0)
    gap_signal = gapgt1_rate - gap0_rate

    # EAD signal
    ead_diff = ead.get("difference_pp", 0)

    # Era signal
    era_delta = era.get("delta_pp", 0)

    # Staleness signal
    fresh_rate = staleness.get("fresh_same_session", {}).get("abandon_rate_pct", 0)
    stale_rate = staleness.get("stale_cross_session", {}).get("abandon_rate_pct", 0)
    stale_signal = stale_rate - fresh_rate

    # Build finding
    rate = overall.get("conversion_rate_pct", 0)
    n = overall.get("closed_total", 0)

    if gap_signal > stale_signal and gap_signal > abs(ead_diff):
        finding = (
            f"Conversion {rate}% (n={n}); session gap remains strongest abandonment predictor "
            f"(gap>1: {gapgt1_rate}% abandon vs gap=0: {gap0_rate}%); "
            f"post-S384 era delta {era_delta:+.1f}pp."
        )
    elif stale_signal > abs(ead_diff):
        finding = (
            f"Conversion {rate}% (n={n}); staleness (cross-session) predicts "
            f"{stale_rate}% abandon vs {fresh_rate}% for fresh lanes; "
            f"era delta {era_delta:+.1f}pp post-S384."
        )
    else:
        finding = (
            f"Conversion {rate}% (n={n}); EAD compliance is strongest merge predictor "
            f"({ead_diff:+.1f}pp); post-S384 era delta {era_delta:+.1f}pp."
        )

    # Prescription
    if gapgt1_rate > 50:
        prescription = (
            "Enforce session-same execution or auto-abandon after 1-session gap; "
            "lanes not touched within opening session have >50% abandonment probability."
        )
    elif stale_rate > 30:
        prescription = (
            "Auto-flag stale lanes (cross-session without progress) for triage; "
            f"stale lanes abandon at {stale_rate}% vs {fresh_rate}% for fresh."
        )
    else:
        prescription = (
            f"Current conversion rate {rate}% is healthy; maintain EAD enforcement "
            "and session-same execution norm to prevent regression."
        )

    return finding, prescription


def main():
    # Parse all rows from both files
    active_rows = parse_lane_rows(LANES_ACTIVE)
    archive_rows = parse_lane_rows(LANES_ARCHIVE)
    all_rows = archive_rows + active_rows  # Archive first, then active (chronological)

    print(f"Parsed {len(archive_rows)} archive rows + {len(active_rows)} active rows = {len(all_rows)} total")

    # Deduplicate: last row per lane ID is definitive
    lanes = deduplicate_lanes(all_rows)
    print(f"Unique lanes: {len(lanes)}")

    # Count by status
    status_counts = defaultdict(int)
    for l in lanes.values():
        status_counts[l["status"]] += 1
    print(f"Status distribution: {dict(status_counts)}")

    # Run all measurements
    overall = measure_overall_conversion(lanes)
    print(f"\n1. Overall conversion: {overall['conversion_rate_pct']}% ({overall['merged']}/{overall['closed_total']})")

    gap = measure_session_gap_abandonment(lanes)
    print(f"2. Session gap abandonment: gap=0 {gap['gap_0']['abandon_rate_pct']}%, "
          f"gap=1 {gap['gap_1']['abandon_rate_pct']}%, gap>1 {gap['gap_gt1']['abandon_rate_pct']}%")

    ead = measure_ead_compliance(lanes)
    print(f"3. EAD compliance: with={ead['with_ead']['merge_rate_pct']}%, "
          f"without={ead['without_ead']['merge_rate_pct']}% (diff {ead['difference_pp']:+.1f}pp)")

    era = measure_era_comparison(lanes)
    print(f"4. Era: pre-S384 {era['pre_s384']['conversion_rate_pct']}% "
          f"(n={era['pre_s384']['total']}), "
          f"post-S384 {era['post_s384']['conversion_rate_pct']}% "
          f"(n={era['post_s384']['total']}), "
          f"delta {era['delta_pp']:+.1f}pp")

    modes = measure_mode_tracking(lanes)
    print(f"5. Mode tracking: diverse={modes['diverse_modes']['resolution_rate_pct']}%, "
          f"single={modes['single_mode']['resolution_rate_pct']}%, "
          f"no_mode={modes['no_mode_tag']['resolution_rate_pct']}%")

    staleness = measure_staleness(lanes)
    print(f"6. Staleness: fresh={staleness['fresh_same_session']['abandon_rate_pct']}% abandon, "
          f"stale={staleness['stale_cross_session']['abandon_rate_pct']}% abandon")

    domains = measure_domain_conversion(lanes)
    print(f"7. Domain conversion: {len(domains['per_domain'])} domains")
    for d in domains["top_5_best"][:3]:
        print(f"   Best: {d['domain']} {d['conversion_rate_pct']}% (n={d['total']})")
    for d in domains["bottom_5_worst"][:3]:
        print(f"   Worst: {d['domain']} {d['conversion_rate_pct']}% (n={d['total']})")

    waves = measure_wave_conversion(lanes)
    print(f"8. Wave conversion: 1-wave={waves['1_wave']['resolution_rate_pct']}%, "
          f"2-wave={waves['2_wave']['resolution_rate_pct']}%, "
          f"3-wave={waves['3_wave']['resolution_rate_pct']}%, "
          f"4+wave={waves['4plus_wave']['resolution_rate_pct']}%")

    finding, prescription = generate_findings(overall, gap, ead, era, staleness, domains, waves)
    print(f"\nKey finding: {finding}")
    print(f"Prescription: {prescription}")

    # Build output JSON
    # Strip frontier_details from waves for cleaner top-level (keep it as sub-key)
    waves_summary = {k: v for k, v in waves.items() if k != "frontier_details"}
    waves_summary["frontier_detail_count"] = len(waves.get("frontier_details", {}))

    output = {
        "frontier": "F-STR2",
        "session": "S391",
        "measurement_date": "2026-03-01",
        "data_sources": [
            str(LANES_ACTIVE.relative_to(REPO)),
            str(LANES_ARCHIVE.relative_to(REPO)),
        ],
        "total_rows_parsed": len(all_rows),
        "unique_lanes": len(lanes),
        "overall_conversion": overall,
        "session_gap_abandonment": gap,
        "ead_compliance_merge": ead,
        "era_comparison": era,
        "staleness_abandonment": staleness,
        "domain_conversion": domains,
        "wave_conversion": waves_summary,
        "mode_tracking": modes,
        "key_finding": finding,
        "prescription": prescription,
        "prior_measurement": {
            "session": "S381",
            "conversion_rate_pct": 72.4,
            "total_lanes": 29,
            "gap_gt1_abandon_rate": 66.7,
            "gap_le1_abandon_rate": 3.8,
        },
        "delta_from_prior": {
            "conversion_rate_delta_pp": round(overall["conversion_rate_pct"] - 72.4, 1),
            "sample_size_delta": overall["closed_total"] - 29,
            "note": "Prior was S381 (n=29 DOMEX only); current includes all lane types from both files",
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {OUTPUT}")
    return output


if __name__ == "__main__":
    main()
