#!/usr/bin/env python3
"""F-CTL3: estimate quality loss under open-loop vs closed-loop session behavior."""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean, median
from typing import Any

import change_quality as cq

REPO_ROOT = Path(__file__).resolve().parent.parent

CHECK_RE = re.compile(
    r"\b(check\.sh|check\.ps1|validate_beliefs|beliefs:\s*pass|maintenance)\b",
    re.IGNORECASE,
)
ORIENT_RE = re.compile(r"\borient(\.py|\.ps1)?\b", re.IGNORECASE)


def classify_session(sig: dict[str, Any]) -> dict[str, bool]:
    text = " | ".join(sig.get("msgs", []))
    has_check = bool(CHECK_RE.search(text))
    has_orient = bool(ORIENT_RE.search(text))
    # Closed-loop requires explicit feedback instrumentation.
    closed_loop = has_check
    return {
        "closed_loop": closed_loop,
        "has_check": has_check,
        "has_orient": has_orient,
    }


def _sample_std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean = fmean(values)
    num = sum((x - mean) ** 2 for x in values)
    return math.sqrt(num / (len(values) - 1))


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {
            "n_sessions": 0,
            "sessions": [],
            "mean_score": 0.0,
            "median_score": 0.0,
            "std_score": 0.0,
            "mean_overhead_ratio": 0.0,
            "mean_lessons": 0.0,
            "mean_principles": 0.0,
        }

    scores = [r["score"] for r in records]
    overhead = [r["overhead_ratio"] for r in records]
    lessons = [r["lessons"] for r in records]
    principles = [r["principles"] for r in records]
    sessions = sorted(r["session"] for r in records)

    return {
        "n_sessions": len(records),
        "sessions": sessions,
        "mean_score": round(fmean(scores), 4),
        "median_score": round(median(scores), 4),
        "std_score": round(_sample_std(scores), 4),
        "mean_overhead_ratio": round(fmean(overhead), 4),
        "mean_lessons": round(fmean(lessons), 4),
        "mean_principles": round(fmean(principles), 4),
    }


def nearest_pair_delta(
    open_loop: list[dict[str, Any]],
    closed_loop: list[dict[str, Any]],
) -> dict[str, Any]:
    if not open_loop or not closed_loop:
        return {
            "n_pairs": 0,
            "mean_closed_minus_open": 0.0,
            "median_closed_minus_open": 0.0,
            "pairs": [],
        }

    closed_by_session = {r["session"]: r for r in closed_loop}
    closed_sessions = sorted(closed_by_session.keys())
    pairs: list[dict[str, Any]] = []

    for row in sorted(open_loop, key=lambda x: x["session"]):
        s = row["session"]
        closest = min(closed_sessions, key=lambda cs: abs(cs - s))
        c = closed_by_session[closest]
        pairs.append(
            {
                "open_session": s,
                "closed_session": closest,
                "session_gap": abs(closest - s),
                "open_score": row["score"],
                "closed_score": c["score"],
                "closed_minus_open": round(c["score"] - row["score"], 4),
            }
        )

    deltas = [p["closed_minus_open"] for p in pairs]
    return {
        "n_pairs": len(pairs),
        "mean_closed_minus_open": round(fmean(deltas), 4),
        "median_closed_minus_open": round(median(deltas), 4),
        "pairs": pairs[:20],
    }


def run(session_min: int, out_path: Path) -> dict[str, Any]:
    commits = cq.get_commits()
    sessions_data = cq.extract_session_signals(commits)
    if not sessions_data:
        raise ValueError("no session data found in git history")

    records: list[dict[str, Any]] = []
    for session, sig in sessions_data.items():
        if session < session_min:
            continue
        cls = classify_session(sig)
        records.append(
            {
                "session": session,
                "score": round(cq.quality_score(sig), 4),
                "overhead_ratio": round(
                    sig["overhead_commits"] / max(1, sig["commits"]), 4
                ),
                "lessons": len(sig["lessons"]),
                "principles": len(sig["principles"]),
                "closed_loop": cls["closed_loop"],
                "has_check": cls["has_check"],
                "has_orient": cls["has_orient"],
            }
        )

    open_loop = [r for r in records if not r["closed_loop"]]
    closed_loop = [r for r in records if r["closed_loop"]]
    open_summary = summarize(open_loop)
    closed_summary = summarize(closed_loop)

    mean_delta = round(
        closed_summary["mean_score"] - open_summary["mean_score"], 4
    )
    overhead_delta = round(
        open_summary["mean_overhead_ratio"] - closed_summary["mean_overhead_ratio"], 4
    )
    pair_delta = nearest_pair_delta(open_loop, closed_loop)

    result = {
        "frontier_id": "F-CTL3",
        "title": "Open-loop vs closed-loop quality comparison",
        "session_filter_min": session_min,
        "classification_rule": {
            "closed_loop_if": "session has explicit check/validation signal in commit messages",
            "signals": [
                "orient(.py/.ps1)",
                "check.sh/check.ps1",
                "validate_beliefs",
                "Beliefs: PASS",
                "maintenance",
            ],
        },
        "open_loop": open_summary,
        "closed_loop": closed_summary,
        "delta": {
            "mean_score_closed_minus_open": mean_delta,
            "mean_overhead_open_minus_closed": overhead_delta,
            "matched_pair_mean_closed_minus_open": pair_delta["mean_closed_minus_open"],
            "matched_pair_median_closed_minus_open": pair_delta["median_closed_minus_open"],
        },
        "matched_pairs": pair_delta,
        "interpretation": {
            "direction": (
                "closed_loop_better"
                if mean_delta > 0
                else "open_loop_better"
                if mean_delta < 0
                else "neutral"
            ),
            "caveat": (
                "Proxy classification from commit-message evidence; some sessions may have orient/check activity "
                "without explicit log mentions."
            ),
        },
    }

    result["generated_at_utc"] = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--session-min",
        type=int,
        default=150,
        help="Minimum session to include (default: 150 for modern protocol era)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/control-theory/f-ctl3-open-loop-vs-closed-loop-s186.json"),
        help="Output artifact path",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    result = run(session_min=args.session_min, out_path=args.out)
    print(f"Wrote {args.out}")
    print(
        "mean_score_closed_minus_open=",
        result["delta"]["mean_score_closed_minus_open"],
        "open_sessions=",
        result["open_loop"]["n_sessions"],
        "closed_sessions=",
        result["closed_loop"]["n_sessions"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
