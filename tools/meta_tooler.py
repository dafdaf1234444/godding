#!/usr/bin/env python3
"""meta_tooler.py — Tool health scanner for meta-tooler dispatch (SIG-39, L-890, L-896).

Scans tools/ for maintenance needs: oversized files, unreferenced tools,
stale tools, code quality markers (TODO/FIXME/HACK), test coverage gaps.
Outputs structured JSON + human-readable summary. Modeled after historian_repair.py.

Usage:
    python3 tools/meta_tooler.py              # human-readable summary
    python3 tools/meta_tooler.py --json       # structured JSON output
    python3 tools/meta_tooler.py --category oversized|unreferenced|stale|quality|tests|all
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / "tools"
ARCHIVE_DIR = ROOT / "tools" / "archive"

# Thresholds
T4_TOKEN_CEILING = 5_000  # tokens (chars//4) — L-469 anti-cascade
STALE_SESSION_THRESHOLD = 50  # sessions since last git modification
UNREFERENCED_ENTRY_FILES = [
    "tools/check.sh", "tools/orient.py", "tools/maintenance.py",
    "tools/periodics.json", "CLAUDE.md", "SWARM.md", "tools/task_order.py",
    "tools/dispatch_optimizer.py",
]

sys.path.insert(0, str(TOOLS_DIR))
try:
    from swarm_io import session_number as _session_number
except ImportError:
    def _session_number() -> int:
        r = subprocess.run(["git", "log", "--oneline", "-50"],
                           capture_output=True, text=True, cwd=str(ROOT))
        nums = [int(m) for m in re.findall(r"\[S(\d+)\]", r.stdout)]
        return max(nums) if nums else 0


@dataclass
class Finding:
    category: str  # oversized, unreferenced, stale, quality, tests
    severity: str  # HIGH, MEDIUM, LOW
    tool: str
    message: str
    metric: float | int | None = None


def _tool_files() -> list[Path]:
    """List production tool .py files (exclude tests, __init__, archive)."""
    if not TOOLS_DIR.exists():
        return []
    return sorted(
        f for f in TOOLS_DIR.glob("*.py")
        if not f.stem.startswith("test_")
        and f.stem != "__init__"
        and "archive" not in str(f)
    )


def _tool_tokens(path: Path) -> int:
    """Estimate token count (chars // 4)."""
    try:
        return len(path.read_text(encoding="utf-8", errors="replace")) // 4
    except OSError:
        return 0


def _git_last_sessions() -> dict[str, int]:
    """Batch: find last session number for all tool files in one git call."""
    try:
        r = subprocess.run(
            ["git", "log", "--oneline", "--name-only", "-300", "--", "tools/*.py"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=15
        )
        # Parse: each commit line has [S<N>], followed by file path lines
        result: dict[str, int] = {}
        current_session = 0
        for line in r.stdout.splitlines():
            m = re.search(r"\[S(\d+)\]", line)
            if m:
                current_session = int(m.group(1))
            elif line.startswith("tools/") and line.endswith(".py"):
                stem = Path(line).stem
                if stem not in result:  # first occurrence = most recent
                    result[stem] = current_session
        return result
    except (subprocess.TimeoutExpired, OSError):
        return {}


def scan_oversized() -> list[Finding]:
    """T4 anti-cascade: tools exceeding token ceiling."""
    findings = []
    for f in _tool_files():
        tokens = _tool_tokens(f)
        if tokens > T4_TOKEN_CEILING:
            sev = "HIGH" if tokens > T4_TOKEN_CEILING * 3 else "MEDIUM"
            findings.append(Finding(
                category="oversized", severity=sev, tool=f.stem,
                message=f"{tokens}t exceeds {T4_TOKEN_CEILING}t ceiling",
                metric=tokens,
            ))
    findings.sort(key=lambda x: -(x.metric or 0))
    return findings


def scan_unreferenced() -> list[Finding]:
    """Tools not referenced by any automation entry point."""
    ref_text = ""
    for ef in UNREFERENCED_ENTRY_FILES:
        ef_path = ROOT / ef
        if ef_path.exists():
            try:
                ref_text += ef_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
    findings = []
    for f in _tool_files():
        if f.stem not in ref_text:
            findings.append(Finding(
                category="unreferenced", severity="LOW", tool=f.stem,
                message="not referenced by automation entry points",
            ))
    return findings


def scan_stale() -> list[Finding]:
    """Tools not modified in many sessions (batched git query)."""
    current = _session_number()
    last_sessions = _git_last_sessions()
    findings = []
    for f in _tool_files():
        last = last_sessions.get(f.stem)
        if last is not None:
            gap = current - last
            if gap > STALE_SESSION_THRESHOLD:
                sev = "MEDIUM" if gap > STALE_SESSION_THRESHOLD * 2 else "LOW"
                findings.append(Finding(
                    category="stale", severity=sev, tool=f.stem,
                    message=f"last modified S{last} ({gap} sessions ago)",
                    metric=gap,
                ))
    findings.sort(key=lambda x: -(x.metric or 0))
    return findings


def scan_quality() -> list[Finding]:
    """Code quality markers in comments (# TODO, # FIXME, etc.)."""
    # Match markers only in comment lines to avoid false positives in regex definitions
    marker_re = re.compile(r"#\s*(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)
    findings = []
    for f in _tool_files():
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits = marker_re.findall(content)
        if hits:
            count = len(hits)
            sev = "MEDIUM" if count >= 3 else "LOW"
            findings.append(Finding(
                category="quality", severity=sev, tool=f.stem,
                message=f"{count} comment marker(s): {', '.join(set(h.upper() for h in hits))}",
                metric=count,
            ))
    findings.sort(key=lambda x: -(x.metric or 0))
    return findings


def scan_tests() -> list[Finding]:
    """Tools lacking corresponding test files."""
    test_files = {f.stem.replace("test_", "") for f in TOOLS_DIR.glob("test_*.py")}
    findings = []
    for f in _tool_files():
        tokens = _tool_tokens(f)
        # Only flag tools with substantial logic (>500 tokens)
        if tokens > 500 and f.stem not in test_files:
            findings.append(Finding(
                category="tests", severity="LOW", tool=f.stem,
                message=f"no test file (test_{f.stem}.py) — {tokens}t",
                metric=tokens,
            ))
    findings.sort(key=lambda x: -(x.metric or 0))
    return findings


SCANNERS = {
    "oversized": scan_oversized,
    "unreferenced": scan_unreferenced,
    "stale": scan_stale,
    "quality": scan_quality,
    "tests": scan_tests,
}


def run_scan(categories: list[str] | None = None) -> dict:
    """Run selected scanners and return structured results."""
    cats = categories or list(SCANNERS.keys())
    all_findings: list[Finding] = []
    for cat in cats:
        if cat in SCANNERS:
            all_findings.extend(SCANNERS[cat]())

    total = len(_tool_files())
    high = [f for f in all_findings if f.severity == "HIGH"]
    medium = [f for f in all_findings if f.severity == "MEDIUM"]
    low = [f for f in all_findings if f.severity == "LOW"]

    return {
        "total_tools": total,
        "findings_count": len(all_findings),
        "high": len(high),
        "medium": len(medium),
        "low": len(low),
        "findings": [
            {"category": f.category, "severity": f.severity,
             "tool": f.tool, "message": f.message, "metric": f.metric}
            for f in all_findings
        ],
        "by_category": {
            cat: len([f for f in all_findings if f.category == cat])
            for cat in cats
        },
    }


def print_report(data: dict) -> None:
    """Print human-readable summary."""
    print(f"\n=== META-TOOLER SCAN ({data['total_tools']} tools) ===")
    print(f"  Findings: {data['findings_count']} "
          f"(HIGH={data['high']}, MEDIUM={data['medium']}, LOW={data['low']})")
    print(f"  Categories: {data['by_category']}")

    if data["high"] > 0:
        print(f"\n--- HIGH severity ({data['high']}) ---")
        for f in data["findings"]:
            if f["severity"] == "HIGH":
                print(f"  🔴 [{f['category']}] {f['tool']}: {f['message']}")

    if data["medium"] > 0:
        print(f"\n--- MEDIUM severity ({data['medium']}) ---")
        for f in data["findings"]:
            if f["severity"] == "MEDIUM":
                print(f"  🟡 [{f['category']}] {f['tool']}: {f['message']}")

    top_low = [f for f in data["findings"] if f["severity"] == "LOW"][:5]
    if top_low:
        remaining = data["low"] - len(top_low)
        print(f"\n--- LOW severity (top 5 of {data['low']}) ---")
        for f in top_low:
            print(f"  ⚪ [{f['category']}] {f['tool']}: {f['message']}")
        if remaining > 0:
            print(f"  ... and {remaining} more")

    # Actionable summary
    oversized_high = [f for f in data["findings"]
                      if f["category"] == "oversized" and f["severity"] == "HIGH"]
    if oversized_high:
        print(f"\n--- Recommended actions ---")
        for f in oversized_high:
            print(f"  → Split/refactor {f['tool']}.py ({f['metric']}t > {T4_TOKEN_CEILING}t ceiling)")


def main():
    parser = argparse.ArgumentParser(description="Meta-tooler: tool health scanner")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--category", default="all",
                        choices=["oversized", "unreferenced", "stale", "quality", "tests", "all"])
    args = parser.parse_args()

    cats = list(SCANNERS.keys()) if args.category == "all" else [args.category]
    data = run_scan(cats)

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_report(data)


if __name__ == "__main__":
    main()
