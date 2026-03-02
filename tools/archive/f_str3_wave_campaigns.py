#!/usr/bin/env python3
"""F-STR3 Multi-Wave Campaign Analysis for DOMEX Lanes.

Parses all MERGED lanes from SWARM-LANES.md (and archive), groups them by
domain+frontier to identify "campaigns" (sequences of visits to the same
frontier), classifies each visit by wave position, and compares outcomes.

Wave classification:
  Wave 1 — First touch (exploration): opening new frontier questions
  Wave 2 — Follow-up (hardening): refining measurements, fixing bugs
  Wave 3+ — Resolution attempt: trying to RESOLVE or produce definitive answer

Output: JSON to stdout + artifact file.

Usage:
  python3 tools/f_str3_wave_campaigns.py
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANES_FILE = os.path.join(REPO_ROOT, "tasks", "SWARM-LANES.md")
ARCHIVE_FILE = os.path.join(REPO_ROOT, "tasks", "SWARM-LANES-ARCHIVE.md")
OUTPUT_FILE = os.path.join(
    REPO_ROOT, "experiments", "strategy",
    "f-str3-wave-campaigns-s385.json"
)

# Domain abbreviation mapping (from dispatch_optimizer.py)
LANE_ABBREV_TO_DOMAIN = {
    "NK": "nk-complexity", "LNG": "linguistics", "EXP": "expert-swarm",
    "STAT": "statistics", "PHI": "philosophy", "CTX": "meta", "MECH": "meta",
    "FLD": "fluid-dynamics", "BRN": "brain", "HLP": "helper-swarm",
    "ECO": "economy", "PHY": "physics", "SCI": "evaluation", "EVO": "evolution",
    "DNA": "meta", "IS": "information-science", "HS": "human-systems",
    "COMP": "competitions", "INFO": "information-science",
    "META": "meta", "SP": "stochastic-processes", "EMP": "empathy",
    "AI": "ai", "CON": "conflict", "CONFLICT": "conflict",
    "CAT": "catastrophic-risks", "DS": "distributed-systems",
    "FIN": "finance", "GOV": "governance", "EVAL": "evaluation",
    "FRA": "fractals", "FRACTALS": "fractals", "GT": "graph-theory",
    "GTH": "graph-theory", "GAME": "gaming", "GAMING": "gaming",
    "SEC": "security", "SECURITY": "security",
    "GUE": "guesstimates", "GAM": "game-theory", "PSY": "psychology",
    "SOC": "social-media", "STR": "strategy", "QC": "quality",
    "QUALITY": "quality", "OR": "operations-research", "OPS": "operations-research",
    "FARMING": "farming", "FAR": "farming", "COORD": "meta", "HUMAN": "human-systems",
    "INFOFLOW": "information-science", "INFRA": "meta", "GEN": "meta",
    "DREAM": "dream", "BRAIN": "brain", "ECON": "economy", "ECONOMY": "economy",
    "EMPATHY": "empathy", "EVOLUTION": "evolution", "EXPERT": "expert-swarm",
    "AGENT": "meta", "CT": "meta", "CTL": "control-theory",
    "CC": "cryptocurrency", "CRY": "cryptography", "CRYPTO": "cryptocurrency",
    "CRYPTOGRAPHY": "cryptography",
    "PRO": "protocol-engineering", "README": "meta",
    "SCHED": "meta", "PRIORITY": "meta", "UNIVERSALITY": "meta",
    "PERSONALITY": "psychology",
}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def extract_session_number(lane_id, session_col):
    """Extract session number from lane_id (preferred) or session column."""
    m = re.search(r'S(\d+)', lane_id)
    if m:
        return int(m.group(1))
    m = re.search(r'S?(\d+)', session_col.strip())
    if m:
        return int(m.group(1))
    return None


def extract_domain_abbrev(lane_id):
    """Extract domain abbreviation from lane_id.

    e.g. DOMEX-META-S377 -> META, DOMEX-CAT2-S381 -> CAT
    Strips trailing digits from the domain part (e.g. META4 -> META, CAT2 -> CAT).
    """
    m = re.match(r'DOMEX-([A-Z]+)\d*-', lane_id)
    if m:
        return m.group(1)
    return None


def extract_domain(lane_id):
    """Extract full domain name from lane_id via abbreviation mapping."""
    abbrev = extract_domain_abbrev(lane_id)
    if abbrev and abbrev in LANE_ABBREV_TO_DOMAIN:
        return LANE_ABBREV_TO_DOMAIN[abbrev]
    if abbrev:
        return abbrev.lower()
    return "unknown"


def extract_etc_field(etc_col, field_name):
    """Extract a named field from the Etc column (semicolon-delimited key=value)."""
    # Match field_name=value up to the next semicolon or pipe or end of string
    pattern = rf'(?:^|;\s*){field_name}=([^;|]+)'
    m = re.search(pattern, etc_col)
    if m:
        return m.group(1).strip()
    return None


def extract_frontier(etc_col, note_col):
    """Extract frontier ID from Etc or Note columns.

    Looks for frontier=F-XXX or frontier=SIG-NN patterns.
    """
    combined = etc_col + " " + note_col
    m = re.search(r'frontier=(F-[A-Z]+\d*|SIG-\d+)', combined)
    if m:
        return m.group(1)
    return None


def extract_intent(etc_col):
    """Extract intent field from Etc column."""
    return extract_etc_field(etc_col, "intent")


def count_lessons(text):
    """Count unique L-NNN references in a text string."""
    matches = re.findall(r'\bL-(\d+)\b', text)
    return len(set(matches))


def check_ead_fields(etc_col, note_col):
    """Check which EAD fields are present and non-TBD."""
    combined = etc_col + " " + note_col
    fields = {}
    for field in ["expect", "actual", "diff"]:
        m = re.search(rf'{field}=([^;|]+)', combined)
        if m:
            val = m.group(1).strip()
            fields[field] = val.upper() not in ("TBD", "", "N/A")
        else:
            fields[field] = False
    return fields


def check_ead_compliance(etc_col, note_col):
    """Check if actual and diff EAD fields are filled (not TBD or empty)."""
    fields = check_ead_fields(etc_col, note_col)
    return fields.get("actual", False) and fields.get("diff", False)


def is_resolution_note(note_col, etc_col):
    """Check if the note indicates a frontier was RESOLVED."""
    combined = (note_col + " " + etc_col).upper()
    return "RESOLVED" in combined


def parse_lane_row(line):
    """Parse a pipe-delimited lane row into a dict.

    Columns: Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes
    """
    parts = [p.strip() for p in line.split("|")]
    # Remove empty strings from leading/trailing pipes
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]

    if len(parts) < 12:
        return None

    date_str = parts[0].strip()
    lane_id = parts[1].strip()

    # Only process DOMEX lanes
    if "DOMEX" not in lane_id:
        return None

    session_col = parts[2].strip()
    etc_col = parts[9].strip()
    status = parts[10].strip().upper()
    note = parts[11].strip() if len(parts) > 11 else ""

    session_num = extract_session_number(lane_id, session_col)
    if session_num is None:
        return None

    domain = extract_domain(lane_id)
    frontier = extract_frontier(etc_col, note)
    intent = extract_intent(etc_col)
    lessons = count_lessons(etc_col + " " + note)
    ead_ok = check_ead_compliance(etc_col, note)
    ead_fields = check_ead_fields(etc_col, note)
    resolved = is_resolution_note(note, etc_col)

    return {
        "lane_id": lane_id,
        "date": date_str,
        "session_num": session_num,
        "domain": domain,
        "frontier": frontier,
        "intent": intent,
        "status": status,
        "lessons": lessons,
        "ead_compliant": ead_ok,
        "ead_fields": ead_fields,
        "resolved": resolved,
        "etc": etc_col,
        "note": note,
    }


def load_lanes(filepath):
    """Load and parse all DOMEX lanes from a file."""
    lanes = []
    if not os.path.exists(filepath):
        return lanes
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            if "---" in line and line.count("|") > 3:
                continue
            if "Lane" in line and "Session" in line and "Status" in line:
                continue
            row = parse_lane_row(line)
            if row:
                lanes.append(row)
    return lanes


def deduplicate_lanes(lanes):
    """Keep only the LATEST row per lane_id (append-only log -> last wins)."""
    seen = {}
    for lane in lanes:
        lid = lane["lane_id"]
        seen[lid] = lane
    return list(seen.values())


# ---------------------------------------------------------------------------
# Campaign detection
# ---------------------------------------------------------------------------
def classify_intent(intent_str):
    """Classify an intent string into a broad category."""
    if not intent_str:
        return "unknown"
    intent_lower = intent_str.lower()

    # Resolution-oriented intents
    if any(k in intent_lower for k in ["resolve", "fix", "harden", "wire", "repair"]):
        return "hardening"

    # Measurement / exploration intents
    if any(k in intent_lower for k in ["build", "measure", "test", "audit",
                                        "detect", "analysis", "backtest",
                                        "explore", "advance", "baseline"]):
        return "exploration"

    # Validation / follow-up intents
    if any(k in intent_lower for k in ["validate", "prospective", "verify",
                                        "refine", "correct", "re-measure",
                                        "consolidat", "diagnos"]):
        return "validation"

    # Closure intents
    if any(k in intent_lower for k in ["closure", "close"]):
        return "closure"

    return "exploration"  # default


def build_campaigns(lanes):
    """Group lanes by frontier to form campaigns.

    A campaign is a sequence of lanes targeting the same frontier,
    ordered chronologically by session number.
    """
    # Only keep MERGED and ABANDONED lanes (closed outcomes)
    closed = [l for l in lanes if l["status"] in ("MERGED", "ABANDONED")]

    # Group by frontier (skip lanes with no frontier)
    frontier_groups = defaultdict(list)
    no_frontier = []
    for lane in closed:
        frontier = lane["frontier"]
        if frontier:
            frontier_groups[frontier].append(lane)
        else:
            no_frontier.append(lane)

    campaigns = []
    for frontier, group in sorted(frontier_groups.items()):
        # Sort by session_num for chronological order
        group.sort(key=lambda l: l["session_num"])

        # All lanes in same frontier form one campaign
        waves = []
        for i, lane in enumerate(group):
            wave_num = i + 1
            intent_type = classify_intent(lane["intent"])
            waves.append({
                "wave": wave_num,
                "lane_id": lane["lane_id"],
                "session": lane["session_num"],
                "domain": lane["domain"],
                "status": lane["status"],
                "intent": lane["intent"],
                "intent_type": intent_type,
                "lessons": lane["lessons"],
                "ead_compliant": lane["ead_compliant"],
                "ead_fields": lane["ead_fields"],
                "resolved": lane["resolved"],
            })

        # Determine campaign outcome
        merged_waves = [w for w in waves if w["status"] == "MERGED"]
        any_resolved = any(w["resolved"] for w in waves)
        total_lessons = sum(w["lessons"] for w in waves)
        merged_lessons = sum(w["lessons"] for w in merged_waves)
        domains = list(set(w["domain"] for w in waves))

        campaigns.append({
            "frontier": frontier,
            "domain": domains[0] if len(domains) == 1 else "/".join(sorted(set(domains))),
            "domains": sorted(set(domains)),
            "wave_count": len(waves),
            "merged_count": len(merged_waves),
            "abandoned_count": len(waves) - len(merged_waves),
            "resolved": any_resolved,
            "total_lessons": total_lessons,
            "merged_lessons": merged_lessons,
            "avg_lessons_per_wave": round(total_lessons / len(waves), 2) if waves else 0,
            "intent_sequence": [w["intent_type"] for w in waves],
            "waves": waves,
        })

    return campaigns, no_frontier


# ---------------------------------------------------------------------------
# Aggregate statistics
# ---------------------------------------------------------------------------
def compute_resolution_by_waves(campaigns):
    """Resolution rate grouped by number of waves."""
    groups = defaultdict(lambda: {"total": 0, "resolved": 0, "campaigns": []})
    for c in campaigns:
        wc = c["wave_count"]
        key = str(wc) if wc <= 3 else "4+"
        groups[key]["total"] += 1
        if c["resolved"]:
            groups[key]["resolved"] += 1
        groups[key]["campaigns"].append(c["frontier"])

    result = {}
    for key in sorted(groups.keys()):
        g = groups[key]
        rate = g["resolved"] / g["total"] if g["total"] > 0 else 0
        result[f"{key}_wave"] = {
            "total_campaigns": g["total"],
            "resolved": g["resolved"],
            "resolution_rate": round(rate, 3),
            "frontiers": g["campaigns"],
        }
    return result


def compute_yield_by_position(campaigns):
    """Average lesson yield by wave position (1, 2, 3+)."""
    position_data = defaultdict(list)
    for c in campaigns:
        for w in c["waves"]:
            pos = w["wave"]
            key = str(pos) if pos <= 3 else "4+"
            position_data[key].append(w["lessons"])

    result = {}
    for key in sorted(position_data.keys()):
        vals = position_data[key]
        result[f"wave_{key}"] = {
            "n_lanes": len(vals),
            "total_lessons": sum(vals),
            "avg_lessons": round(sum(vals) / len(vals), 2) if vals else 0,
            "min": min(vals) if vals else 0,
            "max": max(vals) if vals else 0,
        }
    return result


def compute_ead_by_position(campaigns):
    """EAD compliance rate by wave position."""
    position_data = defaultdict(lambda: {"total": 0, "compliant": 0,
                                          "has_actual": 0, "has_diff": 0})
    for c in campaigns:
        for w in c["waves"]:
            pos = w["wave"]
            key = str(pos) if pos <= 3 else "4+"
            position_data[key]["total"] += 1
            if w["ead_compliant"]:
                position_data[key]["compliant"] += 1
            if w["ead_fields"].get("actual", False):
                position_data[key]["has_actual"] += 1
            if w["ead_fields"].get("diff", False):
                position_data[key]["has_diff"] += 1

    result = {}
    for key in sorted(position_data.keys()):
        d = position_data[key]
        n = d["total"]
        result[f"wave_{key}"] = {
            "n_lanes": n,
            "ead_compliant": d["compliant"],
            "ead_rate": round(d["compliant"] / n, 3) if n > 0 else 0,
            "has_actual_rate": round(d["has_actual"] / n, 3) if n > 0 else 0,
            "has_diff_rate": round(d["has_diff"] / n, 3) if n > 0 else 0,
        }
    return result


def compute_dominant_templates(campaigns):
    """Find the most common intent-type sequences (wave templates)."""
    template_counts = defaultdict(lambda: {"count": 0, "frontiers": [],
                                            "resolved": 0})
    for c in campaigns:
        seq = tuple(c["intent_sequence"])
        template_counts[seq]["count"] += 1
        template_counts[seq]["frontiers"].append(c["frontier"])
        if c["resolved"]:
            template_counts[seq]["resolved"] += 1

    # Sort by count descending
    sorted_templates = sorted(template_counts.items(),
                               key=lambda x: x[1]["count"], reverse=True)

    result = []
    for seq, data in sorted_templates:
        result.append({
            "template": list(seq),
            "template_str": " -> ".join(seq),
            "count": data["count"],
            "frontiers": data["frontiers"],
            "resolution_rate": round(data["resolved"] / data["count"], 3)
                if data["count"] > 0 else 0,
        })
    return result


def compute_domain_summary(campaigns):
    """Per-domain campaign statistics."""
    domain_data = defaultdict(lambda: {
        "campaigns": 0, "total_waves": 0, "resolved": 0,
        "total_lessons": 0, "frontiers": []
    })
    for c in campaigns:
        for d in c["domains"]:
            domain_data[d]["campaigns"] += 1
            domain_data[d]["total_waves"] += c["wave_count"]
            if c["resolved"]:
                domain_data[d]["resolved"] += 1
            domain_data[d]["total_lessons"] += c["total_lessons"]
            domain_data[d]["frontiers"].append(c["frontier"])

    result = {}
    for domain in sorted(domain_data.keys()):
        d = domain_data[domain]
        result[domain] = {
            "campaigns": d["campaigns"],
            "total_waves": d["total_waves"],
            "avg_waves_per_campaign": round(d["total_waves"] / d["campaigns"], 2)
                if d["campaigns"] > 0 else 0,
            "resolved": d["resolved"],
            "resolution_rate": round(d["resolved"] / d["campaigns"], 3)
                if d["campaigns"] > 0 else 0,
            "total_lessons": d["total_lessons"],
            "frontiers": d["frontiers"],
        }
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Load from both files
    lanes_active = load_lanes(LANES_FILE)
    lanes_archive = load_lanes(ARCHIVE_FILE)
    all_lanes = lanes_archive + lanes_active

    # Deduplicate: keep last occurrence per lane_id
    all_lanes = deduplicate_lanes(all_lanes)

    print("=" * 70)
    print("F-STR3 Multi-Wave Campaign Analysis")
    print("=" * 70)
    print()
    print(f"Total DOMEX lanes parsed: {len(all_lanes)}")

    # Status breakdown
    status_counts = defaultdict(int)
    for l in all_lanes:
        status_counts[l["status"]] += 1
    print(f"Status breakdown: {dict(status_counts)}")

    # Build campaigns from closed lanes
    campaigns, no_frontier = build_campaigns(all_lanes)

    # Sort campaigns by wave count descending for display
    campaigns.sort(key=lambda c: c["wave_count"], reverse=True)

    print(f"Campaigns identified: {len(campaigns)}")
    print(f"Lanes without frontier (excluded from campaigns): {len(no_frontier)}")
    print()

    # Compute aggregate stats
    resolution_by_waves = compute_resolution_by_waves(campaigns)
    yield_by_position = compute_yield_by_position(campaigns)
    ead_by_position = compute_ead_by_position(campaigns)
    dominant_templates = compute_dominant_templates(campaigns)
    domain_summary = compute_domain_summary(campaigns)

    # Print campaign details
    print("--- TOP CAMPAIGNS (by wave count) ---")
    for c in campaigns[:15]:
        resolved_tag = "RESOLVED" if c["resolved"] else "OPEN"
        print(f"  {c['frontier']:12s} | domain={c['domain']:20s} | "
              f"waves={c['wave_count']} | merged={c['merged_count']} | "
              f"lessons={c['total_lessons']} | {resolved_tag}")
        for w in c["waves"]:
            status_mark = "+" if w["status"] == "MERGED" else "x"
            print(f"    [{status_mark}] W{w['wave']} S{w['session']} "
                  f"{w['lane_id']:25s} type={w['intent_type']:12s} "
                  f"L={w['lessons']} EAD={'Y' if w['ead_compliant'] else 'N'}")
    print()

    # Print resolution rates
    print("--- RESOLUTION RATE BY WAVE COUNT ---")
    for key, val in resolution_by_waves.items():
        print(f"  {key}: {val['resolved']}/{val['total_campaigns']} "
              f"({val['resolution_rate']:.1%})")
    print()

    # Print yield by position
    print("--- LESSON YIELD BY WAVE POSITION ---")
    for key, val in yield_by_position.items():
        print(f"  {key}: avg={val['avg_lessons']:.2f} "
              f"(n={val['n_lanes']}, total={val['total_lessons']}, "
              f"range={val['min']}-{val['max']})")
    print()

    # Print EAD compliance by position
    print("--- EAD COMPLIANCE BY WAVE POSITION ---")
    for key, val in ead_by_position.items():
        print(f"  {key}: EAD={val['ead_rate']:.1%} "
              f"actual={val['has_actual_rate']:.1%} "
              f"diff={val['has_diff_rate']:.1%} (n={val['n_lanes']})")
    print()

    # Print dominant templates
    print("--- DOMINANT WAVE TEMPLATES ---")
    for t in dominant_templates[:10]:
        print(f"  [{t['count']}x] {t['template_str']} "
              f"(resolution={t['resolution_rate']:.0%}) "
              f"— {', '.join(t['frontiers'][:3])}"
              f"{'...' if len(t['frontiers']) > 3 else ''}")
    print()

    # Print domain summary
    print("--- DOMAIN SUMMARY ---")
    for domain, d in sorted(domain_summary.items(),
                             key=lambda x: x[1]["campaigns"], reverse=True):
        print(f"  {domain:25s} campaigns={d['campaigns']} "
              f"avg_waves={d['avg_waves_per_campaign']:.1f} "
              f"resolved={d['resolved']}/{d['campaigns']} "
              f"({d['resolution_rate']:.0%}) lessons={d['total_lessons']}")
    print()

    # Aggregate numbers
    total_campaigns = len(campaigns)
    total_domains = len(domain_summary)
    multi_wave = [c for c in campaigns if c["wave_count"] >= 2]
    single_wave = [c for c in campaigns if c["wave_count"] == 1]
    resolved_campaigns = [c for c in campaigns if c["resolved"]]

    # Overall stats
    overall_resolution_rate = (len(resolved_campaigns) / total_campaigns
                                if total_campaigns > 0 else 0)
    multi_wave_resolution = (sum(1 for c in multi_wave if c["resolved"]) /
                              len(multi_wave) if multi_wave else 0)
    single_wave_resolution = (sum(1 for c in single_wave if c["resolved"]) /
                               len(single_wave) if single_wave else 0)

    total_lanes_in_campaigns = sum(c["wave_count"] for c in campaigns)
    total_lessons_in_campaigns = sum(c["total_lessons"] for c in campaigns)

    print("--- SUMMARY ---")
    print(f"  Total campaigns: {total_campaigns}")
    print(f"  Total domains: {total_domains}")
    print(f"  Multi-wave campaigns (2+): {len(multi_wave)}")
    print(f"  Single-wave campaigns: {len(single_wave)}")
    print(f"  Overall resolution rate: {overall_resolution_rate:.1%}")
    print(f"  Multi-wave resolution: {multi_wave_resolution:.1%}")
    print(f"  Single-wave resolution: {single_wave_resolution:.1%}")
    print(f"  Total lanes in campaigns: {total_lanes_in_campaigns}")
    print(f"  Total lessons in campaigns: {total_lessons_in_campaigns}")
    print()

    # Build output JSON
    # Simplify campaigns for JSON (remove full etc/note from waves)
    campaigns_json = []
    for c in campaigns:
        simplified_waves = []
        for w in c["waves"]:
            simplified_waves.append({
                "wave": w["wave"],
                "lane_id": w["lane_id"],
                "session": w["session"],
                "domain": w["domain"],
                "status": w["status"],
                "intent_type": w["intent_type"],
                "lessons": w["lessons"],
                "ead_compliant": w["ead_compliant"],
                "resolved": w["resolved"],
            })
        campaigns_json.append({
            "frontier": c["frontier"],
            "domain": c["domain"],
            "wave_count": c["wave_count"],
            "merged_count": c["merged_count"],
            "abandoned_count": c["abandoned_count"],
            "resolved": c["resolved"],
            "total_lessons": c["total_lessons"],
            "avg_lessons_per_wave": c["avg_lessons_per_wave"],
            "intent_sequence": c["intent_sequence"],
            "waves": simplified_waves,
        })

    output = {
        "experiment": "F-STR3 Multi-Wave Campaign Analysis",
        "session": "S385",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "frontier": "F-STR3",
        "method": (
            "Parse all closed DOMEX lanes from SWARM-LANES.md and archive. "
            "Group by frontier to form campaigns. Classify wave positions "
            "(1=exploration, 2=hardening, 3+=resolution). Compare outcomes "
            "by wave count: resolution rate, lesson yield, EAD compliance. "
            "Identify dominant intent-type sequences (wave templates)."
        ),
        "data_sources": [
            "tasks/SWARM-LANES.md",
            "tasks/SWARM-LANES-ARCHIVE.md",
        ],
        "summary": {
            "total_domex_lanes_parsed": len(all_lanes),
            "lanes_in_campaigns": total_lanes_in_campaigns,
            "lanes_without_frontier": len(no_frontier),
            "campaign_count": total_campaigns,
            "domain_count": total_domains,
            "multi_wave_campaigns": len(multi_wave),
            "single_wave_campaigns": len(single_wave),
            "overall_resolution_rate": round(overall_resolution_rate, 3),
            "multi_wave_resolution_rate": round(multi_wave_resolution, 3),
            "single_wave_resolution_rate": round(single_wave_resolution, 3),
            "total_lessons_in_campaigns": total_lessons_in_campaigns,
        },
        "resolution_rate_by_waves": resolution_by_waves,
        "yield_by_position": yield_by_position,
        "ead_by_position": ead_by_position,
        "dominant_templates": dominant_templates[:15],
        "domain_summary": domain_summary,
        "campaigns": campaigns_json,
    }

    # Write JSON artifact
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Artifact written to: {OUTPUT_FILE}")

    # Also output full JSON to stdout for piping
    print()
    print("=== JSON OUTPUT ===")
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
