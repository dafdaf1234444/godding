#!/usr/bin/env python3
"""F-META4 baseline: evaluate visual representability contract adoption."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


EXPECTED_PRIMITIVES = (
    "Node: `Frontier`",
    "Node: `Lane`",
    "Node: `Artifact`",
    "Node: `Knowledge`",
    "Edge: `executes`",
    "Edge: `produces`",
    "Edge: `updates`",
    "Edge: `blocked_by`",
)

EXPECTED_VIEWS = (
    "### 1) Human Orientation View",
    "### 2) Swarm Self-Check View",
    "### 3) Swarm-to-Swarm Exchange View",
)

FRESHNESS_MARKERS = (
    "`session`",
    "`date`",
    "source files",
)


def _coverage(text: str, expected_tokens: Iterable[str]) -> dict[str, object]:
    expected = list(expected_tokens)
    found = [token for token in expected if token in text]
    missing = [token for token in expected if token not in text]
    total = len(expected)
    ratio = (len(found) / total) if total else 1.0
    return {
        "expected_total": total,
        "found_count": len(found),
        "coverage_ratio": ratio,
        "missing": missing,
    }


def analyze_contract(contract_text: str) -> dict[str, object]:
    primitive = _coverage(contract_text, EXPECTED_PRIMITIVES)
    views = _coverage(contract_text, EXPECTED_VIEWS)
    freshness = _coverage(contract_text, FRESHNESS_MARKERS)
    score = (primitive["coverage_ratio"] + views["coverage_ratio"] + freshness["coverage_ratio"]) / 3.0
    return {
        "primitive_coverage": primitive,
        "view_coverage": views,
        "freshness_rule_coverage": freshness,
        "contract_score": score,
    }


def analyze_adoption(file_texts: dict[str, str]) -> dict[str, object]:
    checks = {
        "README.md references visual contract": "SWARM-VISUAL-REPRESENTABILITY.md" in file_texts.get("README.md", ""),
        "memory/INDEX.md references visual contract": "SWARM-VISUAL-REPRESENTABILITY.md" in file_texts.get("memory/INDEX.md", ""),
        "meta frontier contains F-META4": "F-META4" in file_texts.get("domains/meta/tasks/FRONTIER.md", ""),
        "meta index contains F-META4": "F-META4" in file_texts.get("domains/meta/INDEX.md", ""),
        "lane log has F-META4 row": "F-META4" in file_texts.get("tasks/SWARM-LANES.md", ""),
    }
    passed = sum(1 for passed in checks.values() if passed)
    total = len(checks)
    return {
        "checks": checks,
        "passed": passed,
        "total": total,
        "adoption_ratio": (passed / total) if total else 1.0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output JSON artifact path.",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/SWARM-VISUAL-REPRESENTABILITY.md"),
        help="Path to visual representability contract doc.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    file_paths = {
        "README.md": Path("README.md"),
        "memory/INDEX.md": Path("memory/INDEX.md"),
        "domains/meta/tasks/FRONTIER.md": Path("domains/meta/tasks/FRONTIER.md"),
        "domains/meta/INDEX.md": Path("domains/meta/INDEX.md"),
        "tasks/SWARM-LANES.md": Path("tasks/SWARM-LANES.md"),
    }
    file_texts = {
        key: path.read_text(encoding="utf-8") if path.exists() else ""
        for key, path in file_paths.items()
    }

    contract_text = args.contract.read_text(encoding="utf-8")
    contract = analyze_contract(contract_text)
    adoption = analyze_adoption(file_texts)
    overall_score = (contract["contract_score"] + adoption["adoption_ratio"]) / 2.0

    payload = {
        "frontier": "F-META4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "inputs": {
            "contract_path": str(args.contract),
            "adoption_paths": {key: str(path) for key, path in file_paths.items()},
        },
        "contract": contract,
        "adoption": adoption,
        "summary": {
            "overall_score": overall_score,
            "status": "baseline_pass" if overall_score >= 0.95 else "baseline_gap",
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {args.out}")
    print(
        "overall_score=",
        f"{overall_score:.3f}",
        "contract_score=",
        f"{contract['contract_score']:.3f}",
        "adoption_ratio=",
        f"{adoption['adoption_ratio']:.3f}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
