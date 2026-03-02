#!/usr/bin/env python3
"""F-EVO2 contamination profile: cross-domain contamination pressure in swarm state."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ACTIVE_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}
RUNNING_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED"}


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def _lane_rows(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rows: list[dict[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|\s*(Date\s*\||[-: ]+\|)", line, re.IGNORECASE):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 12:
            continue
        rows.append(
            {
                "lane": parts[1],
                "session": parts[2],
                "status": parts[10].upper(),
                "scope_key": parts[8],
                "etc": parts[9],
                "notes": parts[11],
            }
        )
    return rows


def _latest_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    for row in rows:
        lane = row.get("lane", "").strip()
        if not lane:
            continue
        latest[lane] = row
    return list(latest.values())


def _lane_pressure_component(rows: list[dict[str, str]]) -> dict[str, Any]:
    latest = [row for row in _latest_rows(rows) if row.get("status") in ACTIVE_STATUSES]
    ready = sum(1 for row in latest if row.get("status") == "READY")
    running = sum(1 for row in latest if row.get("status") in RUNNING_STATUSES)
    active_total = len(latest)
    queue_ratio = ready / max(1, running)
    # Ratio >=5 indicates queue-heavy coordinator-only motion.
    component = _clamp(queue_ratio / 5.0)
    return {
        "active_lane_count": active_total,
        "ready_count": ready,
        "running_count": running,
        "ready_to_running_ratio": round(queue_ratio, 4),
        "component": round(component, 4),
    }


def _gam2_component(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    summary = ((payload.get("analysis") or {}).get("integrity_summary") or {})
    signal_rate = _as_float(summary.get("reputation_signal_rate_active"), 0.0)
    integrity = _as_float(summary.get("integrity_score"), 0.0)
    gap = _clamp(1.0 - signal_rate)
    return {
        "reputation_signal_rate_active": round(signal_rate, 4),
        "integrity_score": round(integrity, 4),
        "component": round(gap, 4),
        "frontier_id": payload.get("frontier_id", "F-GAM2"),
    }


def _is5_component(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    metrics = payload.get("summary_metrics") or {}
    collision = _as_float(metrics.get("merge_collision_frequency"), 0.0)
    acceptance = _as_float(metrics.get("transfer_acceptance_rate"), 0.0)
    # High collision with low accepted transfer is contamination pressure.
    component = _clamp(collision - acceptance)
    return {
        "merge_collision_frequency": round(collision, 4),
        "transfer_acceptance_rate": round(acceptance, 4),
        "component": round(component, 4),
        "frontier_id": payload.get("experiment", "F-IS5"),
    }


def _stat2_component(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    overall = payload.get("overall") or {}
    i2_percent = _as_float(overall.get("I2_percent"), 0.0)
    pooled_effect = _as_float(overall.get("pooled_effect"), 0.0)
    component = _clamp(i2_percent / 100.0)
    return {
        "i2_percent": round(i2_percent, 4),
        "pooled_effect": round(pooled_effect, 6),
        "component": round(component, 4),
        "frontier_id": payload.get("frontier_id", "F-STAT2"),
    }


def _ops1_component(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    recommended = payload.get("recommended") or {}
    ab = payload.get("ab_comparison") or {}
    conflict_rate = _as_float(recommended.get("conflict_rate"), 0.0)
    overhead = _as_float(recommended.get("overhead_ratio"), 0.0)
    decision_hint = str(ab.get("decision_hint", "")).strip().lower()
    hint_penalty = 0.05 if "inconclusive" in decision_hint else 0.0
    component = _clamp(conflict_rate + hint_penalty)
    return {
        "conflict_rate": round(conflict_rate, 4),
        "overhead_ratio": round(overhead, 4),
        "decision_hint": decision_hint,
        "component": round(component, 4),
        "frontier_id": payload.get("frontier_id", "F-OPS1"),
    }


def _his2_component(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    analysis = payload.get("analysis") or {}
    missing_link = _as_float(analysis.get("missing_link_rate"), 0.0)
    inversion = _as_float(analysis.get("inversion_rate"), 0.0)
    component = _clamp(missing_link + inversion)
    return {
        "missing_link_rate": round(missing_link, 4),
        "inversion_rate": round(inversion, 4),
        "component": round(component, 4),
        "frontier_id": payload.get("frontier_id", "F-HIS2"),
    }


def _classify(index_value: float) -> str:
    if index_value >= 0.60:
        return "HIGH"
    if index_value >= 0.35:
        return "MEDIUM"
    return "LOW"


def _recommendations(components: dict[str, dict[str, Any]]) -> list[str]:
    recs: list[str] = []

    lane = components.get("lane_queue_pressure", {})
    if _as_float(lane.get("component"), 0.0) >= 0.6:
        recs.append(
            "Convert queued READY lanes into ACTIVE execution or explicit BLOCKED with unblocking asks before adding new slots."
        )

    is5 = components.get("is5_transfer_collision", {})
    if _as_float(is5.get("component"), 0.0) >= 0.5:
        recs.append(
            "Run F-IS5 overlap-intensity sweep and keep only settings with collision<0.5 while preserving non-zero transfer acceptance."
        )

    stat2 = components.get("stat2_heterogeneity", {})
    if _as_float(stat2.get("component"), 0.0) >= 0.4:
        recs.append(
            "Split high-heterogeneity families and rerun F-STAT2/F-STAT3 before promoting cross-domain transfer claims."
        )

    gam2 = components.get("gam2_reputation_gap", {})
    if _as_float(gam2.get("component"), 0.0) >= 0.5:
        recs.append(
            "Raise active-lane reputation tag coverage to >=0.6, then rerun F-GAM2 to reduce cohort-selection contamination."
        )

    ops1 = components.get("ops1_conflict_pressure", {})
    if _as_float(ops1.get("component"), 0.0) >= 0.35:
        recs.append(
            "Keep cap-4 default under F-OPS1 until live A/B demonstrates cap-5 gains without conflict/overhead regression."
        )

    his2 = components.get("his2_chronology_gap", {})
    if _as_float(his2.get("component"), 0.0) >= 0.08:
        recs.append(
            "Backfill lane-level artifact refs for unmatched NEXT events to lower chronology contamination below 0.05."
        )

    if not recs:
        recs.append("No high-pressure contamination drivers detected; continue monitoring on next rerun.")
    return recs


def build_report(
    *,
    lanes_path: Path,
    gam2_path: Path,
    is5_path: Path,
    stat2_path: Path,
    ops1_path: Path,
    his2_path: Path,
) -> dict[str, Any]:
    rows = _lane_rows(lanes_path)

    components: dict[str, dict[str, Any]] = {
        "lane_queue_pressure": _lane_pressure_component(rows),
        "gam2_reputation_gap": _gam2_component(gam2_path),
        "is5_transfer_collision": _is5_component(is5_path),
        "stat2_heterogeneity": _stat2_component(stat2_path),
        "ops1_conflict_pressure": _ops1_component(ops1_path),
        "his2_chronology_gap": _his2_component(his2_path),
    }

    weights = {
        "lane_queue_pressure": 0.20,
        "gam2_reputation_gap": 0.15,
        "is5_transfer_collision": 0.20,
        "stat2_heterogeneity": 0.20,
        "ops1_conflict_pressure": 0.15,
        "his2_chronology_gap": 0.10,
    }

    weighted_terms = {
        key: round(_as_float(components[key].get("component")) * weight, 4) for key, weight in weights.items()
    }
    contamination_index = round(sum(weighted_terms.values()), 4)

    return {
        "experiment": "F-EVO2",
        "title": "Cross-domain contamination pressure profile",
        "inputs": {
            "lanes": str(lanes_path).replace("\\", "/"),
            "gam2": str(gam2_path).replace("\\", "/"),
            "is5": str(is5_path).replace("\\", "/"),
            "stat2": str(stat2_path).replace("\\", "/"),
            "ops1": str(ops1_path).replace("\\", "/"),
            "his2": str(his2_path).replace("\\", "/"),
        },
        "components": components,
        "weights": weights,
        "weighted_terms": weighted_terms,
        "contamination_index": contamination_index,
        "contamination_band": _classify(contamination_index),
        "decontamination_recommendations": _recommendations(components),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lanes", type=Path, default=Path("tasks/SWARM-LANES.md"))
    parser.add_argument(
        "--gam2",
        type=Path,
        default=Path("experiments/game-theory/f-gam2-reputation-signals-s186-rerun2.json"),
    )
    parser.add_argument(
        "--is5",
        type=Path,
        default=Path("experiments/information-science/f-is5-lane-distill-tags-s186-overlap.json"),
    )
    parser.add_argument(
        "--stat2",
        type=Path,
        default=Path("experiments/statistics/f-stat2-meta-analysis-s186-rerun.json"),
    )
    parser.add_argument(
        "--ops1",
        type=Path,
        default=Path("experiments/operations-research/f-ops1-wip-limit-s186-msw2-s3-rerun3.json"),
    )
    parser.add_argument(
        "--his2",
        type=Path,
        default=Path("experiments/history/f-his2-chronology-conflicts-s186-rerun.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/evolution/f-evo2-contamination-s186.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        lanes_path=args.lanes,
        gam2_path=args.gam2,
        is5_path=args.is5,
        stat2_path=args.stat2,
        ops1_path=args.ops1,
        his2_path=args.his2,
    )
    report["generated_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    print(
        "contamination_index=",
        report["contamination_index"],
        "band=",
        report["contamination_band"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

