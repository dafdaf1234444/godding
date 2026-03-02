#!/usr/bin/env python3
"""F-HIS2: detect chronology conflicts across NEXT, SWARM-LANES, and artifacts."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
PATH_RE = re.compile(r"(?:^|[`\s(])((?:experiments|tools)/[A-Za-z0-9_./-]+(?:\.json|\.md|\.py))(?:$|[`\s),])")
SESSION_RE = re.compile(r"\bS(\d+)\b")


@dataclass(frozen=True)
class NextEvent:
    session: int
    text: str
    refs: tuple[str, ...]


def _parse_session(raw: str) -> int | None:
    m = SESSION_RE.search(raw or "")
    return int(m.group(1)) if m else None


def _extract_refs(text: str) -> tuple[str, ...]:
    refs = []
    for m in PATH_RE.finditer(text or ""):
        ref = m.group(1).strip().rstrip(".,;")
        refs.append(ref)
    return tuple(dict.fromkeys(refs))


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
        rows.append(row)
    return rows


def parse_next_events(text: str) -> list[NextEvent]:
    section = _extract_markdown_section(text, "What just happened")
    if section is None:
        return []

    events: list[NextEvent] = []
    for raw in section.splitlines():
        line = raw.strip()
        if not line:
            continue
        session = _parse_session(line)
        if session is None:
            continue
        refs = _extract_refs(line)
        events.append(NextEvent(session=session, text=line, refs=refs))
    return events


def _extract_markdown_section(text: str, heading_pattern: str) -> str | None:
    heading = re.search(rf"^##\s*{heading_pattern}\b.*$", text, re.IGNORECASE | re.MULTILINE)
    if not heading:
        return None
    start = heading.end()
    tail = text[start:]
    next_heading = re.search(r"^##\s+\S", tail, re.MULTILINE)
    return tail[:next_heading.start()] if next_heading else tail


def _index_lane_refs(rows: list[dict[str, str]]) -> dict[str, list[int]]:
    by_ref: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        session = _parse_session(row.get("session", ""))
        if session is None:
            continue
        sources = (row.get("scope_key", ""), row.get("etc", ""), row.get("notes", ""))
        refs: set[str] = set()
        for src in sources:
            refs.update(_extract_refs(src))
        # Scope key often carries tool path even without extension parsing in etc/notes.
        scope_key = row.get("scope_key", "").strip()
        if scope_key.startswith(("tools/", "experiments/")):
            refs.add(scope_key)
        for ref in refs:
            by_ref[ref].append(session)
    for ref in by_ref:
        by_ref[ref] = sorted(by_ref[ref])
    return by_ref


def analyze(next_events: list[NextEvent], lane_rows: list[dict[str, str]], *, repo_root: Path = Path(".")) -> dict[str, Any]:
    lane_ref_sessions = _index_lane_refs(lane_rows)
    missing_link_events: list[dict[str, Any]] = []
    inversion_events: list[dict[str, Any]] = []
    missing_artifacts: set[str] = set()
    matched = 0

    for event in next_events:
        if not event.refs:
            continue
        any_match = False
        for ref in event.refs:
            if ref.startswith("experiments/") and not (repo_root / ref).exists():
                missing_artifacts.add(ref)
            sessions = lane_ref_sessions.get(ref, [])
            if sessions:
                any_match = True
                if min(sessions) > event.session:
                    inversion_events.append(
                        {
                            "session": event.session,
                            "ref": ref,
                            "next_event_text": event.text,
                            "earliest_lane_session": min(sessions),
                        }
                    )
        if any_match:
            matched += 1
        else:
            missing_link_events.append(
                {
                    "session": event.session,
                    "refs": list(event.refs),
                    "next_event_text": event.text,
                }
            )

    # Reverse-link pass: recent lane evidence not represented in NEXT.
    next_ref_set = {ref for event in next_events for ref in event.refs}
    lane_only_refs = []
    for ref, sessions in lane_ref_sessions.items():
        if ref in next_ref_set:
            continue
        if not ref.startswith("experiments/"):
            continue
        lane_only_refs.append({"ref": ref, "first_lane_session": min(sessions), "last_lane_session": max(sessions)})
    lane_only_refs.sort(key=lambda item: (-int(item["last_lane_session"]), item["ref"]))

    total_with_refs = sum(1 for event in next_events if event.refs)
    return {
        "next_events_total": len(next_events),
        "next_events_with_refs": total_with_refs,
        "matched_next_events": matched,
        "missing_link_events": missing_link_events[:30],
        "missing_link_rate": round(len(missing_link_events) / max(1, total_with_refs), 4),
        "inversion_events": inversion_events[:30],
        "inversion_rate": round(len(inversion_events) / max(1, total_with_refs), 4),
        "missing_artifacts": sorted(missing_artifacts),
        "lane_only_artifacts_not_in_next": lane_only_refs[:50],
    }


def run(next_path: Path, lanes_path: Path, out_path: Path) -> dict[str, Any]:
    next_text = next_path.read_text(encoding="utf-8", errors="replace")
    lane_text = lanes_path.read_text(encoding="utf-8", errors="replace")
    next_events = parse_next_events(next_text)
    lane_rows = parse_lane_rows(lane_text)
    analysis = analyze(next_events, lane_rows, repo_root=Path("."))
    payload = {
        "frontier_id": "F-HIS2",
        "title": "Chronology conflict detection across NEXT, SWARM-LANES, and artifacts",
        "inputs": {
            "next": str(next_path).replace("\\", "/"),
            "lanes": str(lanes_path).replace("\\", "/"),
        },
        "analysis": analysis,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _current_session() -> int:
    """Detect current session number from SESSION-LOG.md or git log."""
    import subprocess
    numbers = []
    try:
        log_text = Path("memory/SESSION-LOG.md").read_text(encoding="utf-8", errors="replace")
        numbers = [int(m) for m in re.findall(r"^S(\d+)", log_text, re.MULTILINE)]
    except Exception:
        pass
    try:
        git_out = subprocess.run(
            ["git", "log", "--oneline", "-50"],
            capture_output=True, text=True, timeout=5,
        ).stdout
        numbers.extend(int(m) for m in re.findall(r"\[S(\d+)\]", git_out))
    except Exception:
        pass
    return max(numbers) if numbers else 0


def parse_args() -> argparse.Namespace:
    session = _current_session()
    session_tag = f"s{session}" if session else "latest"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--next", type=Path, default=Path("tasks/NEXT.md"))
    parser.add_argument("--lanes", type=Path, default=Path("tasks/SWARM-LANES.md"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(f"experiments/history/f-his2-chronology-conflicts-{session_tag}.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run(args.next, args.lanes, args.out)
    analysis = payload["analysis"]
    print(f"Wrote {args.out}")
    print(
        "next_events=",
        analysis["next_events_total"],
        "with_refs=",
        analysis["next_events_with_refs"],
        "missing_link_rate=",
        analysis["missing_link_rate"],
        "inversion_rate=",
        analysis["inversion_rate"],
        "missing_artifacts=",
        len(analysis["missing_artifacts"]),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

