#!/usr/bin/env python3
"""F-PRO1 Hardening: Empirical protocol contract adoption measurement.

Parses SWARM-LANES.md and measures actual vs required field adoption rates.
Identifies lowest-adoption contracts, regression hotspots, and dispatchability.

Session: S391 | Mode: hardening | Frontier: F-PRO1
"""
import re, json, sys
from pathlib import Path
from collections import Counter, defaultdict

LANES_FILE = Path(__file__).resolve().parents[2] / "tasks" / "SWARM-LANES.md"

# Protocol contracts (required fields per lane state)
ACTIVE_REQUIRED = {"setup", "focus", "available", "blocked", "next_step",
                   "human_open_item", "expect", "artifact"}
DOMAIN_REQUIRED = {"domain_sync", "memory_target"}
MERGED_REQUIRED = {"actual", "diff"}
EAD_FIELDS = {"expect", "actual", "diff"}
DISPATCH_FIELDS = {"intent", "frontier", "check_mode"}
OPTIONAL_VALUABLE = {"personality", "mode", "dispatch", "slot"}

ALL_TRACKED = ACTIVE_REQUIRED | DOMAIN_REQUIRED | MERGED_REQUIRED | DISPATCH_FIELDS | OPTIONAL_VALUABLE


def parse_lanes():
    """Parse SWARM-LANES.md pipe-delimited table into lane dicts."""
    text = LANES_FILE.read_text()
    lanes = []
    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 13:
            continue
        date, lane_id, session, agent, branch, pr, model, platform, scope_key, etc, status, notes = parts[1:13]
        if not lane_id or lane_id == "Lane":
            continue
        # Parse Etc field into key=value pairs
        etc_fields = {}
        if etc:
            for item in re.split(r";\s*", etc):
                item = item.strip()
                if "=" in item:
                    k, v = item.split("=", 1)
                    etc_fields[k.strip()] = v.strip()
        lanes.append({
            "date": date, "lane_id": lane_id, "session": session,
            "status": status.strip(), "etc": etc_fields,
            "scope_key": scope_key, "notes": notes,
            "raw_etc": etc
        })
    return lanes


def deduplicate_lanes(lanes):
    """Keep only the latest row per lane_id (append-only log)."""
    latest = {}
    for lane in lanes:
        latest[lane["lane_id"]] = lane  # last one wins
    return list(latest.values())


def extract_session_num(session_str):
    """Extract numeric session from 'S391' or '391'."""
    m = re.search(r"(\d+)", session_str)
    return int(m.group(1)) if m else 0


def measure_adoption(lanes):
    """Measure per-field adoption rates across all lanes."""
    field_counts = Counter()
    field_applicable = Counter()
    per_field_by_era = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # field -> era -> [present, total]

    for lane in lanes:
        status = lane["status"]
        etc = lane["etc"]
        snum = extract_session_num(lane["session"])
        era = "early" if snum < 370 else ("mid" if snum < 385 else "recent")

        # Active-lane required fields
        for field in ACTIVE_REQUIRED:
            field_applicable[field] += 1
            per_field_by_era[field][era][1] += 1
            if field in etc and etc[field] not in ("", "TBD"):
                field_counts[field] += 1
                per_field_by_era[field][era][0] += 1

        # Domain-required fields (check if domain-focused)
        is_domain = ("focus" in etc and "domain" in etc.get("focus", ""))
        if is_domain:
            for field in DOMAIN_REQUIRED:
                field_applicable[field] += 1
                per_field_by_era[field][era][1] += 1
                if field in etc and etc[field] not in ("", "TBD"):
                    field_counts[field] += 1
                    per_field_by_era[field][era][0] += 1

        # Merged-required fields
        if status == "MERGED":
            for field in MERGED_REQUIRED:
                field_applicable[field] += 1
                per_field_by_era[field][era][1] += 1
                if field in etc and etc[field] not in ("", "TBD"):
                    field_counts[field] += 1
                    per_field_by_era[field][era][0] += 1

        # Dispatch and optional fields (count but don't require)
        for field in DISPATCH_FIELDS | OPTIONAL_VALUABLE:
            field_applicable[field] += 1
            per_field_by_era[field][era][1] += 1
            if field in etc and etc[field] not in ("", "TBD"):
                field_counts[field] += 1
                per_field_by_era[field][era][0] += 1

    return field_counts, field_applicable, per_field_by_era


def compute_dispatchability(lanes):
    """Compute how many lanes have enough fields to be machine-routed."""
    dispatchable = 0
    total = 0
    min_dispatch = {"intent", "frontier", "expect", "artifact", "focus"}
    for lane in lanes:
        total += 1
        etc = lane["etc"]
        present = sum(1 for f in min_dispatch if f in etc and etc[f] not in ("", "TBD"))
        if present >= 4:  # 4/5 minimum
            dispatchable += 1
    return dispatchable, total


def find_regressions(lanes, per_field_by_era):
    """Find fields that had higher adoption in early era but dropped."""
    regressions = []
    for field in per_field_by_era:
        eras = per_field_by_era[field]
        early_rate = eras["early"][0] / max(eras["early"][1], 1)
        recent_rate = eras["recent"][0] / max(eras["recent"][1], 1)
        if early_rate > 0.3 and recent_rate < early_rate - 0.15:
            regressions.append((field, early_rate, recent_rate, recent_rate - early_rate))
    regressions.sort(key=lambda x: x[3])
    return regressions


def ead_compliance(lanes):
    """Measure EAD compliance for MERGED lanes."""
    merged = [l for l in lanes if l["status"] == "MERGED"]
    full_ead = 0
    partial_ead = 0
    no_ead = 0
    for lane in merged:
        etc = lane["etc"]
        has_expect = "expect" in etc and etc["expect"] not in ("", "TBD", "test only")
        has_actual = "actual" in etc and etc["actual"] not in ("", "TBD")
        has_diff = "diff" in etc and etc["diff"] not in ("", "TBD")
        if has_expect and has_actual and has_diff:
            full_ead += 1
        elif has_expect or has_actual:
            partial_ead += 1
        else:
            no_ead += 1
    return full_ead, partial_ead, no_ead, len(merged)


def mode_adoption(lanes):
    """Measure explicit mode= field adoption."""
    total = 0
    with_mode = 0
    for lane in lanes:
        total += 1
        if "mode" in lane["etc"] and lane["etc"]["mode"] not in ("", "TBD"):
            with_mode += 1
    return with_mode, total


def main():
    lanes = parse_lanes()
    deduped = deduplicate_lanes(lanes)
    print(f"=== F-PRO1 HARDENING: Protocol Contract Adoption Audit ===")
    print(f"Total lane entries: {len(lanes)}")
    print(f"Unique lanes (deduplicated): {len(deduped)}")
    print()

    # Status breakdown
    status_counts = Counter(l["status"] for l in deduped)
    print("--- Status Breakdown ---")
    for status, count in status_counts.most_common():
        print(f"  {status}: {count} ({100*count/len(deduped):.0f}%)")
    print()

    # Adoption rates
    field_counts, field_applicable, per_field_by_era = measure_adoption(deduped)
    print("--- Per-Field Adoption Rates ---")
    print(f"{'Field':<20} {'Present':>8} {'Applicable':>10} {'Rate':>8}  Category")
    adoption_list = []
    for field in sorted(ALL_TRACKED):
        present = field_counts.get(field, 0)
        applicable = field_applicable.get(field, 0)
        rate = present / max(applicable, 1)
        category = ("ACTIVE-REQ" if field in ACTIVE_REQUIRED
                    else "DOMAIN-REQ" if field in DOMAIN_REQUIRED
                    else "MERGED-REQ" if field in MERGED_REQUIRED
                    else "DISPATCH" if field in DISPATCH_FIELDS
                    else "OPTIONAL")
        adoption_list.append((field, present, applicable, rate, category))
    adoption_list.sort(key=lambda x: x[3])
    for field, present, applicable, rate, category in adoption_list:
        marker = " !" if rate < 0.3 and category.endswith("REQ") else ""
        print(f"  {field:<20} {present:>8} {applicable:>10} {rate:>7.1%}  {category}{marker}")
    print()

    # Top 3 lowest adoption (required fields only)
    required_adoption = [(f, p, a, r) for f, p, a, r, c in adoption_list
                         if c.endswith("REQ")]
    print("--- Top 3 LOWEST Adoption (Required Fields) ---")
    for i, (field, present, applicable, rate) in enumerate(required_adoption[:3]):
        print(f"  {i+1}. {field}: {rate:.1%} ({present}/{applicable})")
    print()

    # Regressions
    regressions = find_regressions(deduped, per_field_by_era)
    print("--- Regression Hotspots (early > recent by >=15pp) ---")
    if regressions:
        for field, early, recent, delta in regressions[:5]:
            print(f"  {field}: {early:.1%} (early) → {recent:.1%} (recent) [{delta:+.1%}]")
    else:
        print("  None detected.")
    print()

    # EAD compliance
    full, partial, none_, total_merged = ead_compliance(deduped)
    print("--- EAD Compliance (MERGED lanes) ---")
    print(f"  Full EAD (expect+actual+diff): {full}/{total_merged} ({100*full/max(total_merged,1):.0f}%)")
    print(f"  Partial EAD: {partial}/{total_merged} ({100*partial/max(total_merged,1):.0f}%)")
    print(f"  No EAD: {none_}/{total_merged} ({100*none_/max(total_merged,1):.0f}%)")
    print()

    # Dispatchability
    dispatchable, total = compute_dispatchability(deduped)
    print("--- Dispatchability (machine-routable lanes) ---")
    print(f"  Dispatchable (4/5 min fields): {dispatchable}/{total} ({100*dispatchable/max(total,1):.0f}%)")
    print()

    # Mode adoption
    with_mode, total_mode = mode_adoption(deduped)
    print("--- Mode Adoption (explicit mode= field) ---")
    print(f"  With mode=: {with_mode}/{total_mode} ({100*with_mode/max(total_mode,1):.0f}%)")
    print()

    # Automability assessment
    print("--- Automability Coverage ---")
    automatable_fields = {"intent", "frontier", "expect", "artifact", "focus", "check_mode"}
    auto_rates = []
    for field in automatable_fields:
        present = field_counts.get(field, 0)
        applicable = field_applicable.get(field, 0)
        rate = present / max(applicable, 1)
        auto_rates.append((field, rate))
    avg_auto = sum(r for _, r in auto_rates) / len(auto_rates)
    print(f"  Avg automatable field adoption: {avg_auto:.1%}")
    for field, rate in sorted(auto_rates, key=lambda x: x[1]):
        print(f"    {field}: {rate:.1%}")
    print()

    # Era comparison
    print("--- Era Comparison (early=S<370 | mid=S370-384 | recent=S385+) ---")
    core_fields = ["expect", "actual", "diff", "intent", "frontier", "artifact"]
    print(f"  {'Field':<15} {'Early':>8} {'Mid':>8} {'Recent':>8}")
    for field in core_fields:
        eras = per_field_by_era[field]
        early_rate = eras["early"][0] / max(eras["early"][1], 1)
        mid_rate = eras["mid"][0] / max(eras["mid"][1], 1)
        recent_rate = eras["recent"][0] / max(eras["recent"][1], 1)
        print(f"  {field:<15} {early_rate:>7.1%} {mid_rate:>7.1%} {recent_rate:>7.1%}")

    # JSON output
    result = {
        "session": "S391",
        "frontier": "F-PRO1",
        "mode": "hardening",
        "total_lanes": len(lanes),
        "unique_lanes": len(deduped),
        "merged": total_merged,
        "ead_full": full,
        "ead_rate": round(full / max(total_merged, 1), 3),
        "dispatchable": dispatchable,
        "dispatchability_rate": round(dispatchable / max(total, 1), 3),
        "mode_adoption": round(with_mode / max(total_mode, 1), 3),
        "lowest_3_required": [(f, round(r, 3)) for f, _, _, r in required_adoption[:3]],
        "regressions": [(f, round(e, 3), round(r, 3)) for f, e, r, _ in regressions[:5]],
        "automability_avg": round(avg_auto, 3),
    }

    out = Path(__file__).resolve().parent / "f-pro1-hardening-s391.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\n[Saved to {out}]")

    return result


if __name__ == "__main__":
    main()
