#!/usr/bin/env python3
"""
check_fmea_audit.py — Cross-check periodics.json against FMEA defense layers.

Purpose: Manual FMEA auditors miss pre-existing periodic registrations.
FM-30 was undercounted at S441 (cascade_monitor periodic was registered S436
but auditor only counted orient + check.sh layers). This tool detects such gaps.

Usage:
  python3 tools/check_fmea_audit.py [--json] [--verbose]

Output: per-FM periodic coverage report + upgrade candidates.
"""

import re
import json
import glob
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent


def load_latest_fmea_artifact():
    pattern = str(ROOT / "experiments/catastrophic-risks/f-cat1-fmea-s*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        return None, None
    path = files[-1]
    with open(path) as f:
        return json.load(f), path


def load_periodics():
    path = ROOT / "tools/periodics.json"
    with open(path) as f:
        data = json.load(f)
    return data.get("items", [])


def extract_fm_blocks(frontier_text):
    """Extract per-FM tool references from FMEA FRONTIER.md narrative text.

    FMs appear in narrative format: 'FM-NN status (layers: tool1, tool2)'
    or 'FM-NN MINIMAL. 3 defense layers: layer1, layer2.'
    We extract all tool references per FM-ID across all narrative lines.
    """
    fms = {}
    # Find all FM-NN mentions and collect surrounding tool references
    fm_pattern = re.compile(r'\b(FM-\d+)\b')
    tool_pattern = re.compile(r'\b(\w+\.(?:py|sh))\b')

    # Split into lines; for each line mentioning an FM, extract tools
    for line in frontier_text.splitlines():
        fm_ids = fm_pattern.findall(line)
        if not fm_ids:
            continue
        tools = tool_pattern.findall(line)
        for fm_id in fm_ids:
            if fm_id not in fms:
                fms[fm_id] = {"name": fm_id, "tools_referenced": [], "body_snippet": ""}
            fms[fm_id]["tools_referenced"].extend(tools)
            if not fms[fm_id]["body_snippet"]:
                fms[fm_id]["body_snippet"] = line[:150]

    # Deduplicate tool lists
    for fm_id in fms:
        fms[fm_id]["tools_referenced"] = list(dict.fromkeys(fms[fm_id]["tools_referenced"]))

    return fms


def build_tool_to_periodic_map(periodics):
    """Map tool filenames to periodic IDs that mention them."""
    mapping = {}
    for item in periodics:
        desc = item.get("description", "") + " " + item.get("note", "")
        tools = re.findall(r'\b(\w+\.(?:py|sh))\b', desc)
        for t in tools:
            if t not in mapping:
                mapping[t] = []
            mapping[t].append(item["id"])
    return mapping


def get_fm_status_from_artifact(artifact):
    """Extract FM statuses from the FMEA artifact."""
    data = artifact.get("data", {})
    statuses = {}
    # From fm_status_changes we get upgrades
    for fm_id, info in data.get("fm_status_changes", {}).items():
        statuses[fm_id] = info.get("new_status", "UNKNOWN")
    # From remaining_minimal_fms
    for item in data.get("remaining_minimal_fms", []):
        if item["id"] not in statuses:
            statuses[item["id"]] = "MINIMAL"
    return statuses


def check_scan_perspectives():
    """FM-35 defense: detect single-perspective FMEA scans (L-1108).

    Scans all FMEA artifacts from the most recent NAT window and checks
    for scan_perspectives metadata. Single-perspective scans miss ~50% of FMs.
    Returns (perspective_count, perspectives_found, warning_message).
    """
    pattern = str(ROOT / "experiments/catastrophic-risks/f-cat1-fmea-s*.json")
    files = sorted(glob.glob(pattern))
    if len(files) < 2:
        return 0, [], None

    # Check last 3 FMEA artifacts (typical NAT window span)
    recent = files[-3:]
    perspectives = set()
    missing_field = 0
    for f in recent:
        try:
            with open(f) as fh:
                data = json.load(fh)
            sp = data.get("scan_perspectives") or data.get("data", {}).get("scan_perspectives")
            if sp:
                if isinstance(sp, list):
                    perspectives.update(sp)
                else:
                    perspectives.add(str(sp))
            else:
                missing_field += 1
        except (json.JSONDecodeError, IOError):
            pass

    warning = None
    if missing_field == len(recent):
        warning = (
            f"FM-35 NOTICE: {len(recent)} recent FMEA artifacts lack scan_perspectives field. "
            f"L-1108: single-scanner FMEA misses ~50% of FMs. "
            f"Add scan_perspectives to FMEA experiment JSON."
        )
    elif len(perspectives) < 2:
        warning = (
            f"FM-35 WARNING: Only {len(perspectives)} scan perspective(s) in last {len(recent)} "
            f"FMEA artifacts: {sorted(perspectives)}. L-1108: need ≥2 for adequate coverage."
        )

    return len(perspectives), sorted(perspectives), warning


def run_audit(verbose=False):
    artifact, artifact_path = load_latest_fmea_artifact()
    if not artifact:
        print("ERROR: No FMEA artifact found in experiments/catastrophic-risks/")
        return 1

    periodics = load_periodics()
    tool_to_periodic = build_tool_to_periodic_map(periodics)

    frontier_path = ROOT / "domains/catastrophic-risks/tasks/FRONTIER.md"
    frontier_text = frontier_path.read_text() if frontier_path.exists() else ""
    fm_blocks = extract_fm_blocks(frontier_text)

    fm_statuses = get_fm_status_from_artifact(artifact)

    print(f"=== FMEA AUDIT — Periodic Coverage Cross-Check ===")
    print(f"Artifact: {Path(artifact_path).name}")
    print(f"Periodics: {len(periodics)} registered | FMs parsed: {len(fm_blocks)}")

    # FM-35 scanner perspective check (L-1108)
    n_persp, persp_list, persp_warning = check_scan_perspectives()
    if persp_warning:
        print(f"\n  {persp_warning}")
    elif n_persp >= 2:
        print(f"\n  FM-35 OK: {n_persp} scan perspectives detected: {persp_list}")
    print()

    periodic_hits = []
    no_coverage = []

    for fm_id in sorted(fm_blocks.keys(), key=lambda x: int(x.split('-')[1])):
        fm = fm_blocks[fm_id]
        status = fm_statuses.get(fm_id, "UNKNOWN")
        covered_by = []
        for tool in fm["tools_referenced"]:
            if tool in tool_to_periodic:
                for pid in tool_to_periodic[tool]:
                    covered_by.append((tool, pid))

        if covered_by:
            periodic_hits.append((fm_id, fm["name"], status, covered_by))
        elif status in ("MINIMAL", "PARTIAL", "INADEQUATE") and verbose:
            no_coverage.append((fm_id, fm["name"], status))

    if periodic_hits:
        print("FMs with periodic defense coverage (verify these layers are counted):")
        for fm_id, name, status, covered in periodic_hits:
            tools_str = ", ".join(f"{t}→[{pid}]" for t, pid in covered)
            marker = " ⚠ CHECK LAYER COUNT" if status in ("MINIMAL", "PARTIAL") else ""
            print(f"  {fm_id} [{status}] {name[:50]}")
            print(f"    Periodic coverage: {tools_str}{marker}")
        print()
    else:
        print("No FM-periodic cross-references found via tool-name matching.")
        print()

    upgrade_candidates = [
        (fm_id, fm["name"], status, covered)
        for fm_id, fm["name"], status, covered in periodic_hits
        if status in ("MINIMAL", "PARTIAL")
    ]
    if upgrade_candidates:
        print("UPGRADE CANDIDATES — periodic layer may push FM toward ADEQUATE:")
        for fm_id, name, status, covered in upgrade_candidates:
            print(f"  {fm_id} ({status}): periodic '{covered[0][1]}' via {covered[0][0]}")
    else:
        print("No upgrade candidates found via periodic cross-check.")

    if verbose and no_coverage:
        print()
        print("MINIMAL/PARTIAL FMs with no periodic coverage (for reference):")
        for fm_id, name, status in no_coverage:
            print(f"  {fm_id} [{status}] {name[:60]}")

    # Summary
    dist = artifact.get("data", {}).get("mitigation_distribution", {})
    print()
    print(f"Current distribution: {dist}")
    print(f"FMs with periodic coverage: {len(periodic_hits)}")
    print(f"Potential undercounts to verify: {len(upgrade_candidates)}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--verbose", action="store_true", help="Show all FMs")
    args = parser.parse_args()

    if args.json:
        artifact, artifact_path = load_latest_fmea_artifact()
        periodics = load_periodics()
        tool_to_periodic = build_tool_to_periodic_map(periodics)
        frontier_path = ROOT / "domains/catastrophic-risks/tasks/FRONTIER.md"
        frontier_text = frontier_path.read_text() if frontier_path.exists() else ""
        fm_blocks = extract_fm_blocks(frontier_text)
        result = {
            "artifact": Path(artifact_path).name if artifact_path else None,
            "fms_parsed": len(fm_blocks),
            "periodics_checked": len(periodics),
            "tool_to_periodic_count": len(tool_to_periodic),
        }
        print(json.dumps(result, indent=2))
        return 0

    return run_audit(verbose=args.verbose)


if __name__ == "__main__":
    exit(main())
