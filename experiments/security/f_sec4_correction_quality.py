#!/usr/bin/env python3
"""F-SEC4 audit: does correction-rate optimization Goodhart into shallow fixes?"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSONS_DIR = ROOT / "memory" / "lessons"
sys.path.insert(0, str(ROOT))

from tools import correction_propagation as cp  # noqa: E402


SAMPLE_PAIRS: list[tuple[str, str]] = [
    ("L-025", "L-029"),
    ("L-025", "L-613"),
    ("L-050", "L-058"),
    ("L-1558", "L-1595"),
    ("L-374", "L-371"),
    ("L-375", "L-372"),
    ("L-426", "L-423"),
    ("L-556", "L-555"),
    ("L-567", "L-560"),
    ("L-746", "L-885"),
]


MANUAL_AUDIT: dict[tuple[str, str], dict[str, object]] = {
    ("L-025", "L-029"): {
        "addresses_falsified_claim": True,
        "corrected_text_accurate": True,
        "behavior_change_exists": False,
        "rationale": (
            "L-029 adds a correction note that points from L-025 to L-613/L-618, but it does "
            "not change a tool or workflow."
        ),
    },
    ("L-025", "L-613"): {
        "addresses_falsified_claim": True,
        "corrected_text_accurate": True,
        "behavior_change_exists": True,
        "rationale": (
            "L-613 directly re-measures and falsifies the NK claim, then replaces the operating "
            "classification rule for future architecture analysis."
        ),
    },
    ("L-050", "L-058"): {
        "addresses_falsified_claim": True,
        "corrected_text_accurate": True,
        "behavior_change_exists": False,
        "rationale": (
            "L-058 marks L-050 as archived/superseded and keeps the evidence context accurate, "
            "but it does not encode a process or tooling change."
        ),
    },
    ("L-1558", "L-1595"): {
        "addresses_falsified_claim": True,
        "corrected_text_accurate": True,
        "behavior_change_exists": True,
        "rationale": (
            "L-1595 repairs the epidemic interpretation and records a concrete classifier/process "
            "change in epidemic_spread.py."
        ),
    },
    ("L-374", "L-371"): {
        "addresses_falsified_claim": False,
        "corrected_text_accurate": True,
        "behavior_change_exists": False,
        "rationale": (
            "L-371 is the canonical replacement for duplicate L-374, but the correction is "
            "organizational rather than a repair to harmful false content."
        ),
    },
    ("L-375", "L-372"): {
        "addresses_falsified_claim": False,
        "corrected_text_accurate": True,
        "behavior_change_exists": False,
        "rationale": (
            "L-372 cleanly replaces duplicate L-375, but it does not add behavioral follow-through."
        ),
    },
    ("L-426", "L-423"): {
        "addresses_falsified_claim": True,
        "corrected_text_accurate": True,
        "behavior_change_exists": False,
        "rationale": (
            "L-423 is the accurate artifact-backed replacement for L-426, but it does not modify "
            "tooling or operator procedure."
        ),
    },
    ("L-556", "L-555"): {
        "addresses_falsified_claim": True,
        "corrected_text_accurate": True,
        "behavior_change_exists": True,
        "rationale": (
            "L-555 preserves the stale-baseline diagnosis and records the maintenance.py fix that "
            "changes how the baseline floor is selected."
        ),
    },
    ("L-567", "L-560"): {
        "addresses_falsified_claim": True,
        "corrected_text_accurate": True,
        "behavior_change_exists": False,
        "rationale": (
            "L-560 is an accurate canonical replacement for duplicate L-567, but the repair is "
            "organizational only."
        ),
    },
    ("L-746", "L-885"): {
        "addresses_falsified_claim": True,
        "corrected_text_accurate": True,
        "behavior_change_exists": True,
        "rationale": (
            "L-885 directly falsifies L-746's FP estimate and ties the correction to a concrete "
            "self-declaration guard in correction_propagation.py."
        ),
    },
}


def _load_preloaded_lessons() -> tuple[dict[Path, str], list[dict[str, str]]]:
    preloaded: dict[Path, str] = {}
    skipped: list[dict[str, str]] = []
    for path in sorted(LESSONS_DIR.glob("L-*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
            skipped.append({"lesson": path.stem, "reason": "unicode-replaced"})
        except OSError as exc:
            skipped.append({"lesson": path.stem, "reason": f"oserror: {exc}"})
            continue
        preloaded[path] = text
    return preloaded, skipped


def _build_report(session: str) -> dict[str, object]:
    preloaded, skipped = _load_preloaded_lessons()
    lessons = cp._parse_lessons(preloaded=preloaded)
    falsified_map = cp._detect_falsified_lessons(lessons)
    analysis = cp.run_analysis(session=session, classify=True, preloaded=preloaded)

    corrected_pairs = {
        (falsified_id, corrector_id)
        for falsified_id, corrector_ids in falsified_map.items()
        for corrector_id in corrector_ids
    }
    missing_pairs = [pair for pair in SAMPLE_PAIRS if pair not in corrected_pairs]
    if missing_pairs:
        raise SystemExit(
            f"Sample pairs no longer present in live correction graph: {missing_pairs}"
        )

    audits: list[dict[str, object]] = []
    for falsified_id, corrected_id in SAMPLE_PAIRS:
        judgment = dict(MANUAL_AUDIT[(falsified_id, corrected_id)])
        judgment["substantive"] = (
            judgment["addresses_falsified_claim"]
            and judgment["corrected_text_accurate"]
            and judgment["behavior_change_exists"]
        )
        audits.append(
            {
                "falsified_lesson": falsified_id,
                "falsified_title": lessons[falsified_id]["title"],
                "corrected_lesson": corrected_id,
                "corrected_title": lessons[corrected_id]["title"],
                **judgment,
            }
        )

    substantive_count = sum(1 for audit in audits if audit["substantive"])
    addresses_count = sum(1 for audit in audits if audit["addresses_falsified_claim"])
    accurate_count = sum(1 for audit in audits if audit["corrected_text_accurate"])
    behavior_change_count = sum(1 for audit in audits if audit["behavior_change_exists"])

    if substantive_count <= 5:
        verdict = "CONFIRMED"
    elif substantive_count >= 8:
        verdict = "FALSIFIED"
    else:
        verdict = "MIXED"

    return {
        "session": session,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "frontier": "F-SEC4",
        "question": "Does optimizing correction rate cascade Goodhart effects to correction quality?",
        "prediction": "<=5/10 corrections are substantive",
        "falsification_threshold": ">=8/10 corrections are substantive",
        "selection_method": (
            "Deterministic stratified sample across all currently corrected falsified lessons, "
            "plus one extra L-025 pair because it has the largest correction fan-out."
        ),
        "cohort_summary": {
            "corrected_pair_count": len(corrected_pairs),
            "corrected_pairs_by_falsified_lesson": {
                falsified_id: len(corrector_ids)
                for falsified_id, corrector_ids in sorted(falsified_map.items())
            },
            "falsified_ids": analysis["falsified_ids"],
            "total_falsified_detected": analysis["total_falsified_detected"],
            "total_falsified_with_gaps": analysis["total_falsified_with_gaps"],
            "total_uncorrected_citations": analysis["total_uncorrected_citations"],
            "avg_correction_rate": analysis["avg_correction_rate"],
        },
        "audit_summary": {
            "sample_size": len(audits),
            "addresses_falsified_claim_count": addresses_count,
            "corrected_text_accurate_count": accurate_count,
            "behavior_change_count": behavior_change_count,
            "substantive_count": substantive_count,
            "verdict": verdict,
            "conclusion": (
                "The correction pipeline repairs truth at the text layer more reliably than it "
                "drives tool/process change, so correction-rate output over-credits shallow fixes."
            ),
        },
        "sample_pairs": [
            {"falsified_lesson": falsified_id, "corrected_lesson": corrected_id}
            for falsified_id, corrected_id in SAMPLE_PAIRS
        ],
        "audits": audits,
        "loader_notes": {
            "preloaded_lessons": len(preloaded),
            "skipped_or_recovered": skipped,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", default="S544")
    parser.add_argument(
        "--artifact",
        default=str(ROOT / "experiments" / "security" / "f-sec4-correction-quality-s544.json"),
    )
    args = parser.parse_args()

    report = _build_report(args.session)
    artifact_path = Path(args.artifact)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    summary = report["audit_summary"]
    print(
        f"Saved {artifact_path} | verdict={summary['verdict']} | "
        f"substantive={summary['substantive_count']}/{summary['sample_size']} | "
        f"behavior_change={summary['behavior_change_count']}/{summary['sample_size']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
