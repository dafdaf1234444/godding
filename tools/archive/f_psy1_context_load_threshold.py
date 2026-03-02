#!/usr/bin/env python3
"""F-PSY1: estimate context-load thresholds where execution quality degrades."""

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

ACTIVE_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}
LANE_KEYS = (
    "date",
    "lane",
    "session",
    "agent",
    "branch",
    "pr",
    "model",
    "platform",
    "scope_key",
    "etc",
    "status",
    "notes",
)
SESSION_RE = re.compile(r"S(\d+)")
TAG_RE = re.compile(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*([^\s,;|]+)")
WORD_RE = re.compile(r"[A-Za-z0-9_-]+")
NEXT_EVENT_RE = re.compile(r"^S(\d+):\s*(.+)$")


def parse_lane_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|\s*(Date\s*\||[-: ]+\|)", line, re.IGNORECASE):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < len(LANE_KEYS):
            continue
        row = dict(zip(LANE_KEYS, parts))
        row["status"] = row["status"].upper()
        rows.append(row)
    return rows


def parse_session_number(raw: str) -> int | None:
    m = SESSION_RE.search(raw or "")
    return int(m.group(1)) if m else None


def _sample_std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean = fmean(values)
    num = sum((x - mean) ** 2 for x in values)
    return math.sqrt(num / (len(values) - 1))


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    x_mean = fmean(xs)
    y_mean = fmean(ys)
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_den = math.sqrt(sum((x - x_mean) ** 2 for x in xs))
    y_den = math.sqrt(sum((y - y_mean) ** 2 for y in ys))
    den = x_den * y_den
    if den == 0:
        return 0.0
    return num / den


def _word_count(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def _tag_count(text: str) -> int:
    return len(TAG_RE.findall(text or ""))


def parse_next_updates(text: str, session_min: int) -> dict[int, dict[str, float]]:
    by_session_words: dict[int, list[int]] = {}
    for raw in text.splitlines():
        m = NEXT_EVENT_RE.match(raw.strip())
        if not m:
            continue
        session = int(m.group(1))
        if session < session_min:
            continue
        words = _word_count(m.group(2))
        by_session_words.setdefault(session, []).append(words)

    out: dict[int, dict[str, float]] = {}
    for session, words in by_session_words.items():
        out[session] = {
            "next_event_count": float(len(words)),
            "next_event_mean_words": round(fmean(words), 4) if words else 0.0,
        }
    return out


def session_lane_metrics(rows: list[dict[str, str]], session_min: int) -> dict[int, dict[str, float]]:
    by_session: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        session = parse_session_number(row.get("session", ""))
        if session is None or session < session_min:
            continue
        by_session.setdefault(session, []).append(row)

    out: dict[int, dict[str, float]] = {}
    for session, s_rows in by_session.items():
        lane_rows = len(s_rows)
        unique_lanes = len({r.get("lane", "") for r in s_rows if r.get("lane", "")})
        active_rows = sum(1 for r in s_rows if r.get("status", "") in ACTIVE_STATUSES)
        note_words = [_word_count(r.get("notes", "")) for r in s_rows]
        etc_tags = [_tag_count(r.get("etc", "")) for r in s_rows]
        mean_note_words = fmean(note_words) if note_words else 0.0
        mean_etc_tags = fmean(etc_tags) if etc_tags else 0.0
        update_density = lane_rows / max(1, unique_lanes)
        # Composite proxy for coordination cognitive load.
        context_load_score = (
            update_density * 0.55
            + active_rows * 0.20
            + mean_note_words * 0.15
            + mean_etc_tags * 0.10
        )
        out[session] = {
            "lane_rows": float(lane_rows),
            "unique_lanes": float(unique_lanes),
            "active_rows": float(active_rows),
            "update_density": round(update_density, 4),
            "mean_note_words": round(mean_note_words, 4),
            "mean_etc_tags": round(mean_etc_tags, 4),
            "context_load_score": round(context_load_score, 4),
        }
    return out


def session_quality_metrics(session_min: int) -> dict[int, dict[str, float]]:
    commits = cq.get_commits()
    sessions_data = cq.extract_session_signals(commits)
    out: dict[int, dict[str, float]] = {}
    for session, sig in sessions_data.items():
        if session < session_min:
            continue
        commits_n = sig["commits"]
        overhead_ratio = sig["overhead_commits"] / max(1, commits_n)
        out[session] = {
            "quality_score": round(cq.quality_score(sig), 4),
            "commits": float(commits_n),
            "lessons": float(len(sig["lessons"])),
            "principles": float(len(sig["principles"])),
            "overhead_ratio": round(overhead_ratio, 4),
        }
    return out


def _quantile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_vals[lo]
    frac = pos - lo
    return sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac


def threshold_sweep(
    records: list[dict[str, Any]],
    metric_key: str = "context_load_score",
    min_bucket: int = 3,
) -> dict[str, Any]:
    if len(records) < (min_bucket * 2):
        return {"evaluated": 0, "best": None, "candidates": []}

    values = sorted(r[metric_key] for r in records)
    quantiles = [0.35, 0.45, 0.55, 0.65, 0.75]
    thresholds = sorted({round(_quantile(values, q), 4) for q in quantiles})
    candidates: list[dict[str, Any]] = []

    for thr in thresholds:
        low = [r for r in records if r[metric_key] < thr]
        high = [r for r in records if r[metric_key] >= thr]
        if len(low) < min_bucket or len(high) < min_bucket:
            continue
        low_scores = [r["quality_score"] for r in low]
        high_scores = [r["quality_score"] for r in high]
        delta = fmean(low_scores) - fmean(high_scores)
        pooled_std = _sample_std(low_scores + high_scores)
        effect_size = 0.0 if pooled_std == 0 else delta / pooled_std
        candidates.append(
            {
                "threshold": thr,
                "low_count": len(low),
                "high_count": len(high),
                "low_mean_quality": round(fmean(low_scores), 4),
                "high_mean_quality": round(fmean(high_scores), 4),
                "low_median_quality": round(median(low_scores), 4),
                "high_median_quality": round(median(high_scores), 4),
                "delta_low_minus_high": round(delta, 4),
                "effect_size": round(effect_size, 4),
            }
        )

    if not candidates:
        return {"evaluated": 0, "best": None, "candidates": []}

    best = max(
        candidates,
        key=lambda c: (c["delta_low_minus_high"], c["effect_size"], c["threshold"]),
    )
    return {"evaluated": len(candidates), "best": best, "candidates": candidates}


def run(lanes_path: Path, next_path: Path, session_min: int, out_path: Path) -> dict[str, Any]:
    rows = parse_lane_rows(lanes_path.read_text(encoding="utf-8", errors="replace"))
    lane_by_session = session_lane_metrics(rows, session_min=session_min)
    next_by_session = parse_next_updates(
        next_path.read_text(encoding="utf-8", errors="replace"),
        session_min=session_min,
    )
    quality_by_session = session_quality_metrics(session_min=session_min)

    sessions = sorted((set(lane_by_session) | set(next_by_session)) & set(quality_by_session))
    records: list[dict[str, Any]] = []
    for s in sessions:
        lane = lane_by_session.get(
            s,
            {
                "lane_rows": 0.0,
                "unique_lanes": 0.0,
                "active_rows": 0.0,
                "update_density": 0.0,
                "mean_note_words": 0.0,
                "mean_etc_tags": 0.0,
                "context_load_score": 0.0,
            },
        )
        nxt = next_by_session.get(s, {"next_event_count": 0.0, "next_event_mean_words": 0.0})

        # Blend lane-load and NEXT event load into one cognitive-load proxy.
        next_event_load = nxt["next_event_count"] * 0.7 + (nxt["next_event_mean_words"] / 20.0)
        context_load_score = (
            lane["context_load_score"] * 0.65
            + next_event_load * 0.35
        )

        rec = {"session": s}
        rec.update(lane)
        rec.update(nxt)
        rec["next_event_load"] = round(next_event_load, 4)
        rec["context_load_score"] = round(context_load_score, 4)
        rec.update(quality_by_session[s])
        records.append(rec)

    load_scores = [r["context_load_score"] for r in records]
    quality_scores = [r["quality_score"] for r in records]
    correlation = round(_pearson(load_scores, quality_scores), 4) if records else 0.0
    sweep = threshold_sweep(records, metric_key="context_load_score", min_bucket=3)
    best = sweep["best"]

    result: dict[str, Any] = {
        "frontier_id": "F-PSY1",
        "title": "Context-load threshold vs execution quality",
        "inputs": {
            "lanes_path": str(lanes_path).replace("\\", "/"),
            "next_path": str(next_path).replace("\\", "/"),
            "session_min": session_min,
            "active_statuses": sorted(ACTIVE_STATUSES),
            "metric_formula": (
                "lane_load = 0.55*update_density + 0.20*active_rows + "
                "0.15*mean_note_words + 0.10*mean_etc_tags; "
                "next_event_load = 0.7*next_event_count + next_event_mean_words/20; "
                "context_load_score = 0.65*lane_load + 0.35*next_event_load"
            ),
        },
        "summary": {
            "sessions_joined": len(records),
            "session_range": {
                "start": sessions[0] if sessions else None,
                "end": sessions[-1] if sessions else None,
            },
            "context_load_quality_correlation": correlation,
            "best_threshold": best,
            "direction": (
                "higher_load_associated_with_lower_quality"
                if best and best["delta_low_minus_high"] > 0
                else "no_drop_detected_or_reverse"
            ),
            "threshold_candidates_evaluated": sweep["evaluated"],
        },
        "records": records,
        "threshold_sweep": sweep["candidates"],
        "interpretation": {
            "note": (
                "Proxy analysis: lane-update/load signals are used as cognitive-load approximations. "
                "Use as a prioritization trigger, not a hard causal claim."
            ),
            "next_action": (
                "Apply compact schema-first signaling when load >= threshold and compare pickup/correction "
                "metrics against low-load baseline (F-PSY2/F-PSY3)."
            ),
        },
        "generated_at_utc": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lanes", type=Path, default=Path("tasks/SWARM-LANES.md"))
    parser.add_argument("--next", type=Path, default=Path("tasks/NEXT.md"))
    parser.add_argument("--session-min", type=int, default=150)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/psychology/f-psy1-context-load-threshold-s186.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(
        args.lanes,
        next_path=args.next,
        session_min=args.session_min,
        out_path=args.out,
    )
    summary = result["summary"]
    print(f"Wrote {args.out}")
    print(
        "sessions_joined=",
        summary["sessions_joined"],
        "corr=",
        summary["context_load_quality_correlation"],
        "best_threshold=",
        (summary["best_threshold"] or {}).get("threshold"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
