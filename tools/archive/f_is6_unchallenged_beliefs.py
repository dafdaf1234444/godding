#!/usr/bin/env python3
"""F-IS6: audit long-standing unchallenged principles for swarm-improvement challenge lanes."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

PRINCIPLE_RE = re.compile(r"P-\d{3}")
SESSION_RE = re.compile(r"\bS(\d+)\b")

EVIDENCE_PRIORITY = {
    "THEORIZED": 3.0,
    "PARTIALLY OBSERVED": 2.0,
    "UNSPECIFIED": 2.0,
    "OBSERVED": 1.0,
}

THEME_PRIORITY = {
    "Governance": 3.0,
    "Evolution (spawn, colony)": 3.0,
    "Protocols": 2.0,
    "Strategy": 2.0,
    "Architecture": 1.0,
    "Complexity (NK analysis)": 1.0,
    "Distributed Systems": 1.0,
}

FOCUS_THEMES = {
    "Governance",
    "Evolution (spawn, colony)",
    "Protocols",
    "Strategy",
}


@dataclass(frozen=True)
class PrincipleRecord:
    pid: str
    theme: str
    claim: str
    evidence: str


def parse_current_session(next_text: str) -> int:
    m = re.search(r"Updated:\s+\d{4}-\d{2}-\d{2}\s+S(\d+)", next_text)
    return int(m.group(1)) if m else 0


def detect_evidence_tag(line: str) -> str:
    if "THEORIZED" in line:
        return "THEORIZED"
    if "PARTIALLY OBSERVED" in line:
        return "PARTIALLY OBSERVED"
    if "OBSERVED" in line:
        return "OBSERVED"
    return "UNSPECIFIED"


def extract_claim_for_id(line: str, pid: str) -> str:
    m = re.search(rf"{re.escape(pid)}\s*([^|]+)", line)
    if not m:
        return ""
    text = m.group(1).strip()
    text = re.sub(r"\([^)]*\)\s*$", "", text).strip()
    return text


def parse_principles(principles_text: str) -> dict[str, PrincipleRecord]:
    records: dict[str, PrincipleRecord] = {}
    theme = "Unknown"
    for raw in principles_text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            theme = line[3:].strip()
            continue
        if line.startswith("Removed:"):
            break
        if theme == "Unknown":
            continue
        for part in [p.strip() for p in line.split("|")]:
            if not part:
                continue
            if part.lower().startswith(("last compacted:", "removed:")):
                continue
            m = PRINCIPLE_RE.search(part)
            if not m:
                continue
            pid = m.group(0)
            if pid in records:
                continue
            evidence = detect_evidence_tag(part)
            claim = extract_claim_for_id(part, pid)
            records[pid] = PrincipleRecord(pid=pid, theme=theme, claim=claim, evidence=evidence)
    return records


def parse_challenged_ids(challenges_text: str) -> set[str]:
    # Target column in beliefs/CHALLENGES.md table.
    hits = re.findall(r"\|\s*S\d+[^\n|]*\|\s*(P-\d{3})\s*\|", challenges_text)
    return set(hits)


def git_first_seen_session(
    pid: str,
    *,
    repo_root: Path,
    file_path: Path,
) -> int | None:
    cmd = [
        "git",
        "log",
        "--reverse",
        "--format=%s",
        "-S",
        pid,
        "--",
        str(file_path).replace("\\", "/"),
    ]
    try:
        out = subprocess.check_output(cmd, cwd=repo_root, text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    for line in out.splitlines():
        m = SESSION_RE.search(line)
        if m:
            return int(m.group(1))
    return None


def challenge_lens(theme: str) -> str:
    if theme in {"Governance", "Protocols"}:
        return "coordination"
    if theme in {"Evolution (spawn, colony)", "Strategy"}:
        return "objective"
    return "assumption"


def challenge_prompt(record: PrincipleRecord) -> str:
    if record.evidence == "THEORIZED":
        return "Run a direct falsification experiment and promote/demote evidence status."
    if record.evidence == "PARTIALLY OBSERVED":
        return "Run a replication in a new lane/substrate and test boundary conditions."
    if record.evidence == "UNSPECIFIED":
        return "Add an explicit evidence type and run one check that could overturn the claim."
    return "Stress-test with a counterexample run on a different workload."


def priority_score(
    record: PrincipleRecord,
    *,
    challenged: bool,
    age_value: int,
    longstanding_cutoff: int,
) -> float:
    if challenged:
        return 0.0
    evidence_weight = EVIDENCE_PRIORITY.get(record.evidence, 2.0)
    theme_weight = THEME_PRIORITY.get(record.theme, 1.0)
    age_sessions = max(0, age_value)
    age_weight = min(age_sessions / 20.0, 6.0)
    longstanding_bonus = 2.0 if age_sessions >= longstanding_cutoff else 0.0
    return round((3.0 * evidence_weight) + (2.0 * theme_weight) + age_weight + longstanding_bonus, 4)


def analyze(
    principles_text: str,
    challenges_text: str,
    next_text: str,
    *,
    repo_root: Path,
    longstanding_cutoff: int = 40,
    top_n: int = 10,
    session_resolver: Callable[[str], int | None] | None = None,
) -> dict[str, Any]:
    records = parse_principles(principles_text)
    challenged_ids = parse_challenged_ids(challenges_text)
    current_session = parse_current_session(next_text)
    max_pid_num = max(int(pid.split("-")[1]) for pid in records) if records else 0

    by_theme: dict[str, int] = defaultdict(int)
    by_evidence: Counter[str] = Counter()
    challenged_by_evidence: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []

    for pid in sorted(records):
        rec = records[pid]
        challenged = pid in challenged_ids
        pid_num = int(pid.split("-")[1])
        first_seen = session_resolver(pid) if session_resolver else None
        if first_seen and current_session:
            age = max(0, current_session - first_seen)
            age_basis = "session_gap"
        else:
            age = max(0, max_pid_num - pid_num)
            age_basis = "id_gap"
        score = priority_score(
            rec,
            challenged=challenged,
            age_value=age,
            longstanding_cutoff=longstanding_cutoff,
        )
        by_theme[rec.theme] += 1
        by_evidence[rec.evidence] += 1
        if challenged:
            challenged_by_evidence[rec.evidence] += 1
        rows.append(
            {
                "id": pid,
                "theme": rec.theme,
                "claim": rec.claim,
                "evidence": rec.evidence,
                "challenged": challenged,
                "first_seen_session": first_seen,
                "age_sessions": age,
                "age_basis": age_basis,
                "lens": challenge_lens(rec.theme),
                "priority_score": score,
                "challenge_prompt": challenge_prompt(rec),
            }
        )

    unchallenged = [r for r in rows if not r["challenged"]]
    longstanding = [r for r in unchallenged if r["age_sessions"] >= longstanding_cutoff]
    high_leverage = [
        r
        for r in unchallenged
        if r["theme"] in FOCUS_THEMES
        and (r["evidence"] != "OBSERVED" or r["age_sessions"] >= longstanding_cutoff)
    ]
    high_leverage.sort(
        key=lambda r: (
            -r["priority_score"],
            -r["age_sessions"],
            r["id"],
        )
    )

    by_theme_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in high_leverage:
        by_theme_rows[row["theme"]].append(row)

    diverse: list[dict[str, Any]] = []
    theme_order = sorted(by_theme_rows.keys())
    depth = 0
    while len(diverse) < top_n:
        added = False
        for theme in theme_order:
            rows_for_theme = by_theme_rows.get(theme, [])
            if depth < len(rows_for_theme):
                diverse.append(rows_for_theme[depth])
                added = True
                if len(diverse) >= top_n:
                    break
        if not added:
            break
        depth += 1

    return {
        "current_session": current_session,
        "longstanding_cutoff_sessions": longstanding_cutoff,
        "age_mode_default": "id_gap",
        "total_principles": len(rows),
        "challenged_principles": len(rows) - len(unchallenged),
        "unchallenged_principles": len(unchallenged),
        "unchallenged_ratio": round(len(unchallenged) / max(1, len(rows)), 4),
        "longstanding_unchallenged_count": len(longstanding),
        "theme_distribution": dict(sorted(by_theme.items(), key=lambda kv: kv[0])),
        "evidence_distribution": dict(by_evidence),
        "challenged_evidence_distribution": dict(challenged_by_evidence),
        "high_leverage_candidates": high_leverage[:top_n],
        "diverse_challenge_set": diverse[:top_n],
        "audit_rows": rows,
    }


def run(
    *,
    principles_path: Path,
    challenges_path: Path,
    next_path: Path,
    out_path: Path,
    longstanding_cutoff: int = 40,
    top_n: int = 10,
) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    payload = {
        "frontier_id": "F-IS6",
        "title": "Long-standing unchallenged principle audit",
        "inputs": {
            "principles": str(principles_path).replace("\\", "/"),
            "challenges": str(challenges_path).replace("\\", "/"),
            "next": str(next_path).replace("\\", "/"),
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "analysis": analyze(
            principles_path.read_text(encoding="utf-8", errors="replace"),
            challenges_path.read_text(encoding="utf-8", errors="replace"),
            next_path.read_text(encoding="utf-8", errors="replace"),
            repo_root=repo_root,
            longstanding_cutoff=longstanding_cutoff,
            top_n=top_n,
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--principles", type=Path, default=Path("memory/PRINCIPLES.md"))
    parser.add_argument("--challenges", type=Path, default=Path("beliefs/CHALLENGES.md"))
    parser.add_argument("--next", dest="next_path", type=Path, default=Path("tasks/NEXT.md"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/information-science/f-is6-unchallenged-beliefs-s186.json"),
    )
    parser.add_argument("--longstanding-cutoff", type=int, default=40)
    parser.add_argument("--top-n", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run(
        principles_path=args.principles,
        challenges_path=args.challenges,
        next_path=args.next_path,
        out_path=args.out,
        longstanding_cutoff=args.longstanding_cutoff,
        top_n=args.top_n,
    )
    analysis = payload["analysis"]
    print(f"Wrote {args.out}")
    print(
        "total=",
        analysis["total_principles"],
        "challenged=",
        analysis["challenged_principles"],
        "unchallenged=",
        analysis["unchallenged_principles"],
        "longstanding_unchallenged=",
        analysis["longstanding_unchallenged_count"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
