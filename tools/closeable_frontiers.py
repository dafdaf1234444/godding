#!/usr/bin/env python3
"""Closeable frontier advisory (F-NK6 M4 -- 14.3x resolution rate).

Surfaces frontiers scored CLOSEABLE (>=8/10) by the closure classifier,
enabling M4 resolution-intent activation. M4 produces 14.3x the organic
resolution rate when activated (L-1117). Wiring into orient makes the
four-mechanism governance model (M1-M4) self-activating.

DOMEX-NK-S460: section_closeable_frontiers() called from orient_sections.py.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def section_closeable_frontiers(session_num=0, root=ROOT):
    """Return orient lines showing CLOSEABLE frontiers from cached classifier."""
    lines = []
    try:
        classifier_files = sorted(
            (root / "experiments" / "nk-complexity").glob(
                "f-nk6-closure-classifier-s*.json"
            )
        )
        if not classifier_files:
            return lines

        latest_data = json.loads(classifier_files[-1].read_text())
        scores = latest_data.get("results", {}).get("frontier_scores", {})
        if not scores:
            return lines

        cache_session = 0
        m = re.search(r"s(\d+)", classifier_files[-1].name)
        if m:
            cache_session = int(m.group(1))
        cache_age = (
            (session_num - cache_session) if cache_session and session_num else 999
        )

        frontier_path = root / "tasks" / "FRONTIER.md"
        if not frontier_path.exists():
            return lines
        frontier_text = frontier_path.read_text(encoding="utf-8")

        closeable = []
        approaching = []
        for fid, data in scores.items():
            score = data.get("total", 0)
            if f"~~**{fid}**~~" in frontier_text:
                continue
            if f"**{fid}**" not in frontier_text:
                continue
            if score >= 8:
                closeable.append((fid, score))
            elif score >= 6:
                approaching.append((fid, score))

        if not closeable and not approaching:
            return lines

        stale_note = f" \u2014 cache {cache_age}s old" if cache_age > 10 else ""
        lines.append(
            f"--- Closeable Frontiers (F-NK6 M4 \u2014 14.3x rate{stale_note}) ---"
        )
        for fid, score in sorted(closeable, key=lambda x: -x[1]):
            lines.append(
                f"  \U0001f7e2 {fid} (score={score}/10)"
                f" \u2014 ready for M4 resolution-intent session"
            )
        for fid, score in sorted(approaching, key=lambda x: -x[1]):
            lines.append(
                f"  \U0001f7e1 {fid} (score={score}/10)"
                f" \u2014 approaching; needs more evidence"
            )
        if closeable:
            lines.append(
                "  Activate M4: open DOMEX lane with"
                " --mode resolution targeting above frontiers"
            )
        lines.append("")
    except Exception:
        pass
    return lines


if __name__ == "__main__":
    lines = section_closeable_frontiers(session_num=460)
    for line in lines:
        print(line)
