#!/usr/bin/env python3
"""drift_scanner.py — Protocol drift scanner (F-GOV2).

Compares canonical requirements (SWARM.md, beliefs/CORE.md) against bridge files.
Detects missing blocks, stale content, and synchronization gaps.

Usage:
    python3 tools/drift_scanner.py          # full scan, human-readable
    python3 tools/drift_scanner.py --json   # machine-readable output
"""

import json
import os
import re
import sys
from pathlib import Path

try:
    from swarm_io import session_number
except ImportError:
    def session_number():
        try:
            log = Path("memory/SESSION-LOG.md").read_text()
            nums = re.findall(r"\bS(\d+)\b", log)
            return max(int(n) for n in nums) if nums else 0
        except Exception:
            return 0

ROOT = Path(__file__).resolve().parent.parent

BRIDGE_FILES = {
    "CLAUDE.md": ROOT / "CLAUDE.md",
    "AGENTS.md": ROOT / "AGENTS.md",
    ".cursorrules": ROOT / ".cursorrules",
    "GEMINI.md": ROOT / "GEMINI.md",
    ".windsurfrules": ROOT / ".windsurfrules",
    ".github/copilot-instructions.md": ROOT / ".github" / "copilot-instructions.md",
}

CANONICAL_FILES = {
    "SWARM.md": ROOT / "SWARM.md",
    "beliefs/CORE.md": ROOT / "beliefs" / "CORE.md",
}

# Required blocks that every bridge file should contain.
# Each entry: (id, description, pattern_regex, severity)
REQUIRED_BLOCKS = [
    ("swarm-redirect", "Read SWARM.md redirect",
     r"Read\s+`SWARM\.md`", "HIGH"),
    ("parallel-agents", "Parallel agents section",
     r"\*\*Parallel agents\*\*", "MEDIUM"),
    ("swarm-signaling", "Swarm signaling instructions",
     r"swarm_signal\.py\s+post", "HIGH"),
    ("commit-quality", "Commit quality / hooks",
     r"(check\.sh|install-hooks\.sh|commit.+quality)", "MEDIUM"),
    ("entry-statement", "Entry file statement",
     r"(auto-loads|Entry)", "LOW"),
    ("safety-first", "Safety-first collaboration",
     r"[Ss]afety-first\s+collaboration", "HIGH"),
    ("node-interaction", "Node interaction (minimum-by-default)",
     r"(minimum-by-default|Ask the human node only when blocked)", "HIGH"),
    ("msc-check-mode", "MSC: check mode logging",
     r"check\s+mode.*objective.*historian", "HIGH"),
    ("msc-expect-diff", "MSC: expect/diff declaration",
     r"[Dd]eclare\s+expectation\s+before\s+acting", "HIGH"),
    ("msc-all-outcomes", "MSC: positive/negative/null outcomes",
     r"positive.*negative.*null\s+outcomes", "HIGH"),
    ("msc-expert-dispatch", "MSC: expert dispatch first",
     r"[Ee]xpert\s+dispatch\s+first", "HIGH"),
    ("msc-execute-active", "MSC: execute active swarm work",
     r"[Dd]efault\s+to\s+executing\s+active\s+swarm\s+work", "HIGH"),
    ("msc-bridge-sync", "MSC: keep bridge files synchronized",
     r"[Kk]eep\s+bridge\s+files\s+synchronized", "HIGH"),
    ("multi-tool", "Multi-tool compatibility (F118)",
     r"[Mm]ulti-tool\s+compatibility", "MEDIUM"),
]


def read_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def check_bridge(name, content):
    """Check a bridge file against required blocks. Returns list of findings."""
    findings = []
    for block_id, desc, pattern, severity in REQUIRED_BLOCKS:
        match = re.search(pattern, content)
        if not match:
            findings.append({
                "bridge": name,
                "block": block_id,
                "description": desc,
                "severity": severity,
                "status": "MISSING",
            })
        else:
            findings.append({
                "bridge": name,
                "block": block_id,
                "description": desc,
                "severity": severity,
                "status": "PRESENT",
            })
    return findings


def check_version_tracking(bridges):
    """Check if bridge files have version/sync metadata."""
    findings = []
    for name, path in bridges.items():
        content = read_file(path)
        if content is None:
            findings.append({
                "bridge": name,
                "block": "version-tracking",
                "description": "Bridge file not found",
                "severity": "HIGH",
                "status": "MISSING_FILE",
            })
            continue
        has_version = bool(re.search(
            r"(bridge_version|claude_md_version|sync_version|Last.sync)", content))
        if not has_version:
            findings.append({
                "bridge": name,
                "block": "version-tracking",
                "description": "No version/sync metadata header",
                "severity": "LOW",
                "status": "MISSING",
            })
    return findings


def check_authority_hierarchy(bridges):
    """Check if authority hierarchy is referenced."""
    findings = []
    swarm_content = read_file(CANONICAL_FILES["SWARM.md"]) or ""
    has_hierarchy = bool(re.search(r"Authority hierarchy", swarm_content))
    if not has_hierarchy:
        findings.append({
            "source": "SWARM.md",
            "block": "authority-hierarchy",
            "description": "Authority hierarchy section missing from SWARM.md",
            "severity": "HIGH",
            "status": "MISSING",
        })
    return findings


def compute_sync_matrix(bridges):
    """Compare bridge files pairwise for content drift in shared sections."""
    # Extract Minimum Swarmed Cycle from each bridge
    msc_sections = {}
    for name, path in bridges.items():
        content = read_file(path)
        if content is None:
            continue
        match = re.search(
            r"## Minimum Swarmed Cycle\n(.*?)(?=\n## |\Z)",
            content, re.DOTALL)
        if match:
            msc_sections[name] = match.group(1).strip()

    # Compare each pair
    diffs = []
    names = list(msc_sections.keys())
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if msc_sections[a] != msc_sections[b]:
                diffs.append({
                    "pair": f"{a} vs {b}",
                    "section": "Minimum Swarmed Cycle",
                    "status": "DIVERGED",
                    "a_len": len(msc_sections[a]),
                    "b_len": len(msc_sections[b]),
                })
    return diffs, msc_sections


def scan():
    """Run full drift scan. Returns structured report."""
    report = {
        "scanner": "drift_scanner.py",
        "version": "1.0",
        "session": f"S{session_number()}",
        "bridges_scanned": 0,
        "total_checks": 0,
        "missing": 0,
        "present": 0,
        "findings": [],
        "sync_diffs": [],
        "summary": [],
    }

    # 1. Check each bridge against required blocks
    for name, path in BRIDGE_FILES.items():
        content = read_file(path)
        if content is None:
            report["findings"].append({
                "bridge": name,
                "block": "file-exists",
                "description": f"Bridge file {name} not found",
                "severity": "HIGH",
                "status": "MISSING_FILE",
            })
            continue
        report["bridges_scanned"] += 1
        findings = check_bridge(name, content)
        report["findings"].extend(findings)

    # 2. Check version tracking
    report["findings"].extend(check_version_tracking(BRIDGE_FILES))

    # 3. Check authority hierarchy in SWARM.md
    report["findings"].extend(check_authority_hierarchy(BRIDGE_FILES))

    # 4. Check MSC sync across bridges
    diffs, msc_sections = compute_sync_matrix(BRIDGE_FILES)
    report["sync_diffs"] = diffs

    # Tally
    for f in report["findings"]:
        report["total_checks"] += 1
        if f["status"] == "MISSING" or f["status"] == "MISSING_FILE":
            report["missing"] += 1
        elif f["status"] == "PRESENT":
            report["present"] += 1

    # Generate summary
    missing_by_block = {}
    for f in report["findings"]:
        if f["status"] in ("MISSING", "MISSING_FILE"):
            bid = f.get("block", "unknown")
            missing_by_block.setdefault(bid, []).append(f.get("bridge", "?"))

    for block_id, bridges_missing in missing_by_block.items():
        sev = "HIGH"
        for f in report["findings"]:
            if f.get("block") == block_id and f["status"] in ("MISSING", "MISSING_FILE"):
                sev = f["severity"]
                break
        report["summary"].append({
            "block": block_id,
            "severity": sev,
            "missing_from": bridges_missing,
            "count": len(bridges_missing),
        })

    # Sort summary by severity
    sev_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    report["summary"].sort(key=lambda x: sev_order.get(x["severity"], 3))

    return report


def print_report(report):
    """Print human-readable report."""
    print(f"=== PROTOCOL DRIFT SCANNER (F-GOV2) ===")
    print(f"Session: {report['session']}")
    print(f"Bridges scanned: {report['bridges_scanned']}")
    print(f"Total checks: {report['total_checks']}  "
          f"Present: {report['present']}  Missing: {report['missing']}")
    coverage = (report['present'] / report['total_checks'] * 100
                if report['total_checks'] else 0)
    print(f"Coverage: {coverage:.1f}%")
    print()

    if report["summary"]:
        print("--- Drift findings ---")
        for s in report["summary"]:
            icon = "!!" if s["severity"] == "HIGH" else "~" if s["severity"] == "MEDIUM" else "."
            bridges = ", ".join(s["missing_from"])
            print(f"  {icon} [{s['severity']}] {s['block']}: "
                  f"missing from {s['count']} bridge(s): {bridges}")
        print()

    if report["sync_diffs"]:
        print("--- MSC sync divergence ---")
        for d in report["sync_diffs"]:
            print(f"  {d['pair']}: {d['section']} "
                  f"({d['a_len']} vs {d['b_len']} chars)")
        print()

    if not report["summary"] and not report["sync_diffs"]:
        print("  All bridges synchronized. No drift detected.")


def main():
    report = scan()
    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    # Exit code: 1 if any HIGH severity missing
    high_missing = any(
        s["severity"] == "HIGH" for s in report["summary"]
    )
    sys.exit(1 if high_missing else 0)


if __name__ == "__main__":
    main()
