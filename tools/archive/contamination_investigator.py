#!/usr/bin/env python3
"""
contamination_investigator.py — Swarm Contamination Investigator

Surfaces contamination signals across swarm state:
  1) Cross-domain contamination (latest F-EVO2 artifacts)
  2) Platform-scope contamination (runtime-specific statements without [scope: host])
  3) Chronology contamination (missing artifact refs in NEXT/SWARM-LANES)

Usage:
  python3 tools/contamination_investigator.py          # human-readable report
  python3 tools/contamination_investigator.py --json   # machine-readable JSON
  python3 tools/contamination_investigator.py --limit 15
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

RUNTIME_KEYWORDS = (
    "python3", "python", "py -3", "bash", "pwsh", "powershell", "wsl",
    "windows", "linux", "macos", "pre-commit", "commit-msg", "hook", "hooks",
    "pip", "pipx", "conda", "node", "npm",
)
SCOPE_TAG_RE = re.compile(r"\[scope:[^\]]+\]", re.IGNORECASE)

PATH_ROOTS = ("experiments", "tools", "domains", "memory", "docs", "tasks")
PATH_RE = re.compile(
    rf"\b(?:{'|'.join(PATH_ROOTS)})/[A-Za-z0-9_./\\-]+"
)
TRAILING_CHARS = ".,);:!?\"'`"

DEFAULT_SCOPE_SCAN = [
    ROOT / "SWARM.md",
    ROOT / "beliefs" / "CORE.md",
    ROOT / "beliefs" / "PHILOSOPHY.md",
    ROOT / "memory" / "PRINCIPLES.md",
    ROOT / "tasks" / "NEXT.md",
]

DEFAULT_ARTIFACT_SCAN = [
    ROOT / "tasks" / "NEXT.md",
    ROOT / "tasks" / "SWARM-LANES.md",
]


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def _clean_path(raw: str) -> str:
    cleaned = raw.strip().rstrip(TRAILING_CHARS)
    if "#" in cleaned:
        cleaned = cleaned.split("#", 1)[0]
    return cleaned


def _latest_contamination_artifacts(limit: int = 3) -> list[dict[str, Any]]:
    artifacts = sorted(
        ROOT.glob("experiments/evolution/f-evo2-contamination-*.json"),
        key=lambda p: p.stat().st_mtime,
    )
    if not artifacts:
        return []
    recent = artifacts[-limit:]
    report = []
    for path in recent:
        try:
            payload = _load_json(path)
        except Exception:
            continue
        report.append(
            {
                "path": _rel(path),
                "contamination_index": payload.get("contamination_index"),
                "contamination_band": payload.get("contamination_band"),
                "components": payload.get("components", {}),
            }
        )
    return report


def scan_platform_scope(paths: list[Path], limit: int) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    counts = Counter()

    for path in paths:
        if not path.exists():
            continue
        for idx, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            lower = line.lower()
            if not any(k in lower for k in RUNTIME_KEYWORDS):
                continue
            if SCOPE_TAG_RE.search(line):
                continue
            keyword = next((k for k in RUNTIME_KEYWORDS if k in lower), None)
            record = {
                "path": _rel(path),
                "line": idx,
                "keyword": keyword,
                "text": line.strip(),
            }
            findings.append(record)
            counts[_rel(path)] += 1

    return {
        "files_scanned": [_rel(p) for p in paths if p.exists()],
        "finding_count": len(findings),
        "top_files": [
            {"path": path, "count": count}
            for path, count in counts.most_common(5)
        ],
        "sample": findings[:limit],
    }


def scan_missing_artifacts(paths: list[Path], limit: int) -> dict[str, Any]:
    missing: dict[str, list[dict[str, Any]]] = {}

    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for idx, line in enumerate(text.splitlines(), start=1):
            for match in PATH_RE.findall(line):
                raw = _clean_path(match)
                if not raw:
                    continue
                rel = raw.replace("\\", "/")
                if rel.startswith("workspace/"):
                    continue
                if not (ROOT / rel).exists():
                    missing.setdefault(rel, []).append(
                        {"path": _rel(path), "line": idx}
                    )

    missing_items = sorted(missing.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    sample = [
        {"path": path, "occurrences": occ[:3], "count": len(occ)}
        for path, occ in missing_items[:limit]
    ]
    return {
        "files_scanned": [_rel(p) for p in paths if p.exists()],
        "missing_count": len(missing_items),
        "sample": sample,
    }


def build_report(limit: int = 10) -> dict[str, Any]:
    contamination_trend = _latest_contamination_artifacts()
    latest = contamination_trend[-1] if contamination_trend else {}
    top_components = []
    components = latest.get("components", {}) if isinstance(latest, dict) else {}
    if isinstance(components, dict):
        ranked = sorted(
            (
                (name, comp.get("component", 0.0))
                for name, comp in components.items()
                if isinstance(comp, dict)
            ),
            key=lambda item: item[1],
            reverse=True,
        )
        top_components = [
            {"component": name, "value": round(value, 4)}
            for name, value in ranked[:5]
        ]

    platform_scope = scan_platform_scope(DEFAULT_SCOPE_SCAN, limit=limit)
    missing_artifacts = scan_missing_artifacts(DEFAULT_ARTIFACT_SCAN, limit=limit)

    recs = []
    band = latest.get("contamination_band")
    if band in {"HIGH", "MEDIUM"}:
        recs.append("Rerun F-EVO2 contamination after executing the top decontamination action.")
    if platform_scope.get("finding_count", 0) > 0:
        recs.append("Add [scope: host] tags to runtime-specific statements to prevent cross-platform contamination.")
    if missing_artifacts.get("missing_count", 0) > 0:
        recs.append("Backfill missing artifact references to reduce chronology contamination.")
    if not recs:
        recs.append("OK: no major contamination signals detected.")

    return {
        "latest_contamination": latest,
        "contamination_trend": contamination_trend,
        "top_contamination_components": top_components,
        "platform_scope_contamination": platform_scope,
        "chronology_contamination": missing_artifacts,
        "recommendations": recs,
    }


def render_human(report: dict[str, Any]) -> str:
    lines = ["=== SWARM CONTAMINATION INVESTIGATOR REPORT ===\n"]

    latest = report.get("latest_contamination") or {}
    if latest:
        lines.append("[CROSS-DOMAIN] Latest F-EVO2 artifact:")
        lines.append(
            f"  {latest.get('path')} | index={latest.get('contamination_index')} "
            f"band={latest.get('contamination_band')}"
        )
        comps = report.get("top_contamination_components") or []
        if comps:
            lines.append("  Top pressure components:")
            for item in comps[:5]:
                lines.append(f"  - {item['component']}: {item['value']}")
    else:
        lines.append("[CROSS-DOMAIN] No F-EVO2 contamination artifacts found.")

    platform = report.get("platform_scope_contamination", {})
    lines.append(
        f"\n[PLATFORM-SCOPE] {platform.get('finding_count', 0)} potential scope issues "
        f"across {len(platform.get('files_scanned', []))} files"
    )
    for item in platform.get("sample", [])[:5]:
        lines.append(f"  - {item['path']}:{item['line']} ({item['keyword']}): {item['text']}")

    chronology = report.get("chronology_contamination", {})
    lines.append(
        f"\n[CHRONOLOGY] {chronology.get('missing_count', 0)} missing artifact refs "
        f"in {len(chronology.get('files_scanned', []))} files"
    )
    for item in chronology.get("sample", [])[:5]:
        lines.append(f"  - {item['path']} (x{item['count']})")

    lines.append("\n[RECOMMENDATIONS]")
    for rec in report.get("recommendations", []):
        lines.append(f"  {rec}")

    return "\n".join(lines)


def main() -> int:
    limit = 10
    if "--limit" in sys.argv:
        try:
            idx = sys.argv.index("--limit")
            limit = int(sys.argv[idx + 1])
        except Exception:
            pass
    report = build_report(limit=limit)
    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        print(render_human(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
