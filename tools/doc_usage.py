#!/usr/bin/env python3
"""doc_usage.py — classify docs by reference footprint.

Scans `docs/*.md` for incoming explicit path references (`docs/<name>.md`) and
groups the source files into five buckets:

- entry: README / bridge / primary onboarding surfaces
- operational: active state, tools, domains, lessons, tasks
- doc: references from other docs
- artifact: experiments, workspace outputs, test fixtures
- archive: archive files and citation caches

The goal is not to prove semantic usage. It provides a conservative, explicit
link-based audit that helps identify:
- docs that are still live
- docs that only survive in artifacts or archives
- docs that are isolated from current entry surfaces
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"

ENTRY_SURFACES = {
    Path("README.md"),
    Path("SWARM.md"),
    Path("AGENTS.md"),
    Path("CLAUDE.md"),
    Path("GEMINI.md"),
    Path(".github/copilot-instructions.md"),
    Path("docs/HOW-TO-SWARM.md"),
    Path("docs/HUMAN-GUIDE.md"),
    Path("docs/QUESTIONS.md"),
}

TEXT_SUFFIXES = {
    ".md",
    ".mdc",
    ".py",
    ".ps1",
    ".sh",
    ".json",
    ".yml",
    ".yaml",
    ".txt",
}

SESSION_DOC_RE = re.compile(r"(?:^|-)S\d+\b", re.IGNORECASE)
SKIP_TOP_LEVEL_DIRS = {".git", "workspace"}


def is_text_candidate(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    return path.name in {".cursorrules", ".windsurfrules"}


def is_archive_path(rel_path: Path) -> bool:
    path_str = rel_path.as_posix()
    if "archive/" in path_str or path_str.endswith("-ARCHIVE.md") or path_str.endswith("_ARCHIVE.md"):
        return True
    if rel_path.name in {
        "PHILOSOPHY-CHALLENGE-ARCHIVE.md",
        "compact-citation-cache.json",
        "compact-lesson-cache.json",
    }:
        return True
    return False


def classify_source(rel_path: Path) -> str:
    if rel_path in ENTRY_SURFACES:
        return "entry"
    if is_archive_path(rel_path):
        return "archive"
    if rel_path.parts and rel_path.parts[0] == "docs":
        return "doc"
    if rel_path.parts and rel_path.parts[0] in {"experiments", "workspace"}:
        return "artifact"
    if rel_path.parts and rel_path.parts[0] == "tools" and (
        rel_path.name.startswith("test_") or "archive" in rel_path.parts
    ):
        return "artifact"
    return "operational"


def iter_text_files(root: Path) -> Iterable[Path]:
    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)
        rel_root = current_path.relative_to(root)
        if not rel_root.parts:
            dirnames[:] = [
                dirname
                for dirname in dirnames
                if dirname not in SKIP_TOP_LEVEL_DIRS
            ]
        for filename in filenames:
            path = current_path / filename
            if is_text_candidate(path):
                yield path


def recommendation_for(report: dict) -> str:
    if report["entry_refs"] or report["operational_refs"]:
        return "keep"
    if report["doc_refs"]:
        return "index-or-merge"
    if report["artifact_refs"] and report["historical_name"]:
        return "archive-candidate"
    if report["archive_refs"] and report["historical_name"]:
        return "archive-candidate"
    if report["artifact_refs"] or report["archive_refs"]:
        return "index-or-archive"
    return "orphaned"


def collect_doc_usage(root: Path = ROOT) -> list[dict]:
    docs_dir = root / "docs"
    docs = sorted(docs_dir.glob("*.md"))
    docs_by_name = {doc.name: doc for doc in docs}
    reports = {
        name: {
            "doc": f"docs/{name}",
            "entry_refs": 0,
            "operational_refs": 0,
            "doc_refs": 0,
            "artifact_refs": 0,
            "archive_refs": 0,
            "samples": {
                "entry": [],
                "operational": [],
                "doc": [],
                "artifact": [],
                "archive": [],
            },
            "historical_name": bool(SESSION_DOC_RE.search(Path(name).stem)),
        }
        for name in docs_by_name
    }

    needles = {
        name: (f"docs/{name}", f"docs\\{name}")
        for name in docs_by_name
    }

    for path in iter_text_files(root):
        rel = path.relative_to(root)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if "docs/" not in text and "docs\\" not in text:
            continue

        bucket = classify_source(rel)
        for name, (posix_ref, windows_ref) in needles.items():
            if rel == Path("docs") / name:
                continue
            if posix_ref not in text and windows_ref not in text:
                continue

            report = reports[name]
            key = f"{bucket}_refs"
            report[key] += 1
            if len(report["samples"][bucket]) < 3:
                report["samples"][bucket].append(rel.as_posix())

    results = []
    for name in sorted(reports):
        report = reports[name]
        report["status"] = (
            "live"
            if report["entry_refs"] or report["operational_refs"]
            else "non-live"
        )
        report["recommendation"] = recommendation_for(report)
        results.append(report)
    return results


def print_table(reports: list[dict]) -> None:
    if not reports:
        print("No matching docs.")
        return

    header = (
        f"{'status':<8} {'recommendation':<18} {'doc':<42} "
        f"{'entry':>5} {'oper':>5} {'doc':>5} {'art':>5} {'arch':>5}"
    )
    print(header)
    print("-" * len(header))
    for report in reports:
        print(
            f"{report['status']:<8} {report['recommendation']:<18} {report['doc']:<42} "
            f"{report['entry_refs']:>5} {report['operational_refs']:>5} "
            f"{report['doc_refs']:>5} {report['artifact_refs']:>5} "
            f"{report['archive_refs']:>5}"
        )

    print("\nSamples:")
    for report in reports:
        buckets = [
            bucket
            for bucket, refs in report["samples"].items()
            if refs
        ]
        if not buckets:
            continue
        print(f"- {report['doc']}:")
        for bucket in buckets:
            refs = ", ".join(report["samples"][bucket])
            print(f"  {bucket}: {refs}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all",
        action="store_true",
        help="show all docs, not just non-live candidates",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON instead of a text table",
    )
    args = parser.parse_args()

    reports = collect_doc_usage()
    if not args.all:
        reports = [report for report in reports if report["status"] != "live"]

    if args.json:
        print(json.dumps(reports, indent=2))
        return 0

    print_table(reports)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
